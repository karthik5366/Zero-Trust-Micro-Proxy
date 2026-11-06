package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"sync"
	"sync/atomic"
)

// AuditEntry defines the complete 13-field NIST SP 800-53 / SOC 2 forensic log schema.
type AuditEntry struct {
	Index         uint64 `json:"index"`
	Timestamp     string `json:"timestamp"`
	ClientIP      string `json:"client_ip"`
	Identity      string `json:"identity"`
	TargetBackend string `json:"target_backend"`
	Method        string `json:"method"`
	Path          string `json:"path"`
	StatusCode    int    `json:"status_code"`
	Decision      string `json:"decision"` // ALLOW, DENY, SHADOW_DENY, RATE_LIMITED, TLS_REJECT, ERROR
	Reason        string `json:"reason"`
	DurationUS    int64  `json:"duration_us"`
	PrevHash      string `json:"prev_hash"`
	EntryHash     string `json:"entry_hash"`
}

const (
	GenesisHash = "0000000000000000000000000000000000000000000000000000000000000000"
	cReset      = "\033[0m"
	cRed        = "\033[31m"
	cGreen      = "\033[32m"
	cYellow     = "\033[33m"
	cCyan       = "\033[36m"
)

// computeEntryHash calculates the cryptographic SHA-256 hash linking the previous entry.
func computeEntryHash(e AuditEntry) string {
	payload := fmt.Sprintf("%d|%s|%s|%s|%s|%s|%s|%d|%s|%s|%d|%s",
		e.Index, e.Timestamp, e.ClientIP, e.Identity, e.TargetBackend,
		e.Method, e.Path, e.StatusCode, e.Decision, e.Reason, e.DurationUS, e.PrevHash)
	h := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(h[:])
}

// AuditLogger manages the asynchronous, non-blocking disk flush and hash chain.
type AuditLogger struct {
	entryChan chan AuditEntry
	file      *os.File
	writer    *bufio.Writer

	lastIndex uint64
	prevHash  string
	mu        sync.Mutex

	subscribers []chan AuditEntry
	subMu       sync.RWMutex

	dropped atomic.Uint64
	done    chan struct{}
	closed  atomic.Bool

	// Live metrics counters for Control Plane & Telemetry Dashboard
	totalReqs      atomic.Uint64
	allowReqs      atomic.Uint64
	denyReqs       atomic.Uint64
	shadowDenyReqs atomic.Uint64
	tlsRejectReqs  atomic.Uint64
	rateLimitReqs  atomic.Uint64
	errorReqs      atomic.Uint64
}

var globalAuditLogger *AuditLogger

// NewAuditLogger initializes the audit logger and resumes the hash chain from disk if it exists.
func NewAuditLogger(path string) (*AuditLogger, error) {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR|os.O_APPEND, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to open audit log %s: %w", path, err)
	}

	lastIndex := uint64(0)
	prevHash := GenesisHash

	// Startup Tail Recovery: Inspect existing file to resume hash chain across restarts
	fi, err := file.Stat()
	if err == nil && fi.Size() > 0 {
		scanner := bufio.NewScanner(file)
		var lastLine string
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line != "" {
				lastLine = line
			}
		}
		if lastLine != "" {
			var lastEntry AuditEntry
			if err := json.Unmarshal([]byte(lastLine), &lastEntry); err == nil {
				lastIndex = lastEntry.Index
				prevHash = lastEntry.EntryHash
				fmt.Printf("[audit] Resumed tamper-evident hash chain from index #%d (%s...)\n", lastIndex, prevHash[:12])
			}
		}
	}

	al := &AuditLogger{
		entryChan: make(chan AuditEntry, 10000),
		file:      file,
		writer:    bufio.NewWriter(file),
		lastIndex: lastIndex,
		prevHash:  prevHash,
		done:      make(chan struct{}),
	}

	go al.workerLoop()
	return al, nil
}

// workerLoop drains entries with instant flush for single requests and batching under load.
func (al *AuditLogger) workerLoop() {
	defer close(al.done)

	for entry := range al.entryChan {
		al.processOne(entry)

		// Non-blocking inner loop: Drain any queued items into the current batch
		for len(al.entryChan) > 0 {
			extra := <-al.entryChan
			al.processOne(extra)
		}

		// Flush immediately to disk so tail -f and demo queries see events with zero lag
		al.mu.Lock()
		al.writer.Flush()
		al.mu.Unlock()
	}

	// Final flush on channel close
	al.mu.Lock()
	al.writer.Flush()
	al.mu.Unlock()
}

// processOne commits a single entry to the cryptographic hash chain.
func (al *AuditLogger) processOne(e AuditEntry) {
	al.mu.Lock()
	defer al.mu.Unlock()

	al.lastIndex++
	e.Index = al.lastIndex
	e.PrevHash = al.prevHash
	e.EntryHash = computeEntryHash(e)
	al.prevHash = e.EntryHash

	// Update live metric counters
	al.totalReqs.Add(1)
	switch e.Decision {
	case "ALLOW":
		al.allowReqs.Add(1)
	case "DENY":
		al.denyReqs.Add(1)
	case "SHADOW_DENY":
		al.shadowDenyReqs.Add(1)
	case "TLS_REJECT":
		al.tlsRejectReqs.Add(1)
	case "RATE_LIMITED":
		al.rateLimitReqs.Add(1)
	case "ERROR":
		al.errorReqs.Add(1)
	}

	bytes, _ := json.Marshal(e)
	al.writer.Write(bytes)
	al.writer.WriteString("\n")

	// Formatted terminal telemetry
	color := cGreen
	switch e.Decision {
	case "DENY", "TLS_REJECT", "ERROR":
		color = cRed
	case "SHADOW_DENY", "RATE_LIMITED":
		color = cYellow
	}

	fmt.Printf("%s[%-11s]%s #%-4d %-6s %-25s -> %-20s (%dμs: %s)\n",
		color, e.Decision, cReset, e.Index, e.Method, e.Path, e.TargetBackend, e.DurationUS, e.Reason)

	// Broadcast to live SSE subscribers (for Dashboard)
	al.subMu.RLock()
	for _, sub := range al.subscribers {
		select {
		case sub <- e:
		default:
			// Non-blocking: Slow UI consumer will not stall audit logger
		}
	}
	al.subMu.RUnlock()
}

// Log enqueues an audit entry asynchronously via non-blocking send.
func (al *AuditLogger) Log(e AuditEntry) {
	if al == nil || al.closed.Load() {
		return
	}
	select {
	case al.entryChan <- e:
	default:
		al.dropped.Add(1)
	}
}

// Subscribe returns an SSE-ready channel receiving live audit entries.
func (al *AuditLogger) Subscribe() (chan AuditEntry, func()) {
	if al == nil {
		ch := make(chan AuditEntry)
		return ch, func() { close(ch) }
	}
	ch := make(chan AuditEntry, 100)
	al.subMu.Lock()
	al.subscribers = append(al.subscribers, ch)
	al.subMu.Unlock()

	unsubscribe := func() {
		al.subMu.Lock()
		defer al.subMu.Unlock()
		for i, sub := range al.subscribers {
			if sub == ch {
				al.subscribers = append(al.subscribers[:i], al.subscribers[i+1:]...)
				close(ch)
				break
			}
		}
	}
	return ch, unsubscribe
}

// Close gracefully flushes all buffered entries and closes the log file.
func (al *AuditLogger) Close() error {
	if al == nil {
		return nil
	}
	if al.closed.Swap(true) {
		return nil
	}
	close(al.entryChan)
	<-al.done // Wait for worker loop to finish writing and flushing

	al.subMu.Lock()
	for _, ch := range al.subscribers {
		close(ch)
	}
	al.subscribers = nil
	al.subMu.Unlock()

	return al.file.Close()
}

// GetMetrics returns snapshot of live request counters.
func (al *AuditLogger) GetMetrics() map[string]uint64 {
	if al == nil {
		return map[string]uint64{
			"total":        0,
			"allow":        0,
			"deny":         0,
			"shadow_deny":  0,
			"tls_reject":   0,
			"rate_limited": 0,
			"error":        0,
		}
	}
	return map[string]uint64{
		"total":        al.totalReqs.Load(),
		"allow":        al.allowReqs.Load(),
		"deny":         al.denyReqs.Load(),
		"shadow_deny":  al.shadowDenyReqs.Load(),
		"tls_reject":   al.tlsRejectReqs.Load(),
		"rate_limited": al.rateLimitReqs.Load(),
		"error":        al.errorReqs.Load(),
	}
}

// GetRecentEntries reads up to limit most recent parsed entries from the log file.
func (al *AuditLogger) GetRecentEntries(limit int) ([]AuditEntry, error) {
	if al == nil {
		return nil, nil
	}
	if limit <= 0 {
		limit = 100
	}
	al.mu.Lock()
	al.writer.Flush()
	al.mu.Unlock()

	file, err := os.Open(al.file.Name())
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var lines []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		text := strings.TrimSpace(scanner.Text())
		if text != "" {
			lines = append(lines, text)
		}
	}

	start := 0
	if len(lines) > limit {
		start = len(lines) - limit
	}

	result := make([]AuditEntry, 0, len(lines)-start)
	for i := start; i < len(lines); i++ {
		var e AuditEntry
		if err := json.Unmarshal([]byte(lines[i]), &e); err == nil {
			result = append(result, e)
		}
	}
	return result, nil
}

// VerifyAuditFile verifies the unbroken SHA-256 cryptographic chain of an audit file.
func VerifyAuditFile(path string) (int, error) {
	file, err := os.Open(path)
	if err != nil {
		return 0, fmt.Errorf("cannot open audit log: %w", err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	expectedPrevHash := GenesisHash
	expectedIndex := uint64(1)
	count := 0

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		count++

		var entry AuditEntry
		if err := json.Unmarshal([]byte(line), &entry); err != nil {
			return count, fmt.Errorf("line %d: malformed JSON: %w", count, err)
		}

		if entry.Index != expectedIndex {
			return count, fmt.Errorf("line %d: index broken! expected %d, got %d", count, expectedIndex, entry.Index)
		}

		if entry.PrevHash != expectedPrevHash {
			return count, fmt.Errorf("line %d: prev_hash mismatch! expected %s, got %s", count, expectedPrevHash, entry.PrevHash)
		}

		computedHash := computeEntryHash(entry)
		if entry.EntryHash != computedHash {
			return count, fmt.Errorf("line %d: entry_hash invalid! record was tampered with (expected %s, got %s)", count, computedHash, entry.EntryHash)
		}

		expectedIndex++
		expectedPrevHash = entry.EntryHash
	}

	if err := scanner.Err(); err != nil {
		return count, fmt.Errorf("error reading audit file: %w", err)
	}

	return count, nil
}

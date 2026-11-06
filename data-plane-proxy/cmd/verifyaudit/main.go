// cmd/verifyaudit/main.go — ZetaShield Cryptographic Audit Ledger Verifier
//
// Verifies the unbroken SHA-256 hash chain of audit.log.jsonl
package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
)

type AuditRecord struct {
	Index         uint64 `json:"index"`
	Timestamp     string `json:"timestamp"`
	ClientIP      string `json:"client_ip"`
	Identity      string `json:"identity"`
	TargetBackend string `json:"target_backend"`
	Method        string `json:"method"`
	Path          string `json:"path"`
	StatusCode    int    `json:"status_code"`
	Decision      string `json:"decision"`
	Reason        string `json:"reason"`
	DurationUS    int64  `json:"duration_us"`
	PrevHash      string `json:"prev_hash"`
	EntryHash     string `json:"entry_hash"`
}

const GenesisHash = "0000000000000000000000000000000000000000000000000000000000000000"

func computeHash(e AuditRecord) string {
	payload := fmt.Sprintf("%d|%s|%s|%s|%s|%s|%s|%d|%s|%s|%d|%s",
		e.Index, e.Timestamp, e.ClientIP, e.Identity, e.TargetBackend,
		e.Method, e.Path, e.StatusCode, e.Decision, e.Reason, e.DurationUS, e.PrevHash)
	h := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(h[:])
}

func main() {
	filePath := flag.String("file", "audit.log.jsonl", "Path to audit.log.jsonl file")
	flag.Parse()

	// Check environment variable fallback
	if *filePath == "audit.log.jsonl" {
		if envPath := os.Getenv("ZS_AUDIT_PATH"); envPath != "" {
			*filePath = envPath
		}
	}

	fmt.Printf("ZetaShield Cryptographic Ledger Verifier\n")
	fmt.Printf("Auditing file: %s\n\n", *filePath)

	file, err := os.Open(*filePath)
	if err != nil {
		fmt.Printf("[ERROR] Cannot open audit file: %v\n", err)
		os.Exit(1)
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

		var record AuditRecord
		if err := json.Unmarshal([]byte(line), &record); err != nil {
			fmt.Printf("[TAMPER ALERT] Line %d contains malformed JSON: %v\n", count, err)
			os.Exit(1)
		}

		if record.Index != expectedIndex {
			fmt.Printf("[TAMPER ALERT] Line %d: Index broken! Expected #%d, got #%d\n", count, expectedIndex, record.Index)
			os.Exit(1)
		}

		if record.PrevHash != expectedPrevHash {
			fmt.Printf("[TAMPER ALERT] Line %d: Previous hash broken!\n  Expected: %s\n  Got:      %s\n", count, expectedPrevHash, record.PrevHash)
			os.Exit(1)
		}

		computed := computeHash(record)
		if record.EntryHash != computed {
			fmt.Printf("[TAMPER ALERT] Line %d: Entry hash mutated! Record was tampered with.\n  Expected: %s\n  Computed: %s\n", count, record.EntryHash, computed)
			os.Exit(1)
		}

		expectedIndex++
		expectedPrevHash = record.EntryHash
	}

	if err := scanner.Err(); err != nil {
		fmt.Printf("[ERROR] File scan error: %v\n", err)
		os.Exit(1)
	}

	if count == 0 {
		fmt.Println("[WARNING] Audit log is empty (0 records verified).")
		return
	}

	fmt.Printf("✅ [OK] Verified %d tamper-evident audit records.\n", count)
	fmt.Printf("   Latest block index: #%d\n", count)
	fmt.Printf("   Latest block hash:  %s\n", expectedPrevHash)
	fmt.Println("   Cryptographic SHA-256 hash chain is 100% intact.")
}

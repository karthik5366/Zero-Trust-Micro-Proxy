package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// ---------- Existing 19 Tests (Preserved 100% for Regression Prevention) ----------

func TestCheckPolicy(t *testing.T) {
	// Reset activeSnapshot to nil to ensure fallback to legacy policy variable works
	activeSnapshot.Store(nil)

	policy = PolicyConfig{
		Rules: []PolicyRule{
			{Identity: "spiffe://zetashield.local/ns/default/sa/frontend-service", PathPrefix: "/orders/", Methods: []string{"GET"}},
			{Identity: "spiffe://zetashield.local/ns/default/sa/frontend-service", PathPrefix: "/payments/", Methods: []string{"GET", "POST"}},
			{Identity: "spiffe://zetashield.local/ns/default/sa/frontend-service", PathPrefix: "/inventory/", Methods: []string{"GET"}},
			{Identity: "spiffe://zetashield.local/ns/default/sa/orders-service", PathPrefix: "/orders/", Methods: []string{"GET"}},
			{Identity: "spiffe://zetashield.local/ns/default/sa/payments-service", PathPrefix: "/payments/", Methods: []string{"GET", "POST"}},
		},
	}

	tests := []struct {
		name     string
		identity string
		method   string
		path     string
		want     bool
	}{
		{"frontend reads orders", "spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", "/orders/list", true},
		{"frontend posts payments", "spiffe://zetashield.local/ns/default/sa/frontend-service", "POST", "/payments/charge", true},
		{"frontend reads inventory", "spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", "/inventory/status", true},
		{"orders reads own domain", "spiffe://zetashield.local/ns/default/sa/orders-service", "GET", "/orders/list", true},
		{"payments reads own domain", "spiffe://zetashield.local/ns/default/sa/payments-service", "GET", "/payments/balance", true},
		{"orders blocked from payments", "spiffe://zetashield.local/ns/default/sa/orders-service", "GET", "/payments/balance", false},
		{"payments blocked from orders", "spiffe://zetashield.local/ns/default/sa/payments-service", "GET", "/orders/list", false},
		{"orders blocked from inventory", "spiffe://zetashield.local/ns/default/sa/orders-service", "GET", "/inventory/status", false},
		{"frontend wrong method on orders", "spiffe://zetashield.local/ns/default/sa/frontend-service", "POST", "/orders/create", false},
		{"frontend delete on payments", "spiffe://zetashield.local/ns/default/sa/frontend-service", "DELETE", "/payments/x", false},
		{"unknown service", "spiffe://zetashield.local/ns/default/sa/attacker-service", "GET", "/orders/list", false},
		{"empty identity", "", "GET", "/orders/list", false},
		{"admin path probe", "spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", "/admin/delete", false},
		{"root path probe", "spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", "/", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, got := checkPolicy(tt.identity, tt.method, tt.path)
			if got != tt.want {
				t.Errorf("checkPolicy(%q, %q, %q) = %v, want %v",
					tt.identity, tt.method, tt.path, got, tt.want)
			}
		})
	}
}

func TestRouteFor(t *testing.T) {
	activeSnapshot.Store(nil)

	policy = PolicyConfig{
		Routes: map[string]string{
			"/orders/":    "http://127.0.0.1:9091",
			"/payments/":  "http://127.0.0.1:9092",
			"/inventory/": "http://127.0.0.1:9099",
		},
	}

	tests := []struct {
		name    string
		path    string
		wantURL string
		wantOK  bool
	}{
		{"orders route", "/orders/list", "http://127.0.0.1:9091", true},
		{"payments route", "/payments/balance", "http://127.0.0.1:9092", true},
		{"inventory route", "/inventory/status", "http://127.0.0.1:9099", true},
		{"unknown path", "/admin/delete", "", false},
		{"root path", "/", "", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			url, ok := routeFor(tt.path)
			if ok != tt.wantOK || url != tt.wantURL {
				t.Errorf("routeFor(%q) = (%q, %v), want (%q, %v)",
					tt.path, url, ok, tt.wantURL, tt.wantOK)
			}
		})
	}
}

// ---------- Track 1 Hardening Tests (New L7 & Defense Invariants) ----------

func TestPathTraversalRejection(t *testing.T) {
	unsafePaths := []string{
		"/orders/../admin",
		"/orders/%2e%2e/admin",
		"/orders/..",
		"/orders/..\\admin",
		"/orders\x00admin",
		"/payments/..%2fadmin",
	}

	for _, path := range unsafePaths {
		t.Run("unsafe_"+path, func(t *testing.T) {
			if isSafePath(path) {
				t.Errorf("isSafePath(%q) = true, want false (path traversal vulnerability!)", path)
			}
			if _, allowed := checkPolicy("spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", path); allowed {
				t.Errorf("checkPolicy allowed unsafe path %q", path)
			}
			if _, routable := routeFor(path); routable {
				t.Errorf("routeFor routed unsafe path %q", path)
			}
		})
	}
}

func TestSegmentBoundaryPrefixMatching(t *testing.T) {
	policy = PolicyConfig{
		Rules: []PolicyRule{
			{Identity: "spiffe://zetashield.local/ns/default/sa/frontend-service", PathPrefix: "/orders", Methods: []string{"GET"}},
		},
		Routes: map[string]string{
			"/orders": "http://127.0.0.1:9091",
		},
	}
	activeSnapshot.Store(nil)

	// Legitimate paths under /orders
	if _, ok := checkPolicy("spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", "/orders"); !ok {
		t.Errorf("expected /orders to be allowed")
	}
	if _, ok := checkPolicy("spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", "/orders/list"); !ok {
		t.Errorf("expected /orders/list to be allowed")
	}

	// Sibling prefix bypass attempt (/orders-secret must NEVER match rule for /orders)
	if _, ok := checkPolicy("spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", "/orders-secret"); ok {
		t.Errorf("CRITICAL: checkPolicy matched /orders-secret against /orders prefix rule!")
	}
	if _, ok := routeFor("/orders-secret"); ok {
		t.Errorf("CRITICAL: routeFor matched /orders-secret against /orders route!")
	}
}

func TestIdentityRevocationKillSwitch(t *testing.T) {
	identity := "spiffe://zetashield.local/ns/default/sa/compromised-service"

	snap := &GatewaySnapshot{
		Policy: PolicyConfig{
			Rules: []PolicyRule{
				{Identity: identity, PathPrefix: "/orders/", Methods: []string{"GET"}},
			},
			Routes: map[string]string{"/orders/": "http://127.0.0.1:9091"},
		},
		RevokedSet: map[string]bool{
			identity: true, // Static revocation in YAML
		},
		Proxies: make(map[string]*httputil.ReverseProxy),
	}
	activeSnapshot.Store(snap)

	// Verify static revocation
	matchedRule, allowed := checkPolicy(identity, "GET", "/orders/list")
	if allowed || matchedRule != "revoked" {
		t.Errorf("checkPolicy on statically revoked identity returned allowed=%v, matched=%q; want allowed=false, matched=revoked", allowed, matchedRule)
	}

	// Verify real-time dynamic revocation via sync.Map (Control Plane API Kill-Switch)
	activeIdentity := "spiffe://zetashield.local/ns/default/sa/valid-service"
	snap2 := &GatewaySnapshot{
		Policy: PolicyConfig{
			Rules: []PolicyRule{
				{Identity: activeIdentity, PathPrefix: "/orders/", Methods: []string{"GET"}},
			},
			Routes: map[string]string{"/orders/": "http://127.0.0.1:9091"},
		},
		RevokedSet: make(map[string]bool),
		Proxies:    make(map[string]*httputil.ReverseProxy),
	}
	activeSnapshot.Store(snap2)

	// Should be allowed initially
	if _, ok := checkPolicy(activeIdentity, "GET", "/orders/list"); !ok {
		t.Errorf("activeIdentity should be allowed before dynamic revocation")
	}

	// Admin executes 1-click revocation
	dynamicRevoked.Store(activeIdentity, true)
	defer dynamicRevoked.Delete(activeIdentity)

	matchedRule, allowed = checkPolicy(activeIdentity, "GET", "/orders/list")
	if allowed || matchedRule != "revoked" {
		t.Errorf("checkPolicy on dynamically revoked identity returned allowed=%v, matched=%q; want allowed=false, matched=revoked", allowed, matchedRule)
	}
}

func TestTokenBucketRateLimiter(t *testing.T) {
	tb := newTokenBucket(5, 5) // 5 tokens capacity, 5 refill/sec

	// Exhaust burst
	for i := 0; i < 5; i++ {
		if !tb.Allow() {
			t.Fatalf("token #%d should have been allowed from burst", i+1)
		}
	}

	// 6th request must be rate limited immediately
	if tb.Allow() {
		t.Errorf("request after burst exhausted should be rate limited")
	}

	// Sleep 250ms -> refills ~1.25 tokens
	time.Sleep(250 * time.Millisecond)
	if !tb.Allow() {
		t.Errorf("request after refill interval should be allowed")
	}
}

func TestCryptographicAuditHashChainVerification(t *testing.T) {
	tempDir := t.TempDir()
	logPath := filepath.Join(tempDir, "test_audit.log.jsonl")

	// Create and write 5 legitimate chained audit entries
	prevHash := GenesisHash
	file, err := os.Create(logPath)
	if err != nil {
		t.Fatalf("failed to create temp file: %v", err)
	}

	for i := uint64(1); i <= 5; i++ {
		entry := AuditEntry{
			Index:         i,
			Timestamp:     time.Now().UTC().Format(time.RFC3339),
			ClientIP:      "127.0.0.1",
			Identity:      "spiffe://zetashield.local/ns/default/sa/frontend-service",
			TargetBackend: "http://127.0.0.1:9091",
			Method:        "GET",
			Path:          "/orders/list",
			StatusCode:    200,
			Decision:      "ALLOW",
			Reason:        "matched allow rule",
			DurationUS:    450,
			PrevHash:      prevHash,
		}
		entry.EntryHash = computeEntryHash(entry)
		prevHash = entry.EntryHash

		bytes, _ := json.Marshal(entry)
		file.Write(bytes)
		file.WriteString("\n")
	}
	file.Close()

	// 1. Verify valid file
	count, err := VerifyAuditFile(logPath)
	if err != nil {
		t.Fatalf("VerifyAuditFile failed on pristine chain: %v", err)
	}
	if count != 5 {
		t.Errorf("expected 5 verified entries, got %d", count)
	}

	// 2. Tamper Test: Modify 1 single character
	tamperedPath := filepath.Join(tempDir, "tampered_audit.log.jsonl")
	data, _ := os.ReadFile(logPath)
	tamperedStr := string(data)
	tamperedStr = tamperedStr[:len(tamperedStr)/2] + "X" + tamperedStr[len(tamperedStr)/2+1:]
	os.WriteFile(tamperedPath, []byte(tamperedStr), 0644)

	// Verification MUST catch the tampering
	_, err = VerifyAuditFile(tamperedPath)
	if err == nil {
		t.Errorf("CRITICAL: VerifyAuditFile failed to detect tampered audit log!")
	} else {
		t.Logf("Successfully caught tampered audit record: %v", err)
	}
}

// ---------- Track 3 & 3.5 Enterprise Hardening Unit Tests ----------

func TestLearningModeAndAutoDiscovery(t *testing.T) {
	// 1. Verify Mode Toggle
	setActiveMode("learning")
	if getActiveMode() != "learning" {
		t.Fatalf("expected mode 'learning', got %s", getActiveMode())
	}
	defer setActiveMode("enforce")

	// 2. Discover unmapped flow
	testID := "spiffe://zetashield.local/ns/default/sa/test-discovery-service"
	recordDiscoveredRule(testID, "GET", "/payments/balance")
	recordDiscoveredRule(testID, "POST", "/payments/charge")

	discovered := getDiscoveredRules()
	found := false
	for _, r := range discovered {
		if r.Identity == testID && r.PathPrefix == "/payments/" {
			found = true
			if len(r.Methods) != 2 {
				t.Errorf("expected 2 methods discovered, got %v", r.Methods)
			}
		}
	}
	if !found {
		t.Errorf("failed to discover rule for %s", testID)
	}

	// 3. Security Invariant: Revoked identities are STILL blocked in Learning Mode
	dynamicRevoked.Store(testID, true)
	defer dynamicRevoked.Delete(testID)

	matchedRule, allowed := checkPolicy(testID, "GET", "/orders/list")
	if allowed || matchedRule != "revoked" {
		t.Errorf("SECURITY INVARIANT VIOLATED: Revoked identity must be blocked in learning mode! got allowed=%v, rule=%s", allowed, matchedRule)
	}

	// 4. Security Invariant: Path Traversal is STILL blocked in Learning Mode
	if isSafePath("/orders/../secret") {
		t.Errorf("SECURITY INVARIANT VIOLATED: Path traversal must be blocked regardless of mode!")
	}
}

func TestControlPlaneAdminTokenAuth(t *testing.T) {
	adminToken := "zetashield-admin-secret-2026"

	// 1. Check checkAdminAuth unit logic
	req1 := httptest.NewRequest(http.MethodPost, "/api/v1/mode", nil)
	if checkAdminAuth(req1, adminToken) {
		t.Errorf("expected unauthenticated request to fail admin check")
	}

	req2 := httptest.NewRequest(http.MethodPost, "/api/v1/mode", nil)
	req2.Header.Set("X-ZetaShield-Admin-Token", "wrong-secret")
	if checkAdminAuth(req2, adminToken) {
		t.Errorf("expected wrong token to fail admin check")
	}

	req3 := httptest.NewRequest(http.MethodPost, "/api/v1/mode", nil)
	req3.Header.Set("X-ZetaShield-Admin-Token", adminToken)
	if !checkAdminAuth(req3, adminToken) {
		t.Errorf("expected valid X-ZetaShield-Admin-Token to pass admin check")
	}

	req4 := httptest.NewRequest(http.MethodPost, "/api/v1/mode", nil)
	req4.Header.Set("Authorization", "Bearer "+adminToken)
	if !checkAdminAuth(req4, adminToken) {
		t.Errorf("expected valid Bearer token to pass admin check")
	}

	// 2. Integration test against startControlServer handler
	tempDir := t.TempDir()
	auditFile := filepath.Join(tempDir, "control_audit.log.jsonl")
	srv := startControlServer(":0", auditFile, tempDir)
	defer srv.Close()

	// Unauthenticated POST /api/v1/revoke MUST return 401 Unauthorized
	body := bytes.NewBufferString(`{"identity":"frontend-service","action":"revoke"}`)
	unauthReq := httptest.NewRequest(http.MethodPost, "/api/v1/revoke", body)
	rec := httptest.NewRecorder()
	srv.Handler.ServeHTTP(rec, unauthReq)

	if rec.Code != http.StatusUnauthorized {
		t.Errorf("expected unauthenticated revoke to return 401, got %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), "unauthorized") {
		t.Errorf("expected body to contain 'unauthorized', got %q", rec.Body.String())
	}

	// Authenticated POST /api/v1/revoke MUST return 200 OK
	authBody := bytes.NewBufferString(`{"identity":"frontend-service","action":"revoke"}`)
	authReq := httptest.NewRequest(http.MethodPost, "/api/v1/revoke", authBody)
	authReq.Header.Set("X-ZetaShield-Admin-Token", adminToken)
	recAuth := httptest.NewRecorder()
	srv.Handler.ServeHTTP(recAuth, authReq)

	if recAuth.Code != http.StatusOK {
		t.Errorf("expected authenticated revoke to return 200, got %d (%s)", recAuth.Code, recAuth.Body.String())
	}

	// Cleanup revocation
	dynamicRevoked.Delete("spiffe://zetashield.local/ns/default/sa/frontend-service")
}

func TestAtomicTLSBundleReload(t *testing.T) {
	certPath := "../certs/proxy.pem"
	keyPath := "../certs/proxy-key.pem"
	caPath := "../certs/ca.pem"

	// 1. Test load valid bundle
	bundle, err := loadTLSBundle(certPath, keyPath, caPath)
	if err != nil {
		t.Fatalf("loadTLSBundle failed on valid certs: %v", err)
	}
	if bundle == nil || bundle.CAPool == nil {
		t.Fatalf("expected non-nil bundle and CAPool")
	}

	// 2. Test atomic swap
	activeTLSBundle.Store(bundle)
	loaded := activeTLSBundle.Load()
	if loaded != bundle {
		t.Errorf("atomic.Pointer mismatch on TLSBundle swap")
	}

	// 3. Test failure on non-existent file
	_, err = loadTLSBundle("non-existent-cert.pem", keyPath, caPath)
	if err == nil {
		t.Errorf("expected error on non-existent cert, got nil")
	}

	// Ensure active bundle remains intact despite failed candidate load
	if activeTLSBundle.Load() != bundle {
		t.Errorf("activeTLSBundle should remain untouched when a candidate load fails")
	}
}

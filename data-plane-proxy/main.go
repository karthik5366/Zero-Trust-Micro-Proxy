// main.go — ZetaShield V0.1 (Zero-Trust Proxy Spine)
// ====================================================
// WHAT THIS IS: Phase-1 Review-1 prototype.
// A Layer-7 reverse proxy that intercepts every HTTP request,
// identifies the caller, checks an explicit ALLOW policy,
// and denies everything else (deny-by-default) — logging every decision.
//
// WHAT IT ISN'T YET (V1.0 / Review-2 upgrades):
//   - Identity comes from a header here (spoofable, demo only).
//     V1.0 extracts it from the cryptographically verified x509 SAN field over mTLS.
//   - Policy is in-memory here. V1.0 queries the FastAPI/SQLite control
//     plane and FAILS CLOSED (503) if it is unreachable.
package main

import (
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "net/http/httputil"
    "net/url"
    "os"
    "strings"
    "sync"
    "time"
)

// ---------- Configuration ----------
const (
    proxyListenAddr = "0.0.0.0:8080"           // proxy: network-reachable
    backendAddr     = "http://127.0.0.1:9090"  // backend: LOCALHOST ONLY — non-bypassable
    auditLogFile    = "audit.log.jsonl"
)

// ---------- Policy (V0.1: in-memory; V1.0: FastAPI control plane) ----------
// Deny-by-default: a request is forwarded ONLY if it explicitly
// matches one of these rules. Anything unmatched => 403 + audit log.
type PolicyRule struct {
    Identity string // calling service identity
    Path     string // exact path, or prefix if it ends in "*"
    Method   string // HTTP method
}

var policyRules = []PolicyRule{
    {"frontend-proxy", "/api/v1/orders", "GET"},
    {"frontend-proxy", "/api/v1/cart", "GET"},
    {"frontend-proxy", "/api/v1/cart", "POST"},
}

func policyAllows(identity, method, path string) bool {
    for _, r := range policyRules {
        if r.Identity == identity && r.Method == method && pathMatches(r.Path, path) {
            return true
        }
    }
    return false // DENY BY DEFAULT
}

func pathMatches(pattern, path string) bool {
    if strings.HasSuffix(pattern, "*") {
        return strings.HasPrefix(path, strings.TrimSuffix(pattern, "*"))
    }
    return pattern == path
}

// ---------- Identity extraction ----------
// V0.1: caller declares identity in a header (spoofable — demo purpose only).
// V1.0: this exact function is replaced by x509 SAN extraction:
//     cert := r.TLS.VerifiedChains[0][0]
//     identity := cert.URIs[0].String()
func extractIdentity(r *http.Request) (string, bool) {
    id := r.Header.Get("X-Service-Identity")
    if id == "" {
        return "", false
    }
    return id, true
}

// ---------- Structured audit logging (survives unchanged into V1.0) ----------
type AuditEntry struct {
    Time     string `json:"timestamp"`
    Decision string `json:"decision"`
    Identity string `json:"identity"`
    Method   string `json:"method"`
    Path     string `json:"path"`
    Reason   string `json:"reason"`
}

var (
    auditMu   sync.Mutex
    auditFile *os.File
)

const (
    cReset = "\033[0m"
    cRed   = "\033[31m"
    cGreen = "\033[32m"
)

func writeAudit(e AuditEntry) {
    e.Time = time.Now().UTC().Format(time.RFC3339)
    auditMu.Lock()
    defer auditMu.Unlock()
    if auditFile != nil {
        json.NewEncoder(auditFile).Encode(e)
    }
    color := cGreen
    if e.Decision == "DENY" {
        color = cRed
    }
    fmt.Printf("%s[%s]%s identity=%-18s %-6s %-22s (%s)\n",
        color, e.Decision, cReset, e.Identity, e.Method, e.Path, e.Reason)
}

// ---------- Proxy ----------
func main() {
    backend, err := url.Parse(backendAddr)
    if err != nil {
        log.Fatal(err)
    }

    auditFile, err = os.OpenFile(auditLogFile, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
    if err != nil {
        log.Fatal(err)
    }
    defer auditFile.Close()

    proxy := httputil.NewSingleHostReverseProxy(backend)

    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        // STEP 1 — Identity: who is calling?
        identity, ok := extractIdentity(r)
        if !ok {
            writeAudit(AuditEntry{Decision: "DENY", Identity: "none",
                Method: r.Method, Path: r.URL.Path,
                Reason: "no identity presented (V1.0: no valid x509 certificate)"})
            http.Error(w, "403 Forbidden: no service identity", http.StatusForbidden)
            return
        }

        // STEP 2 — Authorization: is this identity ALLOWED this method+path?
        if !policyAllows(identity, r.Method, r.URL.Path) {
            writeAudit(AuditEntry{Decision: "DENY", Identity: identity,
                Method: r.Method, Path: r.URL.Path,
                Reason: "no matching ALLOW rule (deny-by-default)"})
            http.Error(w, "403 Forbidden: denied by policy", http.StatusForbidden)
            return
        }

        // STEP 3 — Forward to the protected backend (localhost-only).
        writeAudit(AuditEntry{Decision: "ALLOW", Identity: identity,
            Method: r.Method, Path: r.URL.Path,
            Reason: "matched explicit ALLOW rule"})
        proxy.ServeHTTP(w, r)
    })

    fmt.Println("ZetaShield V0.1 — Zero-Trust Proxy Spine")
    fmt.Printf("  proxy   : %s  (network reachable)\n", proxyListenAddr)
    fmt.Printf("  backend : %s  (LOCALHOST ONLY — non-bypassable)\n", backendAddr)
    fmt.Printf("  audit   : %s\n\n", auditLogFile)
    log.Fatal(http.ListenAndServe(proxyListenAddr, nil))
}
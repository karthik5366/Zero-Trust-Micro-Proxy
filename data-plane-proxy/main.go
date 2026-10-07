// main.go — ZetaShield V1.0 (Zero-Trust Gateway)
// ============================================================
// ARCHITECTURE (per supervisor feedback — consolidated):
//
//	[Callers] --mTLS--> [THIS GATEWAY] --HTTP--> [Backends]
package main

import (
	"crypto/tls"
	"crypto/x509"
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

	"gopkg.in/yaml.v3"
)

// ---------- Policy configuration (policy.yaml) ----------

type PolicyConfig struct {
	Version string            `yaml:"version"`
	Routes  map[string]string `yaml:"routes"`
	Rules   []PolicyRule      `yaml:"rules"`
}

type PolicyRule struct {
	Identity   string   `yaml:"identity"`
	PathPrefix string   `yaml:"path_prefix"`
	Methods    []string `yaml:"methods"`
}

var (
	policy   PolicyConfig
	policyMu sync.RWMutex
)

func loadPolicy(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("cannot read policy.yaml: %w", err)
	}
	policyMu.Lock()
	defer policyMu.Unlock()
	return yaml.Unmarshal(data, &policy)
}

func checkPolicy(identity, method, path string) (string, bool) {
	shortName := identity
	if idx := strings.LastIndex(identity, "/"); idx >= 0 {
		shortName = identity[idx+1:]
	}

	policyMu.RLock()
	defer policyMu.RUnlock()

	for _, rule := range policy.Rules {
		idMatch := rule.Identity == identity || rule.Identity == shortName
		if !idMatch {
			continue
		}
		if !strings.HasPrefix(path, rule.PathPrefix) {
			continue
		}
		for _, m := range rule.Methods {
			if m == method || m == "*" {
				return rule.Identity, true
			}
		}
	}
	return "", false // DENY BY DEFAULT
}

func routeFor(path string) (string, bool) {
	policyMu.RLock()
	defer policyMu.RUnlock()

	bestPrefix := ""
	bestTarget := ""
	for prefix, target := range policy.Routes {
		if strings.HasPrefix(path, prefix) && len(prefix) > len(bestPrefix) {
			bestPrefix = prefix
			bestTarget = target
		}
	}
	if bestTarget != "" {
		return bestTarget, true
	}
	return "", false
}

// ---------- Identity extraction (mTLS SAN) ----------

func extractIdentity(r *http.Request) (string, bool) {
	if r.TLS == nil || len(r.TLS.PeerCertificates) == 0 {
		return "", false
	}
	cert := r.TLS.PeerCertificates[0]
	if len(cert.URIs) > 0 {
		return cert.URIs[0].String(), true
	}
	return "", false
}

// ---------- Audit logging ----------

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
	fmt.Printf("%s[%s]%s identity=%-25s %-6s %-25s (%s)\n",
		color, e.Decision, cReset, e.Identity, e.Method, e.Path, e.Reason)
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

// ---------- Main ----------

func main() {
	policyPath := getEnv("ZS_POLICY_PATH", "../policy.yaml")
	if err := loadPolicy(policyPath); err != nil {
		log.Fatalf("FATAL: %v", err)
	}
	fmt.Printf("[policy] loaded %s — routes + rules active\n", policyPath)

	auditPath := getEnv("ZS_AUDIT_PATH", "audit.log.jsonl")
	var err error
	auditFile, err = os.OpenFile(auditPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal(err)
	}
	defer auditFile.Close()

	caPath := getEnv("ZS_CA_PATH", "../certs/ca.pem")
	caPEM, err := os.ReadFile(caPath)
	if err != nil {
		log.Fatalf("FATAL: cannot read CA cert: %v", err)
	}
	caPool := x509.NewCertPool()
	if !caPool.AppendCertsFromPEM(caPEM) {
		log.Fatal("FATAL: failed to parse CA certificate")
	}

	certPath := getEnv("ZS_CERT_PATH", "../certs/proxy.pem")
	keyPath := getEnv("ZS_KEY_PATH", "../certs/proxy-key.pem")
	gatewayCert, err := tls.LoadX509KeyPair(certPath, keyPath)
	if err != nil {
		log.Fatalf("FATAL: cannot load gateway cert: %v", err)
	}

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// CHECKPOINT 1: Identity (mTLS)
		identity, ok := extractIdentity(r)
		if !ok {
			writeAudit(AuditEntry{Decision: "DENY", Identity: "none",
				Method: r.Method, Path: r.URL.Path,
				Reason: "no valid x509 certificate presented"})
			http.Error(w, "403 Forbidden: no service identity", http.StatusForbidden)
			return
		}

		// CHECKPOINT 2: Authorization (deny-by-default)
		if _, allowed := checkPolicy(identity, r.Method, r.URL.Path); !allowed {
			writeAudit(AuditEntry{Decision: "DENY", Identity: identity,
				Method: r.Method, Path: r.URL.Path,
				Reason: "no matching ALLOW rule (deny-by-default)"})
			http.Error(w, "403 Forbidden: denied by policy", http.StatusForbidden)
			return
		}

		// CHECKPOINT 3: Route
		backendURL, routable := routeFor(r.URL.Path)
		if !routable {
			writeAudit(AuditEntry{Decision: "DENY", Identity: identity,
				Method: r.Method, Path: r.URL.Path,
				Reason: "no route configured for path"})
			http.Error(w, "404 Not Found: no such service", http.StatusNotFound)
			return
		}

		backend, err := url.Parse(backendURL)
		if err != nil {
			writeAudit(AuditEntry{Decision: "ERROR", Identity: identity,
				Method: r.Method, Path: r.URL.Path,
				Reason: "backend URL parse error"})
			http.Error(w, "503 Service Unavailable", http.StatusServiceUnavailable)
			return
		}

		proxy := httputil.NewSingleHostReverseProxy(backend)
		proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
			writeAudit(AuditEntry{Decision: "ERROR", Identity: identity,
				Method: r.Method, Path: r.URL.Path,
				Reason: fmt.Sprintf("backend unreachable: %v (fail-closed)", err)})
			http.Error(w, "503 Service Unavailable (fail-closed)", http.StatusServiceUnavailable)
		}

		writeAudit(AuditEntry{Decision: "ALLOW", Identity: identity,
			Method: r.Method, Path: r.URL.Path,
			Reason: fmt.Sprintf("matched ALLOW rule, routed to %s", backendURL)})
		proxy.ServeHTTP(w, r)
	})

	listenAddr := getEnv("ZS_LISTEN_ADDR", ":8443")
	server := &http.Server{
		Addr:    listenAddr,
		Handler: handler,
		TLSConfig: &tls.Config{
			ClientCAs:    caPool,
			ClientAuth:   tls.RequireAndVerifyClientCert,
			Certificates: []tls.Certificate{gatewayCert},
			MinVersion:   tls.VersionTLS12,
		},
	}

	fmt.Println("╔══════════════════════════════════════════════════════╗")
	fmt.Println("║  ZetaShield V1.0 — Zero-Trust Gateway                ║")
	fmt.Println("╠══════════════════════════════════════════════════════╣")
	fmt.Println("║  mTLS      : ENABLED (client certs required)        ║")
	fmt.Println("║  Identity  : x509 SAN (unforgeable)                 ║")
	fmt.Println("║  Policy    : policy.yaml (deny-by-default)          ║")
	fmt.Println("║  Audit     : audit.log.jsonl (every decision)       ║")
	fmt.Println("║  Backends  : orders:9091, payments:9092 (localhost) ║")
	fmt.Println("╚══════════════════════════════════════════════════════╝")
	fmt.Printf("  Gateway listening on %s (mTLS required)\n\n", listenAddr)

	log.Fatal(server.ListenAndServeTLS("", ""))
}

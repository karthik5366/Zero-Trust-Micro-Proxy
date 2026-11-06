package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync/atomic"
	"syscall"
	"time"
)

// tlsErrorLogWriter captures TLS handshake failures directly from net/http.
type tlsErrorLogWriter struct{}

func (w *tlsErrorLogWriter) Write(p []byte) (n int, err error) {
	msg := string(p)
	if strings.Contains(msg, "TLS handshake error from ") {
		parts := strings.SplitN(msg, "TLS handshake error from ", 2)
		if len(parts) == 2 {
			sub := parts[1]
			idx := strings.Index(sub, ": ")
			clientIP := "unknown"
			reason := strings.TrimSpace(sub)
			if idx != -1 {
				clientIP = sub[:idx]
				reason = strings.TrimSpace(sub[idx+2:])
			}

			// Handshake rate limiter check
			CheckHandshakeRate(clientIP)

			if globalAuditLogger != nil {
				globalAuditLogger.Log(AuditEntry{
					Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
					ClientIP:      clientIP,
					Identity:      "unverified",
					TargetBackend: "none",
					Method:        "TLS_HANDSHAKE",
					Path:          "/",
					StatusCode:    495, // SSL Certificate Error
					Decision:      "TLS_REJECT",
					Reason:        fmt.Sprintf("tls handshake abort: %s", reason),
					DurationUS:    50, // TLS handshake processing time estimate
				})
			}
		}
	}
	return len(p), nil
}

// extractIdentity pulls the authenticated SPIFFE URI or CommonName from client certificate.
func extractIdentity(r *http.Request) (string, bool) {
	if r.TLS == nil || len(r.TLS.PeerCertificates) == 0 {
		return "", false
	}
	cert := r.TLS.PeerCertificates[0]
	if len(cert.URIs) > 0 {
		return cert.URIs[0].String(), true
	}
	if cert.Subject.CommonName != "" {
		return cert.Subject.CommonName, true
	}
	return "", false
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

// TLSBundle wraps the active server certificate and trusted client CA pool.
type TLSBundle struct {
	Cert   tls.Certificate
	CAPool *x509.CertPool
}

var activeTLSBundle atomic.Pointer[TLSBundle]

// loadTLSBundle loads and validates the server keypair and client CA pool from disk.
func loadTLSBundle(certPath, keyPath, caPath string) (*TLSBundle, error) {
	cert, err := tls.LoadX509KeyPair(certPath, keyPath)
	if err != nil {
		return nil, fmt.Errorf("load keypair failed: %w", err)
	}

	caPEM, err := os.ReadFile(caPath)
	if err != nil {
		return nil, fmt.Errorf("read CA cert failed: %w", err)
	}
	caPool := x509.NewCertPool()
	if !caPool.AppendCertsFromPEM(caPEM) {
		return nil, fmt.Errorf("parse CA cert failed: no valid PEM certificates found")
	}

	return &TLSBundle{
		Cert:   cert,
		CAPool: caPool,
	}, nil
}

// startCertWatcher monitors certPath, keyPath, and caPath for disk modifications
// and hot-swaps activeTLSBundle atomically with zero dropped connections and zero downtime.
func startCertWatcher(certPath, keyPath, caPath string) {
	go func() {
		getModTime := func(p string) time.Time {
			fi, err := os.Stat(p)
			if err != nil {
				return time.Time{}
			}
			return fi.ModTime()
		}

		lastMod := getModTime(certPath)
		if m := getModTime(keyPath); m.After(lastMod) {
			lastMod = m
		}
		if m := getModTime(caPath); m.After(lastMod) {
			lastMod = m
		}

		ticker := time.NewTicker(1 * time.Second)
		defer ticker.Stop()

		for range ticker.C {
			m1 := getModTime(certPath)
			m2 := getModTime(keyPath)
			m3 := getModTime(caPath)

			maxMod := m1
			if m2.After(maxMod) {
				maxMod = m2
			}
			if m3.After(maxMod) {
				maxMod = m3
			}

			if maxMod.After(lastMod) {
				time.Sleep(150 * time.Millisecond) // Allow atomic file write to settle
				bundle, err := loadTLSBundle(certPath, keyPath, caPath)
				if err != nil {
					log.Printf("[tls-watcher] cert reload failed (retaining existing active certs): %v", err)
					continue
				}

				activeTLSBundle.Store(bundle)
				lastMod = maxMod
				log.Println("[tls] hot-reloaded certificates with zero downtime")

				if globalAuditLogger != nil {
					globalAuditLogger.Log(AuditEntry{
						Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
						ClientIP:      "127.0.0.1",
						Identity:      "control-plane-cert-watcher",
						TargetBackend: "none",
						Method:        "CONTROL",
						Path:          "/tls/reload",
						StatusCode:    http.StatusOK,
						Decision:      "CERT_RELOAD",
						Reason:        "zero-downtime x509 cert hot-reload",
						DurationUS:    10,
					})
				}
			}
		}
	}()
}

func main() {
	fmt.Println("╔══════════════════════════════════════════════════════╗")
	fmt.Println("║  ZetaShield V2.1 — Hardened Zero-Trust Data Plane    ║")
	fmt.Println("╠══════════════════════════════════════════════════════╣")
	fmt.Println("║  mTLS      : STRICT (x509 client verification)       ║")
	fmt.Println("║  Identity  : SPIFFE SAN (unforgeable cryptographic)  ║")
	fmt.Println("║  Engine    : Lock-Free Atomic Snapshots              ║")
	fmt.Println("║  Audit     : Tamper-Evident SHA-256 Hash Chain       ║")
	fmt.Println("║  Defense   : Token-Bucket & L7 Path Traversal Guard  ║")
	fmt.Println("╚══════════════════════════════════════════════════════╝")

	policyPath := getEnv("ZS_POLICY_PATH", "../policy.yaml")
	if err := loadPolicy(policyPath); err != nil {
		log.Fatalf("FATAL: %v", err)
	}
	fmt.Printf("[policy] Initialized policy snapshot from %s\n", policyPath)
	startPolicyWatcher(policyPath)

	auditPath := getEnv("ZS_AUDIT_PATH", "audit.log.jsonl")
	var err error
	globalAuditLogger, err = NewAuditLogger(auditPath)
	if err != nil {
		log.Fatalf("FATAL: audit logger init failed: %v", err)
	}
	defer globalAuditLogger.Close()

	caPath := getEnv("ZS_CA_PATH", "../certs/ca.pem")
	certPath := getEnv("ZS_CERT_PATH", "../certs/proxy.pem")
	keyPath := getEnv("ZS_KEY_PATH", "../certs/proxy-key.pem")

	initialBundle, err := loadTLSBundle(certPath, keyPath, caPath)
	if err != nil {
		log.Fatalf("FATAL: cannot load initial TLS bundle: %v", err)
	}
	activeTLSBundle.Store(initialBundle)
	fmt.Printf("[tls] Initialized mTLS bundle (proxy: %s, ca: %s)\n", certPath, caPath)
	startCertWatcher(certPath, keyPath, caPath)

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		sc := &statusCaptureResponseWriter{ResponseWriter: w}

		clientIP := r.RemoteAddr
		identity := "none"
		targetBackend := "none"
		decision := "DENY"
		reason := "unhandled"

		// Single-Outcome Request Pipeline: Defer final audit log emission
		defer func() {
			elapsed := time.Since(start)
			durationUS := elapsed.Microseconds()
			if durationUS <= 0 {
				durationUS = elapsed.Nanoseconds() / 1000
				if durationUS <= 0 {
					durationUS = 1 // Minimum 1 microsecond resolution
				}
			}
			statusCode := sc.statusCode
			if statusCode == 0 {
				statusCode = http.StatusOK
			}

			// Fail-closed backend outage capture (eliminates Test 7 double logging)
			if sc.backendError != nil {
				decision = "ERROR"
				statusCode = http.StatusServiceUnavailable
				reason = fmt.Sprintf("backend unreachable: %v (fail-closed)", sc.backendError)
			}

			globalAuditLogger.Log(AuditEntry{
				Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
				ClientIP:      clientIP,
				Identity:      identity,
				TargetBackend: targetBackend,
				Method:        r.Method,
				Path:          r.URL.Path,
				StatusCode:    statusCode,
				Decision:      decision,
				Reason:        reason,
				DurationUS:    durationUS,
			})
		}()

		// CHECKPOINT 1: Identity Extraction (mTLS SAN)
		id, ok := extractIdentity(r)
		if !ok {
			decision = "DENY"
			reason = "no valid x509 client certificate presented"
			http.Error(sc, "403 Forbidden: no service identity", http.StatusForbidden)
			return
		}
		identity = id

		// CHECKPOINT 2: Path Traversal Guard
		if !isSafePath(r.URL.Path) {
			decision = "DENY"
			reason = "path traversal or invalid character detected"
			http.Error(sc, "400 Bad Request: unsafe path", http.StatusBadRequest)
			return
		}

		// CHECKPOINT 3: Policy Authorization (Deny-by-Default / Learning Mode)
		matchedRule, allowed := checkPolicy(identity, r.Method, r.URL.Path)

		snap := activeSnapshot.Load()
		mode := getActiveMode()
		defaultRate := 5000.0
		defaultBurst := 1000.0
		if snap != nil {
			defaultRate = snap.Policy.DefaultRateLimit
			defaultBurst = snap.Policy.DefaultBurst
		}

		if !allowed {
			if matchedRule == "revoked" {
				decision = "DENY"
				reason = "identity is revoked (kill-switch active)"
				http.Error(sc, "403 Forbidden: identity revoked", http.StatusForbidden)
				return
			}

			if mode == "learning" {
				decision = "SHADOW_DENY"
				reason = "learning mode: unmapped flow allowed & recorded for policy discovery"
				recordDiscoveredRule(identity, r.Method, r.URL.Path)
				// Allowed to proceed for dry-run observation & discovery
			} else {
				decision = "DENY"
				reason = "no matching ALLOW rule (deny-by-default)"
				http.Error(sc, "403 Forbidden: denied by policy", http.StatusForbidden)
				return
			}
		} else {
			decision = "ALLOW"
			reason = fmt.Sprintf("matched policy rule for %s", matchedRule)
		}

		// CHECKPOINT 4: Per-Identity Rate Limiting
		if !CheckIdentityRate(identity, defaultRate, defaultBurst) {
			decision = "RATE_LIMITED"
			reason = fmt.Sprintf("exceeded identity rate limit (%.0f req/s)", defaultRate)
			http.Error(sc, "429 Too Many Requests: rate limit exceeded", http.StatusTooManyRequests)
			return
		}

		// CHECKPOINT 5: Pre-Warmed Reverse Proxy Dispatch
		proxy, target, routable := getProxyForRoute(r.URL.Path)
		if !routable {
			decision = "DENY"
			reason = "no route configured for path"
			http.Error(sc, "404 Not Found: no such service", http.StatusNotFound)
			return
		}
		targetBackend = target
		reason = fmt.Sprintf("routed to %s", target)

		// Pass identity internally to proxy director for Hop-2 HMAC injection
		r.Header.Set("X-Identity-Internal", identity)
		proxy.ServeHTTP(sc, r)
	})

	listenAddr := getEnv("ZS_LISTEN_ADDR", ":8443")
	server := &http.Server{
		Addr:     listenAddr,
		Handler:  handler,
		ErrorLog: log.New(&tlsErrorLogWriter{}, "", 0),
		TLSConfig: &tls.Config{
			ClientCAs:    initialBundle.CAPool,
			ClientAuth:   tls.RequireAndVerifyClientCert,
			Certificates: []tls.Certificate{initialBundle.Cert},
			MinVersion:   tls.VersionTLS12,
			GetConfigForClient: func(hello *tls.ClientHelloInfo) (*tls.Config, error) {
				bundle := activeTLSBundle.Load()
				if bundle == nil {
					return nil, fmt.Errorf("tls bundle not loaded")
				}
				return &tls.Config{
					ClientCAs:    bundle.CAPool,
					ClientAuth:   tls.RequireAndVerifyClientCert,
					Certificates: []tls.Certificate{bundle.Cert},
					MinVersion:   tls.VersionTLS12,
				}, nil
			},
		},
	}

	// Embedded Control Plane & Live Telemetry Server (Port 8444)
	controlAddr := getEnv("ZS_CONTROL_ADDR", ":8444")
	dashboardDir := getEnv("ZS_DASHBOARD_DIR", "../telemetry-dashboard")
	controlServer := startControlServer(controlAddr, auditPath, dashboardDir)

	// Graceful Shutdown
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	go func() {
		fmt.Printf("  Gateway active on %s (mTLS strictly enforced)\n\n", listenAddr)
		if err := server.ListenAndServeTLS("", ""); err != nil && err != http.ErrServerClosed {
			log.Fatalf("FATAL server error: %v", err)
		}
	}()

	<-ctx.Done()
	fmt.Println("\n[shutdown] Graceful shutdown initiated...")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Printf("[shutdown] Server shutdown error: %v", err)
	}
	if err := controlServer.Shutdown(shutdownCtx); err != nil {
		log.Printf("[shutdown] Control server shutdown error: %v", err)
	}
	globalAuditLogger.Close()
	fmt.Println("[shutdown] ZetaShield cleanly stopped. All audit buffers flushed to disk.")
}

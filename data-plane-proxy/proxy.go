package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
	"time"
)

// statusCaptureResponseWriter intercepts status codes and byte counts for single-decision audit logging.
type statusCaptureResponseWriter struct {
	http.ResponseWriter
	statusCode   int
	bytesWritten int64
	backendError error
}

func (w *statusCaptureResponseWriter) WriteHeader(code int) {
	w.statusCode = code
	w.ResponseWriter.WriteHeader(code)
}

func (w *statusCaptureResponseWriter) Write(b []byte) (int, error) {
	if w.statusCode == 0 {
		w.statusCode = http.StatusOK
	}
	n, err := w.ResponseWriter.Write(b)
	w.bytesWritten += int64(n)
	return n, err
}

func (w *statusCaptureResponseWriter) Flush() {
	if flusher, ok := w.ResponseWriter.(http.Flusher); ok {
		flusher.Flush()
	}
}

// sharedTransport reuses persistent TCP connection pools across all reverse proxy instances.
var sharedTransport = &http.Transport{
	MaxIdleConns:        256,
	MaxIdleConnsPerHost: 100,
	IdleConnTimeout:     90 * time.Second,
	DisableKeepAlives:   false,
}

// buildReverseProxy constructs a pre-warmed reverse proxy with header sanitation and Hop-2 HMAC signing.
func buildReverseProxy(targetURL string) (*httputil.ReverseProxy, error) {
	backend, err := url.Parse(targetURL)
	if err != nil {
		return nil, fmt.Errorf("invalid backend target url %s: %w", targetURL, err)
	}

	proxy := httputil.NewSingleHostReverseProxy(backend)
	proxy.Transport = sharedTransport

	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)

		// 1. Sanitize: Strip any untrusted caller-supplied X-ZetaShield-* headers
		for h := range req.Header {
			if strings.HasPrefix(strings.ToLower(h), "x-zetashield-") {
				req.Header.Del(h)
			}
		}

		// 2. Identity Propagation: Inject authenticated SPIFFE identity into internal Hop-2 request
		identity := req.Header.Get("X-Identity-Internal")
		req.Header.Del("X-Identity-Internal") // Remove internal transport artifact

		if identity != "" {
			req.Header.Set("X-ZetaShield-Identity", identity)

			// 3. Hop-2 Cryptographic Proof: Sign Hop-2 request if HMAC secret is configured
			secret := os.Getenv("ZS_HMAC_SECRET")
			if secret != "" {
				payload := fmt.Sprintf("%s|%s|%s", req.Method, req.URL.Path, identity)
				mac := hmac.New(sha256.New, []byte(secret))
				mac.Write([]byte(payload))
				req.Header.Set("X-ZetaShield-Signature", hex.EncodeToString(mac.Sum(nil)))
			}
		}
	}

	// Fail-closed error handler
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		if sc, ok := w.(*statusCaptureResponseWriter); ok {
			sc.backendError = err
		}
		w.Header().Set("X-ZetaShield-Backend-Error", "true")
		http.Error(w, "503 Service Unavailable (fail-closed)", http.StatusServiceUnavailable)
	}

	return proxy, nil
}

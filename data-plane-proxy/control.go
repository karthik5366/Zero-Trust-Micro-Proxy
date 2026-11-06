package main

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

var controlStartTime = time.Now()

// checkAdminAuth verifies the admin bearer token or X-ZetaShield-Admin-Token header.
func checkAdminAuth(r *http.Request, adminToken string) bool {
	if adminToken == "" {
		return true
	}
	token := r.Header.Get("X-ZetaShield-Admin-Token")
	if token != "" && subtle.ConstantTimeCompare([]byte(token), []byte(adminToken)) == 1 {
		return true
	}
	authHeader := r.Header.Get("Authorization")
	if strings.HasPrefix(authHeader, "Bearer ") {
		bearer := strings.TrimPrefix(authHeader, "Bearer ")
		if subtle.ConstantTimeCompare([]byte(bearer), []byte(adminToken)) == 1 {
			return true
		}
	}
	return false
}

// enableCORS wraps a handler to permit cross-origin access from dashboards and tools.
func enableCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// startControlServer starts the embedded Control Plane & Telemetry server on ZS_CONTROL_ADDR.
func startControlServer(addr, auditPath, dashboardDir string) *http.Server {
	adminToken := getEnv("ZS_ADMIN_TOKEN", "zetashield-admin-secret-2026")
	mux := http.NewServeMux()

	// 1. Cluster Status & Health Endpoint
	mux.HandleFunc("/api/v1/status", func(w http.ResponseWriter, r *http.Request) {
		snap := activeSnapshot.Load()
		mode := getActiveMode()

		// Real-time ledger verification
		count, err := VerifyAuditFile(auditPath)
		ledgerStatus := map[string]any{
			"verified_records": count,
			"latest_hash":      globalAuditLogger.prevHash,
			"intact":           err == nil,
			"error_msg":        "",
		}
		if err != nil {
			ledgerStatus["error_msg"] = err.Error()
		}

		// Collect revoked identities (static YAML + dynamic 1-click)
		revokedMap := make(map[string]bool)
		if snap != nil {
			for _, id := range snap.Policy.RevokedIdentities {
				revokedMap[id] = true
			}
		}
		dynamicRevoked.Range(func(key, value any) bool {
			revokedMap[key.(string)] = true
			return true
		})

		revokedList := make([]string, 0, len(revokedMap))
		for id := range revokedMap {
			revokedList = append(revokedList, id)
		}

		discovered := getDiscoveredRules()

		// Generate candidate YAML snippet from discovered rules
		var yamlSnippet strings.Builder
		if len(discovered) > 0 {
			yamlSnippet.WriteString("# Auto-Generated Rules from Learning Mode\n")
			for _, r := range discovered {
				yamlSnippet.WriteString(fmt.Sprintf("- identity: %s\n  path_prefix: %s\n  methods: %v\n",
					r.Identity, r.PathPrefix, r.Methods))
			}
		}

		resp := map[string]any{
			"version":            "2.1-enterprise",
			"uptime_sec":         int(time.Since(controlStartTime).Seconds()),
			"mode":               mode,
			"metrics":            globalAuditLogger.GetMetrics(),
			"ledger":             ledgerStatus,
			"routes":             snap.Policy.Routes,
			"rules":              snap.Policy.Rules,
			"revoked_identities": revokedList,
			"discovered_rules":   discovered,
			"discovered_yaml":    yamlSnippet.String(),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	})

	// 2. Recent Audit Stream Query
	mux.HandleFunc("/api/v1/audit", func(w http.ResponseWriter, r *http.Request) {
		entries, err := globalAuditLogger.GetRecentEntries(100)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error": "%v"}`, err), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(entries)
	})

	// 3. Server-Sent Events (SSE) Live Feed
	mux.HandleFunc("/api/v1/events", func(w http.ResponseWriter, r *http.Request) {
		flusher, ok := w.(http.Flusher)
		if !ok {
			http.Error(w, "streaming unsupported", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")

		// Handshake event
		fmt.Fprintf(w, "data: {\"type\":\"connected\",\"time\":\"%s\"}\n\n", time.Now().UTC().Format(time.RFC3339))
		flusher.Flush()

		ch, unsubscribe := globalAuditLogger.Subscribe()
		defer unsubscribe()

		ctx := r.Context()
		for {
			select {
			case <-ctx.Done():
				return
			case entry, ok := <-ch:
				if !ok {
					return
				}
				data, err := json.Marshal(entry)
				if err == nil {
					fmt.Fprintf(w, "data: %s\n\n", data)
					flusher.Flush()
				}
			}
		}
	})

	// 4. Instant 1-Click Identity Kill-Switch
	mux.HandleFunc("/api/v1/revoke", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		if !checkAdminAuth(r, adminToken) {
			if globalAuditLogger != nil {
				globalAuditLogger.Log(AuditEntry{
					Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
					ClientIP:      r.RemoteAddr,
					Identity:      "unauthorized-admin",
					TargetBackend: "none",
					Method:        "CONTROL",
					Path:          r.URL.Path,
					StatusCode:    http.StatusUnauthorized,
					Decision:      "CONTROL_DENY",
					Reason:        "missing or invalid admin token",
					DurationUS:    10,
				})
			}
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			json.NewEncoder(w).Encode(map[string]string{
				"error": "unauthorized: invalid or missing admin token",
			})
			return
		}

		var payload struct {
			Identity string `json:"identity"`
			Action   string `json:"action"` // "revoke" or "unrevoke"
		}
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, `{"error": "invalid json payload"}`, http.StatusBadRequest)
			return
		}

		id := strings.TrimSpace(payload.Identity)
		if id == "" {
			http.Error(w, `{"error": "identity required"}`, http.StatusBadRequest)
			return
		}

		// Auto-expand short service names
		if !strings.HasPrefix(id, "spiffe://") {
			id = "spiffe://zetashield.local/ns/default/sa/" + id
		}

		action := strings.ToLower(strings.TrimSpace(payload.Action))
		if action != "revoke" && action != "unrevoke" {
			action = "revoke"
		}

		if action == "revoke" {
			dynamicRevoked.Store(id, true)
		} else {
			dynamicRevoked.Delete(id)
		}

		// Log control-plane administrative event in audit ledger
		globalAuditLogger.Log(AuditEntry{
			Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
			ClientIP:      r.RemoteAddr,
			Identity:      "control-plane-admin",
			TargetBackend: "none",
			Method:        "CONTROL",
			Path:          "/api/v1/revoke",
			StatusCode:    http.StatusOK,
			Decision:      strings.ToUpper(action) + "D",
			Reason:        fmt.Sprintf("kill-switch %sd %s", action, id),
			DurationUS:    10,
		})

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"status":   "ok",
			"identity": id,
			"action":   action,
		})
	})

	// 5. Dynamic Mode Switch (Enforce vs Learning)
	mux.HandleFunc("/api/v1/mode", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		if !checkAdminAuth(r, adminToken) {
			if globalAuditLogger != nil {
				globalAuditLogger.Log(AuditEntry{
					Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
					ClientIP:      r.RemoteAddr,
					Identity:      "unauthorized-admin",
					TargetBackend: "none",
					Method:        "CONTROL",
					Path:          r.URL.Path,
					StatusCode:    http.StatusUnauthorized,
					Decision:      "CONTROL_DENY",
					Reason:        "missing or invalid admin token",
					DurationUS:    10,
				})
			}
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			json.NewEncoder(w).Encode(map[string]string{
				"error": "unauthorized: invalid or missing admin token",
			})
			return
		}

		var payload struct {
			Mode string `json:"mode"`
		}
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, `{"error": "invalid json payload"}`, http.StatusBadRequest)
			return
		}

		mode := strings.ToLower(strings.TrimSpace(payload.Mode))
		if mode != "enforce" && mode != "learning" {
			http.Error(w, `{"error": "mode must be 'enforce' or 'learning'"}`, http.StatusBadRequest)
			return
		}

		setActiveMode(mode)

		// Record mode change event
		globalAuditLogger.Log(AuditEntry{
			Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
			ClientIP:      r.RemoteAddr,
			Identity:      "control-plane-admin",
			TargetBackend: "none",
			Method:        "CONTROL",
			Path:          "/api/v1/mode",
			StatusCode:    http.StatusOK,
			Decision:      "MODE_CHANGE",
			Reason:        fmt.Sprintf("gateway mode set to %s", mode),
			DurationUS:    10,
		})

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"status": "ok",
			"mode":   mode,
		})
	})

	// 6. Embedded SOC Telemetry Dashboard File Server
	fileServer := http.FileServer(http.Dir(dashboardDir))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/" || !strings.Contains(r.URL.Path, ".") {
			indexPath := filepath.Join(dashboardDir, "index.html")
			if _, err := os.Stat(indexPath); err == nil {
				http.ServeFile(w, r, indexPath)
				return
			}
		}
		fileServer.ServeHTTP(w, r)
	})

	server := &http.Server{
		Addr:    addr,
		Handler: enableCORS(mux),
	}

	go func() {
		fmt.Printf("  Control Plane API & SOC Dashboard listening on %s\n", addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("[control] server error: %v", err)
		}
	}()

	return server
}

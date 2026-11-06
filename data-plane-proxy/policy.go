package main

import (
	"fmt"
	"log"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"gopkg.in/yaml.v3"
)

// PolicyConfig defines the declarative rules, routes, and operational modes.
type PolicyConfig struct {
	Version           string            `yaml:"version"`
	Mode              string            `yaml:"mode"` // "enforce" (default) or "learning"
	DefaultRateLimit  float64           `yaml:"default_rate_limit"`
	DefaultBurst      float64           `yaml:"default_burst"`
	RevokedIdentities []string          `yaml:"revoked_identities"`
	Routes            map[string]string `yaml:"routes"`
	Rules             []PolicyRule      `yaml:"rules"`
}

// PolicyRule defines an authorization grant for a specific identity.
type PolicyRule struct {
	Identity   string   `yaml:"identity"`
	PathPrefix string   `yaml:"path_prefix"`
	Methods    []string `yaml:"methods"`
	RateLimit  float64  `yaml:"rate_limit,omitempty"`
	Burst      float64  `yaml:"burst,omitempty"`
}

// GatewaySnapshot holds an immutable, atomic snapshot of the active configuration.
type GatewaySnapshot struct {
	Policy     PolicyConfig
	Proxies    map[string]*httputil.ReverseProxy
	RevokedSet map[string]bool
}

var (
	// activeSnapshot provides lock-free, zero-downtime pointer swaps for policy reading.
	activeSnapshot atomic.Pointer[GatewaySnapshot]

	// dynamicRevoked enables real-time 1-click revocation from the Control Plane API.
	dynamicRevoked sync.Map

	// Legacy global state preserved for backward compatibility with existing unit tests.
	policy   PolicyConfig
	policyMu sync.RWMutex

	// activeMode dynamically tracks "enforce" vs "learning" (Shadow Mode).
	activeMode atomic.Value

	// discoveredRules maps "identity|method|prefix" -> PolicyRule observed during Learning Mode.
	discoveredRules sync.Map
)

func getActiveMode() string {
	v := activeMode.Load()
	if v == nil {
		return "enforce"
	}
	return v.(string)
}

func setActiveMode(m string) {
	if m != "learning" {
		m = "enforce"
	}
	activeMode.Store(m)
}

func extractPrefix(path string) string {
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) > 0 && parts[0] != "" {
		return "/" + parts[0] + "/"
	}
	return "/"
}

func recordDiscoveredRule(identity, method, path string) {
	prefix := extractPrefix(path)
	key := fmt.Sprintf("%s|%s", identity, prefix)
	if existing, ok := discoveredRules.Load(key); ok {
		rule := existing.(PolicyRule)
		methodFound := false
		for _, m := range rule.Methods {
			if m == method {
				methodFound = true
				break
			}
		}
		if !methodFound {
			rule.Methods = append(rule.Methods, method)
			discoveredRules.Store(key, rule)
		}
		return
	}
	discoveredRules.Store(key, PolicyRule{
		Identity:   identity,
		PathPrefix: prefix,
		Methods:    []string{method},
	})
}

func getDiscoveredRules() []PolicyRule {
	var rules []PolicyRule
	discoveredRules.Range(func(key, value any) bool {
		rules = append(rules, value.(PolicyRule))
		return true
	})
	return rules
}

// isSafePath validates against path traversal, backslashes, and null bytes.
func isSafePath(rawPath string) bool {
	if strings.Contains(rawPath, "..") || strings.Contains(rawPath, "\\") || strings.Contains(rawPath, "\x00") {
		return false
	}
	unescaped, err := url.PathUnescape(rawPath)
	if err != nil {
		return false
	}
	if strings.Contains(unescaped, "..") || strings.Contains(unescaped, "\\") || strings.Contains(unescaped, "\x00") {
		return false
	}
	return true
}

// matchPathPrefix checks segment-boundary matching (/orders matches /orders and /orders/list, but NOT /orders-secret).
func matchPathPrefix(reqPath, rulePrefix string) bool {
	if reqPath == rulePrefix {
		return true
	}
	if strings.HasSuffix(rulePrefix, "/") {
		return strings.HasPrefix(reqPath, rulePrefix)
	}
	if strings.HasPrefix(reqPath, rulePrefix) {
		if len(reqPath) > len(rulePrefix) && reqPath[len(rulePrefix)] == '/' {
			return true
		}
	}
	return false
}

// loadPolicy unmarshals YAML safely into an isolated struct before performing an atomic swap.
func loadPolicy(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("cannot read policy file %s: %w", path, err)
	}

	var candidate PolicyConfig
	if err := yaml.Unmarshal(data, &candidate); err != nil {
		return fmt.Errorf("yaml parse error (retaining existing active policy): %w", err)
	}

	// Normalize defaults
	if candidate.Mode == "" {
		candidate.Mode = "enforce"
	}
	if candidate.DefaultRateLimit <= 0 {
		candidate.DefaultRateLimit = 5000
	}
	if candidate.DefaultBurst <= 0 {
		candidate.DefaultBurst = 1000
	}

	revokedSet := make(map[string]bool)
	for _, id := range candidate.RevokedIdentities {
		revokedSet[strings.TrimSpace(id)] = true
	}

	// Pre-warm reverse proxies for all routes in candidate configuration
	proxies := make(map[string]*httputil.ReverseProxy)
	for prefix, target := range candidate.Routes {
		proxy, err := buildReverseProxy(target)
		if err != nil {
			return fmt.Errorf("failed to pre-warm proxy for route %s -> %s: %w", prefix, target, err)
		}
		proxies[prefix] = proxy
	}

	// Atomic snapshot swap
	snapshot := &GatewaySnapshot{
		Policy:     candidate,
		Proxies:    proxies,
		RevokedSet: revokedSet,
	}
	activeSnapshot.Store(snapshot)

	// Keep legacy policy variable in sync for test suite compatibility
	policyMu.Lock()
	policy = candidate
	policyMu.Unlock()

	return nil
}

// startPolicyWatcher polls file modtime and reloads safely in the background.
func startPolicyWatcher(path string) {
	info, err := os.Stat(path)
	if err != nil {
		return
	}
	lastMod := info.ModTime()

	go func() {
		ticker := time.NewTicker(1 * time.Second)
		defer ticker.Stop()
		for range ticker.C {
			fi, err := os.Stat(path)
			if err != nil {
				continue
			}
			if fi.ModTime().After(lastMod) {
				lastMod = fi.ModTime()
				if err := loadPolicy(path); err != nil {
					log.Printf("[policy] hot-reload rejected: %v", err)
				} else {
					fmt.Printf("[policy] hot-reloaded %s (%s)\n", path, time.Now().UTC().Format(time.RFC3339))
				}
			}
		}
	}()
}

// checkPolicy evaluates whether an identity is authorized for method + path.
func checkPolicy(identity, method, path string) (string, bool) {
	if !isSafePath(path) {
		return "", false
	}

	// Check dynamic revocation list (from Control Plane API)
	if _, isRevoked := dynamicRevoked.Load(identity); isRevoked {
		return "revoked", false
	}

	var rules []PolicyRule
	var revokedSet map[string]bool

	snap := activeSnapshot.Load()
	if snap != nil {
		rules = snap.Policy.Rules
		revokedSet = snap.RevokedSet
		if revokedSet[identity] {
			return "revoked", false
		}
	} else {
		// Fallback for tests modifying global `policy` directly
		policyMu.RLock()
		rules = policy.Rules
		policyMu.RUnlock()
	}

	shortName := identity
	if idx := strings.LastIndex(identity, "/"); idx >= 0 {
		shortName = identity[idx+1:]
	}

	for _, rule := range rules {
		idMatch := rule.Identity == identity || rule.Identity == shortName
		if !idMatch {
			continue
		}
		if !matchPathPrefix(path, rule.PathPrefix) {
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

// routeFor performs longest-prefix matching to locate the target backend URL.
func routeFor(path string) (string, bool) {
	if !isSafePath(path) {
		return "", false
	}

	var routes map[string]string
	snap := activeSnapshot.Load()
	if snap != nil {
		routes = snap.Policy.Routes
	} else {
		policyMu.RLock()
		routes = policy.Routes
		policyMu.RUnlock()
	}

	bestPrefix := ""
	bestTarget := ""
	for prefix, target := range routes {
		if matchPathPrefix(path, prefix) && len(prefix) > len(bestPrefix) {
			bestPrefix = prefix
			bestTarget = target
		}
	}
	if bestTarget != "" {
		return bestTarget, true
	}
	return "", false
}

// getProxyForRoute retrieves the pre-warmed ReverseProxy instance for a given path.
func getProxyForRoute(path string) (*httputil.ReverseProxy, string, bool) {
	if !isSafePath(path) {
		return nil, "", false
	}

	snap := activeSnapshot.Load()
	if snap == nil {
		target, ok := routeFor(path)
		if !ok {
			return nil, "", false
		}
		p, err := buildReverseProxy(target)
		if err != nil {
			return nil, "", false
		}
		return p, target, true
	}

	bestPrefix := ""
	var bestProxy *httputil.ReverseProxy
	bestTarget := ""

	for prefix, proxy := range snap.Proxies {
		if matchPathPrefix(path, prefix) && len(prefix) > len(bestPrefix) {
			bestPrefix = prefix
			bestProxy = proxy
			bestTarget = snap.Policy.Routes[prefix]
		}
	}

	if bestProxy != nil {
		return bestProxy, bestTarget, true
	}

	return nil, "", false
}

package main

import "testing"

func TestPolicyAllows(t *testing.T) {
	tests := []struct {
		name     string
		identity string
		method   string
		path     string
		want     bool
	}{
		// Explicit ALLOW rules
		{"allowed: orders GET", "frontend-proxy", "GET", "/api/v1/orders", true},
		{"allowed: cart GET", "frontend-proxy", "GET", "/api/v1/cart", true},
		{"allowed: cart POST", "frontend-proxy", "POST", "/api/v1/cart", true},

		// Valid identity, wrong method → deny
		{"wrong method: orders POST", "frontend-proxy", "POST", "/api/v1/orders", false},
		{"wrong method: cart DELETE", "frontend-proxy", "DELETE", "/api/v1/cart", false},

		// Valid identity, forbidden path → deny (demo Test 3)
		{"forbidden path: POST /admin/delete", "frontend-proxy", "POST", "/admin/delete", false},

		// Wrong identity → deny (demo Test 4)
		{"wrong identity: kitchen-service", "kitchen-service", "GET", "/api/v1/orders", false},
		{"empty identity", "", "GET", "/api/v1/orders", false},

		// Deny-by-default
		{"unknown caller", "attacker-service", "GET", "/api/v1/orders", false},
		{"admin path probe", "frontend-proxy", "GET", "/admin", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := policyAllows(tt.identity, tt.method, tt.path)
			if got != tt.want {
				t.Errorf("policyAllows(%q, %q, %q) = %v, want %v",
					tt.identity, tt.method, tt.path, got, tt.want)
			}
		})
	}
}

func TestPathMatches(t *testing.T) {
	tests := []struct {
		name    string
		pattern string
		path    string
		want    bool
	}{
		{"exact match", "/api/v1/orders", "/api/v1/orders", true},
		{"exact mismatch", "/api/v1/orders", "/api/v1/cart", false},
		{"prefix wildcard match", "/api/v1/*", "/api/v1/orders", true},
		{"prefix wildcard miss", "/api/v1/*", "/admin/delete", false},
		{"prefix shorter than pattern", "/api/v1/orders", "/api/v1/order", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := pathMatches(tt.pattern, tt.path)
			if got != tt.want {
				t.Errorf("pathMatches(%q, %q) = %v, want %v",
					tt.pattern, tt.path, got, tt.want)
			}
		})
	}
}

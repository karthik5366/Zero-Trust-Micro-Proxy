package main

import "testing"

func TestCheckPolicy(t *testing.T) {
	policy = PolicyConfig{
		Rules: []PolicyRule{
			{Identity: "spiffe://zetashield.local/ns/default/sa/frontend-service", PathPrefix: "/orders/", Methods: []string{"GET"}},
			{Identity: "spiffe://zetashield.local/ns/default/sa/frontend-service", PathPrefix: "/payments/", Methods: []string{"GET", "POST"}},
			{Identity: "spiffe://zetashield.local/ns/default/sa/frontend-service", PathPrefix: "/inventory/", Methods: []string{"GET"}}, // NEW
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
		{"frontend reads inventory", "spiffe://zetashield.local/ns/default/sa/frontend-service", "GET", "/inventory/status", true}, // NEW
		{"orders reads own domain", "spiffe://zetashield.local/ns/default/sa/orders-service", "GET", "/orders/list", true},
		{"payments reads own domain", "spiffe://zetashield.local/ns/default/sa/payments-service", "GET", "/payments/balance", true},
		{"orders blocked from payments", "spiffe://zetashield.local/ns/default/sa/orders-service", "GET", "/payments/balance", false},
		{"payments blocked from orders", "spiffe://zetashield.local/ns/default/sa/payments-service", "GET", "/orders/list", false},
		{"orders blocked from inventory", "spiffe://zetashield.local/ns/default/sa/orders-service", "GET", "/inventory/status", false}, // NEW
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
	policy = PolicyConfig{
		Routes: map[string]string{
			"/orders/":    "http://127.0.0.1:9091",
			"/payments/":  "http://127.0.0.1:9092",
			"/inventory/": "http://127.0.0.1:9099", // NEW
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
		{"inventory route", "/inventory/status", "http://127.0.0.1:9099", true}, // NEW
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

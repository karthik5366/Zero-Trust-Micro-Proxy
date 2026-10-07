// cmd/loadtest/main.go — ZetaShield V1.0 latency benchmark
//
// Measures the cost of zero-trust enforcement:
//
//	direct-to-backend latency  vs  through-gateway latency
package main

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"os"
	"sort"
	"time"
)

const requests = 500

func newMTLSClient() *http.Client {
	caPEM, err := os.ReadFile("../certs/ca.pem")
	if err != nil {
		panic("cannot read CA cert (run from data-plane-proxy/): " + err.Error())
	}
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(caPEM)

	cert, err := tls.LoadX509KeyPair("../certs/frontend-service.pem", "../certs/frontend-service-key.pem")
	if err != nil {
		panic("cannot load client cert: " + err.Error())
	}

	return &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				RootCAs:      pool,
				Certificates: []tls.Certificate{cert},
			},
		},
	}
}

func main() {
	direct := &http.Client{}
	gateway := newMTLSClient()

	fmt.Printf("ZetaShield V1.0 — Latency Benchmark (%d requests per mode)\n", requests)
	fmt.Println("Backends + gateway must be running.\n")

	directLats := measure(direct, "http://127.0.0.1:9091/orders/list")
	gwLats := measure(gateway, "https://127.0.0.1:8443/orders/list")

	dMean, dP50, dP99 := stats(directLats)
	gMean, gP50, gP99 := stats(gwLats)

	fmt.Println("\n──────────────────────────────────────────────────────────")
	fmt.Println("MODE                         MEAN         P50          P99")
	fmt.Printf("Direct to backend            %-12s %-12s %s\n", dMean, dP50, dP99)
	fmt.Printf("Through Zero-Trust gateway   %-12s %-12s %s\n", gMean, gP50, gP99)
	fmt.Println("──────────────────────────────────────────────────────────")
	fmt.Printf("\nZero-Trust enforcement overhead (median): %s\n", gP50-dP50)
	fmt.Println("Overhead includes: mTLS session + SAN identity extraction")
	fmt.Println("+ policy evaluation + routing + audit log write.")
}

func measure(c *http.Client, url string) []time.Duration {
	lats := make([]time.Duration, 0, requests)
	for i := 0; i < requests; i++ {
		start := time.Now()
		resp, err := c.Get(url)
		if err != nil {
			fmt.Println("\nrequest failed:", err)
			os.Exit(1)
		}
		resp.Body.Close()
		lats = append(lats, time.Since(start))
	}
	return lats
}

func stats(l []time.Duration) (mean, p50, p99 time.Duration) {
	sort.Slice(l, func(i, j int) bool { return l[i] < l[j] })
	var sum time.Duration
	for _, d := range l {
		sum += d
	}
	return sum / time.Duration(len(l)), l[len(l)/2], l[len(l)*99/100]
}

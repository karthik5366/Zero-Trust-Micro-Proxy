package main

import (
	"math"
	"sync"
	"time"
)

// TokenBucket implements a standard-library thread-safe token bucket rate limiter.
type TokenBucket struct {
	capacity   float64
	tokens     float64
	refillRate float64 // Tokens per second
	lastRefill time.Time
	mu         sync.Mutex
}

// newTokenBucket initializes a new token bucket.
func newTokenBucket(rate, burst float64) *TokenBucket {
	if burst <= 0 {
		burst = 10
	}
	if rate <= 0 {
		rate = 10
	}
	return &TokenBucket{
		capacity:   burst,
		tokens:     burst,
		refillRate: rate,
		lastRefill: time.Now(),
	}
}

// Allow attempts to consume 1 token, returning true if allowed and false if rate-limited.
func (tb *TokenBucket) Allow() bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(tb.lastRefill).Seconds()
	tb.lastRefill = now

	// Refill tokens based on elapsed time
	tb.tokens = math.Min(tb.capacity, tb.tokens+(elapsed*tb.refillRate))
	if tb.tokens >= 1.0 {
		tb.tokens -= 1.0
		return true
	}
	return false
}

var (
	// identityLimiters maps SPIFFE identity -> *TokenBucket
	identityLimiters sync.Map

	// handshakeLimiters maps client IP -> *TokenBucket
	handshakeLimiters sync.Map
)

// CheckIdentityRate checks if a request from an identity is within allowed L7 limits.
func CheckIdentityRate(identity string, rate, burst float64) bool {
	val, ok := identityLimiters.Load(identity)
	if !ok {
		limiter := newTokenBucket(rate, burst)
		actual, _ := identityLimiters.LoadOrStore(identity, limiter)
		val = actual
	}
	return val.(*TokenBucket).Allow()
}

// CheckHandshakeRate protects against TLS handshake floods without banning IPs.
// Default: 30 handshakes/sec with burst of 60 per IP.
func CheckHandshakeRate(clientIP string) bool {
	val, ok := handshakeLimiters.Load(clientIP)
	if !ok {
		limiter := newTokenBucket(30, 60)
		actual, _ := handshakeLimiters.LoadOrStore(clientIP, limiter)
		val = actual
	}
	return val.(*TokenBucket).Allow()
}

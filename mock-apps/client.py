#!/usr/bin/env python3
"""
client.py — Demo test client (simulates the 'frontend' microservice)

Runs the 4-test Review-1 sequence against the proxy on :8080.
Watch Terminal 2 (the proxy) to see [ALLOW]/[DENY] decisions live.
"""
import urllib.request
import urllib.error

PROXY = "http://127.0.0.1:8080"


def send(label, method, path, identity=None):
    req = urllib.request.Request(PROXY + path, method=method)
    if identity:
        req.add_header("X-Service-Identity", identity)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            result = f"HTTP {r.status}"
            body = r.read().decode()[:80]
    except urllib.error.HTTPError as e:
        result, body = f"HTTP {e.code} {e.reason}", ""
    except Exception as e:
        result, body = f"CONNECTION FAILED ({e})", ""
    print(f"{label}\n  -> {result}" + (f"\n  -> {body}" if body else "") + "\n")


if __name__ == "__main__":
    print("=" * 62)
    print("  Zero-Trust Proxy V0.1 — Review 1 Demo Sequence")
    print("=" * 62)

    send("TEST 1  Authorized request", "GET", "/api/v1/orders",
         identity="frontend-proxy")
    send("TEST 2  No identity (unknown caller)", "GET", "/api/v1/orders")
    send("TEST 3  Valid identity, forbidden action", "POST", "/admin/delete",
         identity="frontend-proxy")
    send("TEST 4  Wrong identity (kitchen-service)", "GET", "/api/v1/orders",
         identity="kitchen-service")
#!/usr/bin/env python3
"""
client.py — V1.0 demo client (simulates services with real certificates)
Runs the 5-test Review 2 demonstration sequence.
"""
import ssl
import urllib.request
import urllib.error

GATEWAY = "https://127.0.0.1:8443"


def make_request(label, method, path, cert_file=None, key_file=None):
    """Send a request to the gateway, optionally with a client certificate."""
    ctx = ssl.create_default_context(cafile="../certs/ca.pem")

    if cert_file and key_file:
        ctx.load_cert_chain(cert_file, key_file)

    req = urllib.request.Request(GATEWAY + path, method=method)

    try:
        handler = urllib.request.HTTPSHandler(context=ctx)
        opener = urllib.request.build_opener(handler)
        with opener.open(req, timeout=5) as r:
            result = f"HTTP {r.status}"
            body = r.read().decode()[:80]
    except urllib.error.HTTPError as e:
        result, body = f"HTTP {e.code} {e.reason}", ""
    except ssl.SSLError as e:
        result, body = f"TLS REJECTED ({e.reason})", ""
    except Exception as e:
        result, body = f"FAILED ({type(e).__name__}: {e})", ""

    print(f"{label}")
    print(f"  → {result}")
    if body:
        print(f"  → {body}")
    print()


if __name__ == "__main__":
    print("=" * 65)
    print("  ZetaShield V1.0 — Review 2 Demo (5-Test Sequence)")
    print("=" * 65)
    print()

    # TEST 1: Authorized — frontend-service reads orders
    make_request(
        "TEST 1: frontend-service → GET /orders/ (authorized)",
        "GET", "/orders/list",
        "../certs/frontend-service.pem", "../certs/frontend-service-key.pem"
    )

    # TEST 2: No certificate — rejected at TLS handshake
    make_request(
        "TEST 2: No certificate (unknown caller)",
        "GET", "/orders/list"
    )

    # TEST 3: Valid identity, no rule for this path — denied
    make_request(
        "TEST 3: frontend-service → GET /admin/ (no rule — denied)",
        "GET", "/admin/delete",
        "../certs/frontend-service.pem", "../certs/frontend-service-key.pem"
    )

    # TEST 4: MICRO-SEGMENTATION — orders-service tries to access payments
    make_request(
        "TEST 4: orders-service → GET /payments/ (SEGMENTATION VIOLATION)",
        "GET", "/payments/balance",
        "../certs/orders-service.pem", "../certs/orders-service-key.pem"
    )

    # TEST 5: Payments-service reads its own domain (allowed)
    make_request(
        "TEST 5: payments-service → GET /payments/ (authorized)",
        "GET", "/payments/balance",
        "../certs/payments-service.pem", "../certs/payments-service-key.pem"
    )

    print("=" * 65)
    print("  Expected: 200, TLS_REJECT, 403, 403, 200")
    print("=" * 65)
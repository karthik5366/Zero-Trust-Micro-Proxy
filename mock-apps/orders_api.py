#!/usr/bin/env python3
"""
orders_api.py — Protected backend microservice (V0.1)

SECURITY NOTE (a real design decision, not a demo hack):
Binds EXCLUSIVELY to 127.0.0.1 — no network exposure at all.
No other machine can reach port 9090. The ONLY path to this
service is through the local Go proxy on :8080.
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler


class OrdersHandler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/v1/orders":
            self._send(200, {
                "service": "orders-api",
                "orders": [
                    {"id": 1, "item": "Laptop", "qty": 1},
                    {"id": 2, "item": "Phone", "qty": 2},
                    {"id": 3, "item": "Monitor", "qty": 1},
                ],
            })
        elif self.path == "/api/v1/cart":
            self._send(200, {"service": "orders-api",
                             "cart": {"items": 3, "total": 154999}})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/v1/cart":
            self._send(200, {"service": "orders-api", "cart": "item added"})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"[orders-api] {fmt % args}")


if __name__ == "__main__":
    print("[orders-api] listening on 127.0.0.1:9090  (LOCALHOST ONLY)")
    print("[orders-api] no other machine can reach this port — by design")
    HTTPServer(("127.0.0.1", 9090), OrdersHandler).serve_forever()
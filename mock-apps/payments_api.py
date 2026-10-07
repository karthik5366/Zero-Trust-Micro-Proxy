#!/usr/bin/env python3
"""payments-api — protected backend service (V1.0)
Binds EXCLUSIVELY to 127.0.0.1:9092 — unreachable from the network."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/payments/"):
            self._send(200, {"service": "payments-api", "balance": 154999})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/payments/"):
            self._send(200, {"service": "payments-api", "status": "payment processed"})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"[payments-api] {fmt % args}")


if __name__ == "__main__":
    print("[payments-api] listening on 127.0.0.1:9092 (LOCALHOST ONLY)")
    HTTPServer(("127.0.0.1", 9092), Handler).serve_forever()
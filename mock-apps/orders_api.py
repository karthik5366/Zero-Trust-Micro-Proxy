#!/usr/bin/env python3
"""orders-api — protected backend service (V1.0)
Binds EXCLUSIVELY to 127.0.0.1:9091 — unreachable from the network.
The only path to this service is through the Zero-Trust gateway."""
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
        if self.path.startswith("/orders/"):
            self._send(200, {"service": "orders-api", "data": [{"id": 1, "item": "Laptop"}]})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"[orders-api] {fmt % args}")


if __name__ == "__main__":
    print("[orders-api] listening on 127.0.0.1:9091 (LOCALHOST ONLY)")
    HTTPServer(("127.0.0.1", 9091), Handler).serve_forever()
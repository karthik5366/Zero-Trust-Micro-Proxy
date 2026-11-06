#!/usr/bin/env python3
"""orders-api — protected backend service (V2.1 Hardened)
Binds to 127.0.0.1:9091 by default, or configurable via BIND_HOST and PORT.
Enforces Hop-2 HMAC signature verification when ZS_HMAC_SECRET is set."""
import hashlib
import hmac
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    def _verify_hmac(self):
        secret = os.environ.get("ZS_HMAC_SECRET", "")
        if not secret:
            return True  # Opt-in: allows direct baseline tests if secret is unset
        identity = self.headers.get("X-ZetaShield-Identity", "")
        signature = self.headers.get("X-ZetaShield-Signature", "")
        if not identity or not signature:
            return False
        payload = f"{self.command}|{self.path}|{identity}"
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._verify_hmac():
            self._send(401, {"error": "unauthorized: invalid or missing gateway signature"})
            return
        if self.path.startswith("/orders/"):
            self._send(200, {"service": "orders-api", "data": [{"id": 1, "item": "Laptop"}]})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"[orders-api] {fmt % args}")


if __name__ == "__main__":
    host = os.environ.get("BIND_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 9091))
    print(f"[orders-api] listening on {host}:{port} (HMAC enforced: {bool(os.environ.get('ZS_HMAC_SECRET'))})")
    HTTPServer((host, port), Handler).serve_forever()

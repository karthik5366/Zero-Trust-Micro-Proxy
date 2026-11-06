#!/usr/bin/env python3
"""redteam_sim.py — Continuous Traffic & Adversarial Simulator
Fires a randomized mix of legitimate Zero-Trust calls and red-team attacks
against the ZetaShield Gateway to demonstrate live micro-segmentation,
threat containment, and real-time SOC dashboard telemetry.

Zero external dependencies (Python 3.8+ standard library only)."""

import argparse
import os
import random
import ssl
import sys
import time
import urllib.error
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_GATEWAY = os.environ.get("ZS_GATEWAY_URL", "https://127.0.0.1:8443")
DEFAULT_CERTS = os.environ.get("ZS_CERTS_DIR", "")

# ANSI Color codes for clean terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def resolve_certs_dir(user_dir):
    candidates = [
        user_dir,
        os.path.join(os.getcwd(), "certs"),
        os.path.join(os.getcwd(), "../certs"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../certs"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs"),
    ]
    for c in candidates:
        if c and os.path.isfile(os.path.join(c, "ca.pem")):
            return os.path.abspath(c)
    print(f"{RED}[ERROR] Could not locate certs/ directory containing ca.pem.{RESET}")
    print("Please specify --certs-dir /path/to/certs")
    sys.exit(1)


def send_request(gateway_url, certs_dir, name, method, path, cert_name=None, body=None, timeout=3):
    url = f"{gateway_url}{path}"
    ca_file = os.path.join(certs_dir, "ca.pem")

    try:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_file)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_REQUIRED

        if cert_name:
            cert_file = os.path.join(certs_dir, f"{cert_name}.pem")
            key_file = os.path.join(certs_dir, f"{cert_name}-key.pem")
            if not os.path.isfile(cert_file) or not os.path.isfile(key_file):
                return "CERT_MISSING", 0

            ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)

        data = body.encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, method=method)

        t0 = time.perf_counter()
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            dur_ms = (time.perf_counter() - t0) * 1000
            return "ALLOW", resp.status, dur_ms

    except (ssl.SSLError, ConnectionResetError) as e:
        return "TLS_REJECT", 495, 0.5
    except urllib.error.HTTPError as e:
        code = e.code
        decision = "DENY"
        if code == 429:
            decision = "RATE_LIMITED"
        elif code == 400:
            decision = "PATH_TRAVERSAL"
        elif code == 503:
            decision = "FAIL_CLOSED"
        return decision, code, 1.0
    except urllib.error.URLError as e:
        if "Connection refused" in str(e):
            return "GATEWAY_DOWN", 0, 0
        return "ERROR", 0, 0
    except Exception as e:
        return "ERROR", 0, 0


def run_scenario(gateway_url, certs_dir, scenario_id):
    if scenario_id == "BENIGN_FRONTEND_ORDERS":
        dec, status, dur = send_request(
            gateway_url, certs_dir, "Legitimate Orders Query",
            "GET", "/orders/list", cert_name="frontend-service"
        )
        return "Legitimate frontend -> orders", dec, status, dur

    elif scenario_id == "BENIGN_PAYMENTS_BALANCE":
        dec, status, dur = send_request(
            gateway_url, certs_dir, "Legitimate Payments Query",
            "GET", "/payments/balance", cert_name="payments-service"
        )
        return "Legitimate payments -> balance", dec, status, dur

    elif scenario_id == "LATERAL_MOVEMENT":
        dec, status, dur = send_request(
            gateway_url, certs_dir, "Lateral Movement Attempt",
            "GET", "/payments/balance", cert_name="orders-service"
        )
        return "Lateral Movement (orders -> payments)", dec, status, dur

    elif scenario_id == "UNAUTHORIZED_ADMIN":
        dec, status, dur = send_request(
            gateway_url, certs_dir, "Unauthorized Admin Access",
            "GET", "/admin/delete", cert_name="frontend-service"
        )
        return "Unauthorized Path (frontend -> /admin)", dec, status, dur

    elif scenario_id == "ANONYMOUS_HANDSHAKE":
        dec, status, dur = send_request(
            gateway_url, certs_dir, "Anonymous Attacker",
            "GET", "/orders/list", cert_name=None
        )
        return "Anonymous Intruder (No TLS Cert)", dec, status, dur

    elif scenario_id == "FORGED_CERTIFICATE":
        dec, status, dur = send_request(
            gateway_url, certs_dir, "Forged Cert Attacker",
            "GET", "/orders/list", cert_name="attacker"
        )
        return "Forged Cert (Untrusted Attacker CA)", dec, status, dur

    elif scenario_id == "PATH_TRAVERSAL":
        dec, status, dur = send_request(
            gateway_url, certs_dir, "Directory Traversal Attack",
            "GET", "/orders/../secret", cert_name="frontend-service"
        )
        return "Directory Traversal (/orders/../secret)", dec, status, dur

    elif scenario_id == "BURST_BURST":
        # Rapid burst
        for _ in range(5):
            send_request(
                gateway_url, certs_dir, "Rate Limit Burst",
                "GET", "/orders/list", cert_name="frontend-service"
            )
        dec, status, dur = send_request(
            gateway_url, certs_dir, "Rate Limit Burst",
            "GET", "/orders/list", cert_name="frontend-service"
        )
        return "Traffic Burst (Rate-Limit Stress)", dec, status, dur

    return "Unknown", "UNKNOWN", 0, 0


def main():
    parser = argparse.ArgumentParser(description="ZetaShield Continuous Red-Team & Traffic Simulator")
    parser.add_argument("--count", type=int, default=20, help="Number of simulated requests to send (default: 20)")
    parser.add_argument("--continuous", action="store_true", help="Run indefinitely until stopped with Ctrl+C")
    parser.add_argument("--interval", type=float, default=0.5, help="Delay between requests in seconds (default: 0.5s)")
    parser.add_argument("--gateway-url", default=DEFAULT_GATEWAY, help=f"Gateway URL (default: {DEFAULT_GATEWAY})")
    parser.add_argument("--certs-dir", default=DEFAULT_CERTS, help="Path to certs directory")
    parser.add_argument("--mode", choices=["all", "benign", "attack"], default="all", help="Traffic distribution mode")

    args = parser.parse_args()
    certs_dir = resolve_certs_dir(args.certs_dir)

    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║     ZetaShield V2.1 — Continuous Red-Team & Telemetry Simulator          ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"  Target Gateway : {BOLD}{args.gateway_url}{RESET}")
    print(f"  Certificates   : {certs_dir}")
    print(f"  Interval       : {args.interval}s")
    print(f"  Mode           : {args.mode.upper()}")
    print(f"  Continuous     : {args.continuous}\n")

    scenario_pool = []
    if args.mode in ("all", "benign"):
        scenario_pool.extend([
            ("BENIGN_FRONTEND_ORDERS", 40),
            ("BENIGN_PAYMENTS_BALANCE", 25),
        ])
    if args.mode in ("all", "attack"):
        scenario_pool.extend([
            ("LATERAL_MOVEMENT", 10),
            ("UNAUTHORIZED_ADMIN", 10),
            ("ANONYMOUS_HANDSHAKE", 10),
            ("FORGED_CERTIFICATE", 10),
            ("PATH_TRAVERSAL", 5),
        ])

    scenarios = [s[0] for s in scenario_pool]
    weights = [s[1] for s in scenario_pool]

    total_sent = 0
    total_allowed = 0
    total_blocked = 0

    print(f"{'#':<5} | {'SCENARIO':<38} | {'OUTCOME':<14} | {'HTTP':<5} | {'LATENCY'}")
    print("-" * 75)

    try:
        while True:
            chosen = random.choices(scenarios, weights=weights, k=1)[0]
            name, decision, status, dur = run_scenario(args.gateway_url, certs_dir, chosen)

            total_sent += 1
            if decision == "ALLOW":
                total_allowed += 1
                outcome_str = f"{GREEN}{BOLD}ALLOW{RESET}"
            elif decision in ("DENY", "TLS_REJECT", "PATH_TRAVERSAL"):
                total_blocked += 1
                outcome_str = f"{RED}{BOLD}{decision}{RESET}"
            else:
                outcome_str = f"{YELLOW}{BOLD}{decision}{RESET}"

            lat_str = f"{dur:.2f}ms" if dur > 0 else "-"
            print(f"[{total_sent:>3}] | {name:<38} | {outcome_str:<23} | {status:<5} | {lat_str}")

            if not args.continuous and total_sent >= args.count:
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}[Simulator interrupted by user]{RESET}")

    print("\n" + "=" * 75)
    print(f"{BOLD}SIMULATION COMPLETE:{RESET} Total Requests: {total_sent} | Allowed: {GREEN}{total_allowed}{RESET} | Blocked: {RED}{total_blocked}{RESET}")
    print("=" * 75)


if __name__ == "__main__":
    main()

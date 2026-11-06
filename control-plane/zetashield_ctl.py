#!/usr/bin/env python3
"""zetashield_ctl.py — ZetaShield Enterprise Control Plane CLI
Operator tool for dynamic fleet management, 1-click revocation kill-switches,
live learning mode toggles, and cryptographic ledger attestation.

Zero external dependencies (Python standard library only)."""

import json
import os
import sys
import urllib.error
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CONTROL_URL = os.environ.get("ZS_CONTROL_URL", "http://127.0.0.1:8444")
ADMIN_TOKEN = os.environ.get("ZS_ADMIN_TOKEN", "zetashield-admin-secret-2026")


def _req(path, method="GET", data=None):
    url = f"{CONTROL_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "X-ZetaShield-Admin-Token": ADMIN_TOKEN,
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to connect to Control Plane at {url}: {e}")
        print("Ensure the ZetaShield Gateway is running with port 8444 exposed.")
        sys.exit(1)


def cmd_status():
    data = _req("/api/v1/status")
    ledger = data.get("ledger", {})
    metrics = data.get("metrics", {})
    mode = data.get("mode", "enforce").upper()

    print("╔════════════════════════════════════════════════════════════════╗")
    print(f"║  ZetaShield {data.get('version', 'V2.1')} Control Plane — Cluster Status          ║")
    print("╠════════════════════════════════════════════════════════════════╣")
    print(f"║  Active Mode : {mode:<47}║")
    print(f"║  Uptime      : {data.get('uptime_sec', 0):<5} seconds{' ' * 40}║")
    
    intact = ledger.get("intact", False)
    badge = "✅ CRYPTOGRAPHICALLY INTACT" if intact else "❌ TAMPER DETECTED"
    print(f"║  Audit Ledger: {badge:<47}║")
    print(f"║  Blocks Count: {ledger.get('verified_records', 0):<47}║")
    latest_hash = ledger.get("latest_hash", "0000...")
    print(f"║  Latest Hash : {latest_hash[:45]}... ║")
    print("╠════════════════════════════════════════════════════════════════╣")
    print(f"║  METRICS     : Total: {metrics.get('total', 0)} | Allow: {metrics.get('allow', 0)} | Blocked: {metrics.get('deny', 0) + metrics.get('tls_reject', 0)} | Error: {metrics.get('error', 0)} ║")
    print(f"║                Shadow: {metrics.get('shadow_deny', 0)} | Handshake Drops: {metrics.get('tls_reject', 0)}                   ║")
    print("╚════════════════════════════════════════════════════════════════╝")

    revoked = data.get("revoked_identities", [])
    print(f"\n[Active Revocations (Kill-Switch)]: {len(revoked)} identities revoked")
    for r in revoked:
        print(f"  ❌ {r}")

    routes = data.get("routes", {})
    print(f"\n[Active Routes]: {len(routes)} upstream targets")
    for prefix, target in routes.items():
        print(f"  • {prefix:<15} -> {target}")

    discovered = data.get("discovered_rules", [])
    if discovered:
        print(f"\n[Policy Discovery]: {len(discovered)} unmapped flows observed in Learning Mode")
        print("Run 'python control-plane/zetashield_ctl.py discover' to see candidate YAML rules.")


def cmd_revoke(identity):
    data = _req("/api/v1/revoke", method="POST", data={"identity": identity, "action": "revoke"})
    print(f"🚨 [KILL-SWITCH ACTIVE] Identity revoked immediately: {data.get('identity')}")
    print("All requests presenting this SPIFFE certificate will be dropped with 403 Forbidden.")


def cmd_unrevoke(identity):
    data = _req("/api/v1/revoke", method="POST", data={"identity": identity, "action": "unrevoke"})
    print(f"✅ [ACCESS RESTORED] Revocation cleared for: {data.get('identity')}")


def cmd_mode(mode_val):
    mode_val = mode_val.lower().strip()
    if mode_val not in ("enforce", "learning"):
        print("Usage: python zetashield_ctl.py mode <enforce|learning>")
        sys.exit(1)
    data = _req("/api/v1/mode", method="POST", data={"mode": mode_val})
    print(f"⚙️ [MODE SWITCHED] Gateway enforcement mode is now: {data.get('mode').upper()}")


def cmd_discover():
    data = _req("/api/v1/status")
    yaml_snippet = data.get("discovered_yaml", "").strip()
    discovered = data.get("discovered_rules", [])
    if not discovered:
        print("No new unmapped flows observed. (Switch to 'learning' mode and run traffic to observe flows).")
        return
    print("=" * 60)
    print(f"ZetaShield Auto-Discovered Policy Rules ({len(discovered)} flows observed):")
    print("=" * 60)
    print(yaml_snippet)
    print("=" * 60)
    print("Append these rules to policy.yaml and switch back to 'enforce' mode.")


def cmd_verify():
    data = _req("/api/v1/status")
    ledger = data.get("ledger", {})
    intact = ledger.get("intact", False)
    if intact:
        print(f"✅ [OK] Verified {ledger.get('verified_records', 0)} tamper-evident audit records.")
        print(f"   Latest block hash: {ledger.get('latest_hash')}")
        print("   Cryptographic SHA-256 chain is 100% intact.")
    else:
        print(f"❌ [TAMPER DETECTED] Ledger verification failed: {ledger.get('error_msg')}")
        sys.exit(1)


def cmd_rotate_cert(service, days=30):
    print(f"🔄 [CERT ROTATION] Initiating zero-downtime rotation for service: '{service}' (validity: {days} days)...")
    
    candidates = [
        os.path.join(os.getcwd(), "certs"),
        os.path.join(os.getcwd(), "../certs"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../certs"),
    ]
    certs_dir = None
    for c in candidates:
        if os.path.isfile(os.path.join(c, "issue_cert.sh")):
            certs_dir = os.path.abspath(c)
            break

    if not certs_dir:
        print("[ERROR] Could not find certs/ directory containing issue_cert.sh")
        sys.exit(1)

    import subprocess
    cmd = ["bash", "./issue_cert.sh", service, str(days)]
    
    res = subprocess.run(cmd, cwd=certs_dir, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] Certificate rotation failed:\n{res.stderr}")
        sys.exit(1)

    for line in res.stdout.strip().splitlines():
        print(f"  {line}")

    print(f"✅ [SUCCESS] New X.509 certificate and private key written to disk for '{service}'.")
    print("   The ZetaShield Gateway cert-watcher detects modified timestamps and hot-swaps atomically.")


def main():
    if len(sys.argv) < 2:
        print("ZetaShield Enterprise Control Plane CLI")
        print("\nCommands:")
        print("  status                   Show cluster health, mode, metrics, and ledger state")
        print("  revoke <identity>        Instantly revoke access for a service identity")
        print("  unrevoke <identity>      Restore access for a revoked service identity")
        print("  mode <enforce|learning>  Toggle dynamic enforcement vs shadow learning mode")
        print("  discover                 Show candidate YAML rules from learning mode")
        print("  verify                   Cryptographically verify SHA-256 ledger integrity")
        print("  rotate-cert <service>    Rotate X.509 certificate on disk for zero-downtime reload")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "status":
        cmd_status()
    elif cmd == "revoke":
        if len(sys.argv) < 3:
            print("Usage: python zetashield_ctl.py revoke <service-name|spiffe-uri>")
            sys.exit(1)
        cmd_revoke(sys.argv[2])
    elif cmd == "unrevoke":
        if len(sys.argv) < 3:
            print("Usage: python zetashield_ctl.py unrevoke <service-name|spiffe-uri>")
            sys.exit(1)
        cmd_unrevoke(sys.argv[2])
    elif cmd == "mode":
        if len(sys.argv) < 3:
            print("Usage: python zetashield_ctl.py mode <enforce|learning>")
            sys.exit(1)
        cmd_mode(sys.argv[2])
    elif cmd == "discover":
        cmd_discover()
    elif cmd == "verify":
        cmd_verify()
    elif cmd in ("rotate-cert", "rotate_cert"):
        if len(sys.argv) < 3:
            print("Usage: python zetashield_ctl.py rotate-cert <service-name> [validity-days]")
            sys.exit(1)
        service = sys.argv[2]
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        cmd_rotate_cert(service, days)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()

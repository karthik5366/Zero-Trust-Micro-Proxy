# ZetaShield Control Plane & Fleet Management

The **ZetaShield Control Plane** is the administrative and operational backbone for the Zero-Trust Micro-Segmentation Forward Proxy architecture. It operates independently alongside the high-throughput Data Plane, providing dynamic runtime policy management, instantaneous threat containment, live cryptographic ledger attestation, and real-time observability.

---

## 1. Architectural Architecture & Port Separation

ZetaShield strictly decouples the **Data Plane** and the **Control Plane** into separate network listeners:

```
                          ┌──────────────────────────────────────┐
                          │         Operator / SOC Team          │
                          └──────┬────────────────────────┬──────┘
                                 │                        │
                    zetashield_ctl.py CLI            Web Browser
                                 │                        │
                         REST API & SSE             HTTP / Static
                                 │                        │
                                 ▼                        ▼
                   ┌──────────────────────────────────────────────┐
                   │   Control Plane & Telemetry Server (:8444)   │
                   │   - REST API: /api/v1/*                      │
                   │   - SSE Live Event Stream: /api/v1/events    │
                   │   - Embedded SOC Dashboard File Server       │
                   └──────────────────────┬───────────────────────┘
                                          │ Memory Snapshot & Lock-Free Channels
                                          ▼
                   ┌──────────────────────────────────────────────┐
                   │     ZetaShield Core Data Plane (:8443)       │
                   │   - Strictly Enforced Mutual TLS (mTLS)      │
                   │   - Zero-Trust L7 Policy Enforcement Engine  │
                   │   - Hop-2 HMAC Cryptographic Signature       │
                   │   - Non-Blocking SHA-256 Audit Logger        │
                   └──────────────────────────────────────────────┘
```

- **Data Plane (`:8443` mTLS):** Exclusively dedicated to proxying workloads. Rejects all traffic without valid, CA-signed x509 certificates and cryptographic SPIFFE IDs.
- **Control Plane (`:8444` HTTP):** Dedicated administrative and SOC monitoring channel. Serves JSON REST APIs, Server-Sent Events (SSE) telemetry streams, and the embedded dark-mode SOC dashboard.
- **Audit Traceability:** Every administrative operation performed on the Control Plane (mode switch, revocation kill-switch) is recorded into the immutable SHA-256 audit ledger as a `CONTROL` event.

---

## 2. Operator CLI: `zetashield_ctl.py`

The primary command-line interface for platform engineers and security response teams is `zetashield_ctl.py`. It requires **zero third-party dependencies** (runs on Python 3.8+ standard library).

### Environment Configuration
```bash
export ZS_CONTROL_URL="http://127.0.0.1:8444"
```

### CLI Commands Reference

| Command | Usage | Description |
| :--- | :--- | :--- |
| `status` | `python zetashield_ctl.py status` | Displays cluster health, uptime, active mode, live metrics, and ledger cryptographic attestation. |
| `revoke` | `python zetashield_ctl.py revoke <id>` | **1-Click Kill-Switch**: Instantly revokes an identity in RAM. Subsequent requests fail immediately with `403 Forbidden`. |
| `unrevoke` | `python zetashield_ctl.py unrevoke <id>` | Clears dynamic revocation and restores legitimate access for a recovered identity. |
| `mode` | `python zetashield_ctl.py mode <enforce\|learning>` | Toggles between strict enforcement (`DENY`) and discovery mode (`SHADOW_DENY`). |
| `discover` | `python zetashield_ctl.py discover` | Inspects unmapped network flows observed during Learning Mode and outputs candidate YAML policy rules. |
| `verify` | `python zetashield_ctl.py verify` | Verifies the cryptographic integrity of the SHA-256 audit ledger from block #1 to current. |

---

## 3. Step-by-Step Operator Workflows

### A. 1-Click Threat Containment (Identity Kill-Switch)
If an identity's private key is compromised (e.g., `frontend-service`):
```bash
# 1. Trigger instantaneous kill-switch
python control-plane/zetashield_ctl.py revoke frontend-service

# Result:
# 🚨 [KILL-SWITCH ACTIVE] Identity revoked immediately: spiffe://zetashield.local/ns/default/sa/frontend-service
# All requests presenting this SPIFFE certificate will be dropped with 403 Forbidden.

# 2. Check cluster status to verify revocation in memory
python control-plane/zetashield_ctl.py status

# 3. After workload remediation / credential rotation, restore access:
python control-plane/zetashield_ctl.py unrevoke frontend-service
```

### B. Safe Day-0 Policy Learning (Shadow Mode)
When introducing ZetaShield into an existing legacy microservice mesh:
```bash
# 1. Put the gateway into learning mode
python control-plane/zetashield_ctl.py mode learning

# 2. Run legitimate service traffic through the mesh
# Unmapped flows are permitted (allowing services to operate) but flagged as SHADOW_DENY and tracked.

# 3. Export discovered policy rules into declarative YAML:
python control-plane/zetashield_ctl.py discover

# 4. Review candidate YAML, commit to deploy/policy.yaml, and re-lock the gateway:
python control-plane/zetashield_ctl.py mode enforce
```

---

## 4. Control Plane REST API Reference

The Control Plane exposes lightweight JSON endpoints on port `:8444`:

### `GET /api/v1/status`
Returns high-level cluster state, cryptographic ledger integrity, active routes, rules, and revocation lists.
```json
{
  "version": "2.1-enterprise",
  "uptime_sec": 1420,
  "mode": "enforce",
  "ledger": {
    "intact": true,
    "verified_records": 108,
    "latest_hash": "a4b2c1..."
  },
  "metrics": {
    "total": 512,
    "allow": 480,
    "deny": 28,
    "tls_reject": 4,
    "shadow_deny": 0,
    "error": 0
  },
  "revoked_identities": [
    "spiffe://zetashield.local/ns/default/sa/rogue-service"
  ]
}
```

### `GET /api/v1/audit`
Returns the 100 most recent cryptographic audit records from the active ledger.

### `GET /api/v1/events`
Server-Sent Events (SSE) live stream. Pushes newline-delimited JSON events immediately as requests are processed by the Data Plane. Used directly by the SOC Telemetry Dashboard.

### `POST /api/v1/revoke`
Dynamic RAM revocation toggle.
```json
// Request:
{
  "identity": "frontend-service",
  "action": "revoke" // or "unrevoke"
}

// Response:
{
  "status": "ok",
  "identity": "spiffe://zetashield.local/ns/default/sa/frontend-service",
  "action": "revoke"
}
```

### `POST /api/v1/mode`
Switch runtime enforcement mode.
```json
// Request:
{
  "mode": "learning" // or "enforce"
}

// Response:
{
  "status": "ok",
  "mode": "learning"
}
```

---

## 5. Security & Deployment Hardening

1. **Network Segregation:** In multi-tenant cloud deployments, port `8444` should only be bound to an internal VPN, bastion network, or localhost (`127.0.0.1:8444`). Port `8443` is the sole public/ingress port.
2. **Zero Runtime Dependencies:** The control plane is fully integrated into the compiled Go binary and Python standard library, eliminating external package vulnerabilities.
3. **Audited Admin Actions:** Dynamic administrative changes trigger synchronous records in the SHA-256 hash-chained ledger, preventing unauthorized or untracked changes.

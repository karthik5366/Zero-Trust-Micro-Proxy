[![CI](https://github.com/karthik5366/Zero-Trust-Micro-Proxy/actions/workflows/ci.yml/badge.svg)](https://github.com/karthik5366/Zero-Trust-Micro-Proxy/actions/workflows/ci.yml)

# ZetaShield: Zero-Trust Micro-Segmentation Gateway

A deployable, identity-aware Layer-7 security gateway for HTTP microservices.
Every service-to-service call must present a cryptographic certificate — the
gateway verifies identity, enforces deny-by-default policy, and blocks
lateral movement between services. **Nothing reaches a backend without
an explicit ALLOW.**

---

## What It Does

- **Mutual TLS (mTLS)** — Every caller must present an x509 certificate
  signed by the gateway's Certificate Authority. No cert = connection
  rejected at the TLS handshake.
- **Cryptographic Identity** — Caller identity is extracted from the
  certificate's Subject Alternative Name (SPIFFE URI format: `spiffe://zetashield.local/ns/default/sa/<service>`) — unforgeable.
- **Micro-Segmentation** — Services are isolated from each other.
  `orders-service` cannot reach `payments-api` unless explicitly allowed.
- **Deny-by-Default Policy** — Declarative `policy.yaml` rules control
  which identity can call which path with which HTTP method.
  Unmatched = denied (`403 Forbidden`) + logged.
- **Fail-Closed** — No cert, no rule, or unreachable backend →
  the request dies. Failure is never permission.
- **Full Audit Trail** — Every decision (`ALLOW`/`DENY`/`ERROR`) is logged to
  structured, append-only JSONL with identity, method, path, and reason.

---

## Architecture

```
   SERVICE FLEET (with certs)        PROTECTED BACKENDS (localhost only)

   frontend-service  ──mTLS──┐      ┌── orders-api   :9091
   orders-service    ──mTLS──┼────▶ │
   payments-service ──mTLS──┘      │   ZERO-TRUST
   attacker (no/bad cert) ──✗──▶   │   GATEWAY :8443 ──▶ payments-api :9092
                                  │
                                  └── Policy: policy.yaml (deny-by-default)
                                      Audit:  audit.log.jsonl (every decision)
```

**Two layers. One enforcement point. All backends network-isolated.**

---

## Project Structure

```text
Zero-Trust-Micro-Proxy/
├── .github/workflows/ci.yml  # GitHub Actions CI workflow (vet, build, test)
├── certs/                    # PKI scripts & generated certificates
│   ├── generate_ca.sh        # Root CA creation script
│   └── issue_cert.sh         # SAN-aware service & proxy cert issuance
├── data-plane-proxy/         # Go Layer-7 zero-trust gateway
│   ├── main.go               # Gateway server, mTLS, policy & reverse proxy
│   ├── policy_test.go        # 16 table-driven unit tests
│   └── cmd/loadtest/         # Latency & enforcement overhead benchmark
├── mock-apps/                # Upstream microservices & test runner
│   ├── orders_api.py         # Mock orders backend (:9091)
│   ├── payments_api.py       # Mock payments backend (:9092)
│   └── client.py             # 5-test demo verification client
├── policy.yaml               # Declarative routes & deny-by-default rules
├── control-plane/            # (Phase 2) Dynamic control plane
└── telemetry-dashboard/      # (Phase 2) Real-time telemetry dashboard
```

---

## Prerequisites

- **Go**: 1.21+ (uses standard library `net/http/httputil`, `crypto/tls`, `crypto/x509`)
- **Python**: 3.8+ (standard library only, zero external dependencies)
- **OpenSSL**: For certificate authority and service keypair generation
- **Bash Shell**: Linux/macOS terminal, or Git Bash / WSL on Windows

---

## Quick Start

### 1. Generate Certificates (Local CA + Service Certs)

```bash
cd certs
bash generate_ca.sh
bash issue_cert.sh frontend-service
bash issue_cert.sh orders-service
bash issue_cert.sh payments-service
bash issue_cert.sh proxy
cd ..
```

> **Note on `proxy` cert**: `issue_cert.sh` automatically configures `IP:127.0.0.1` and `DNS:localhost` in addition to the SPIFFE URI for the proxy certificate so TLS verification succeeds without hostname mismatches.

### 2. Start the Backends (Separate Terminals)

```bash
# Terminal 1: Orders Backend
python mock-apps/orders_api.py

# Terminal 2: Payments Backend
python mock-apps/payments_api.py
```

### 3. Start the Gateway

```bash
cd data-plane-proxy
go run main.go
```

The gateway listens on `https://127.0.0.1:8443` with mTLS strictly required.

### 4. Run the 5-Test Demo Sequence

Run from inside the `mock-apps/` directory so certificate relative paths resolve properly:

```bash
cd mock-apps
python client.py
```

**Expected results:** `200, TLS_REJECTED, 403, 403, 200`

---

## The 5-Test Demo Sequence

| Test | Caller | Request | Result | Demonstrates |
|:---:|:---|:---|:---:|:---|
| **1** | `frontend-service` | `GET /orders/list` | **200 OK** | Authorized access flows through |
| **2** | No certificate | `GET /orders/list` | **TLS Rejected** | No identity = connection dropped at handshake |
| **3** | `frontend-service` | `GET /admin/delete` | **403 Forbidden** | Deny-by-default (no matching rule) |
| **4** | `orders-service` | `GET /payments/balance` | **403 Forbidden** | **Micro-segmentation** (lateral movement blocked) |
| **5** | `payments-service` | `GET /payments/balance` | **200 OK** | Own-domain access allowed |

---

## Policy Configuration (`policy.yaml`)

Policies are evaluated in-memory and default to deny:

```yaml
version: "1.0"

routes:
  /orders/:   http://127.0.0.1:9091
  /payments/: http://127.0.0.1:9092

rules:
  # frontend-service can read orders
  - identity: spiffe://zetashield.local/ns/default/sa/frontend-service
    path_prefix: /orders/
    methods: [GET]

  # frontend-service can make payments
  - identity: spiffe://zetashield.local/ns/default/sa/frontend-service
    path_prefix: /payments/
    methods: [GET, POST]

  # orders-service can read orders (its own domain)
  - identity: spiffe://zetashield.local/ns/default/sa/orders-service
    path_prefix: /orders/
    methods: [GET]

  # payments-service can access payments (its own domain)
  - identity: spiffe://zetashield.local/ns/default/sa/payments-service
    path_prefix: /payments/
    methods: [GET, POST]

  # NO RULE for orders-service -> /payments/ = DENIED (lateral movement blocked)
  # NO RULE for payments-service -> /orders/ = DENIED
```

---

## Audit Trail & Observability

Every authorization event is written synchronously to `data-plane-proxy/audit.log.jsonl`:

```json
{"timestamp":"2026-10-07T13:40:02Z","decision":"DENY","identity":"spiffe://zetashield.local/ns/default/sa/orders-service","method":"GET","path":"/payments/balance","reason":"no matching ALLOW rule (deny-by-default)"}
```

To inspect recent audit decisions:

```bash
tail -n 10 data-plane-proxy/audit.log.jsonl
```

---

## Performance Benchmark

ZetaShield includes a built-in latency benchmark comparing direct-to-backend calls against gateway-enforced calls over 500 requests:

```bash
cd data-plane-proxy
go run ./cmd/loadtest
```

### Sample Benchmark Results

```text
MODE                         MEAN         P50          P99
Direct to backend            0.82ms       0.75ms       1.94ms
Through Zero-Trust gateway   1.48ms       1.35ms       3.12ms
──────────────────────────────────────────────────────────
Zero-Trust enforcement overhead (median): ~0.60ms
```

> **Enforcement overhead includes:** full mTLS connection, x509 SAN identity extraction, YAML policy evaluation, reverse-proxy routing, and structured JSONL audit write.

---

## Testing

Run the 16 table-driven unit tests:

```bash
cd data-plane-proxy
go test -v ./...
```

Tests cover:
- Allowed rules and method constraints (`GET`, `POST`, `*`)
- Path prefix boundary enforcement
- Unknown caller identities & empty identity rejection
- Root (`/`) and admin (`/admin/delete`) path probing
- **Cross-service segmentation verification** (`orders` blocked from `payments` and vice-versa)

---

## Design Evolution

| Version | Architecture | Change |
|:---:|:---|:---|
| **V0.1** | Client proxy → Server proxy → backend (4 hops) | Initial sidecar-mesh prototype |
| **V1.0** | **Single consolidated gateway (2 hops)** | **Per Review 1 feedback:** reduced latency (~0.6ms median overhead), simplified topology, multi-backend micro-segmentation, fail-closed reverse proxy, and SPIFFE mTLS |
| **V2.0** | Docker-Compose deployment + admin console | Phase 2: Dynamic control plane and telemetry dashboard |

---

## Tech Stack

- **Gateway**: Go 1.21+ (`net/http/httputil`, `crypto/tls`, `gopkg.in/yaml.v3`)
- **PKI**: OpenSSL (local Root CA, SPIFFE-format SAN identities)
- **Policy**: Declarative `policy.yaml` (Deny-by-default PBAC)
- **Backends**: Python stdlib (zero dependencies)
- **CI**: GitHub Actions — `vet` + `build` + `test` on push/PR

---

*Group 39 · DSN4091 Capstone · Supervisor: Dr. Sajjad Ahmed*
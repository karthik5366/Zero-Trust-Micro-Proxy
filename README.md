# ZetaShield: Zero-Trust Micro-Segmentation Gateway

[![CI](https://github.com/karthik5366/Zero-Trust-Micro-Proxy/actions/workflows/ci.yml/badge.svg)](https://github.com/karthik5366/Zero-Trust-Micro-Proxy/actions/workflows/ci.yml)

A deployable, identity-aware Layer-7 security gateway for HTTP microservices.
Every service-to-service call must present a cryptographic certificate — the gateway verifies identity, enforces deny-by-default policy, and blocks lateral movement between services. **Nothing reaches a backend without an explicit ALLOW.**

---

## Core Capabilities

*   **Mutual TLS (mTLS):** Every caller must present an x509 certificate signed by the gateway's Certificate Authority. No cert = connection rejected at the TLS handshake.
*   **Cryptographic Identity:** Caller identity is extracted from the certificate's Subject Alternative Name (SPIFFE URI format: `spiffe://zetashield.local/ns/default/sa/<service>`) — unforgeable.
*   **Micro-Segmentation:** Services are isolated from each other. `orders-service` cannot reach `payments-api` unless explicitly allowed.
*   **Deny-by-Default Policy:** Declarative `policy.yaml` rules control which identity can call which path with which HTTP method. Unmatched = denied (`403 Forbidden`) + logged.
*   **Fail-Closed:** No cert, no rule, or unreachable backend → the request dies. Failure is never permission.
*   **Policy Hot-Reload:** Edits to `policy.yaml` are monitored and dynamically reloaded in real time with zero downtime and no container restart required.
*   **Full Audit Trail:** Every decision (`ALLOW`/`DENY`/`ERROR`) is logged to structured, append-only JSONL with identity, method, path, and reason.

---

## Architecture

```text
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

## Performance Benchmark

ZetaShield is lightweight. We benchmarked 500 requests to measure the cost of full Zero-Trust enforcement (mTLS handshake, SAN extraction, policy eval, reverse proxy, audit write).

| Metric | Direct to Backend | Through ZetaShield | Overhead |
| :--- | :--- | :--- | :--- |
| **Mean** | 0.82ms | 1.48ms | ~0.66ms |
| **Median (P50)** | 0.75ms | 1.35ms | **~0.60ms** |
| **P99** | 1.94ms | 3.12ms | ~1.18ms |

> **Result:** Full identity verification and policy enforcement adds only **~0.6ms** median latency per request.

---

## Project Structure

```text
Zero-Trust-Micro-Proxy/
├── .github/workflows/ci.yml  # GitHub Actions CI (vet + build + 19 tests)
├── certs/                    # PKI scripts & generated certificates
│   ├── generate_ca.sh        # Root CA creation
│   └── issue_cert.sh         # SAN-aware service cert issuance
├── data-plane-proxy/         # Go Layer-7 zero-trust gateway
│   ├── main.go               # Gateway server & reverse proxy
│   ├── policy_test.go        # 19 table-driven unit tests
│   └── cmd/loadtest/         # Latency benchmark tool
├── mock-apps/                # Upstream microservices & test runner
│   ├── orders_api.py         # Mock orders backend (:9091)
│   ├── payments_api.py       # Mock payments backend (:9092)
│   └── client.py             # 7-test adversarial demo client
├── policy.yaml               # Declarative routes & deny-by-default rules
└── README.md                 # This file
```

---

## Prerequisites

*   **Go:** 1.21+ (Standard library `net/http/httputil`, `crypto/tls`, `crypto/x509`)
*   **Python:** 3.8+ (Standard library only, zero external dependencies)
*   **OpenSSL:** For certificate authority and service keypair generation
*   **Bash Shell:** Linux/macOS terminal, or **Git Bash** on Windows

---

## Quick Start

### 1. Generate Certificates (Local CA + Service Certs)
Run these commands in **Git Bash** (Windows) or standard terminal (Linux/Mac):

```bash
cd certs
export MSYS_NO_PATHCONV=1  # Required for Git Bash on Windows
bash generate_ca.sh
bash issue_cert.sh frontend-service
bash issue_cert.sh orders-service
bash issue_cert.sh payments-service
bash issue_cert.sh proxy
cd ..
```
> *Note: `issue_cert.sh` automatically configures `IP:127.0.0.1` and `DNS:localhost` for the proxy certificate to ensure local TLS verification succeeds.*

### 2. Generate Adversarial Assets (Test 6)
Create a forged certificate that claims to be `frontend-service` but is self-signed (untrusted):

```bash
cd certs
export MSYS_NO_PATHCONV=1
openssl req -x509 -newkey rsa:2048 -nodes -keyout attacker-key.pem -out attacker.pem -days 30 \
  -subj "/CN=frontend-service" \
  -addext "subjectAltName=URI:spiffe://zetashield.local/ns/default/sa/frontend-service"
cd ..
```

### 3. Start the Backends
Run in separate terminals:
```bash
# Terminal 1
python mock-apps/orders_api.py

# Terminal 2
python mock-apps/payments_api.py
```
*(Note: Do NOT start an inventory backend; Test 7 relies on it being offline to demonstrate fail-closed behavior.)*

### 4. Start the Gateway
Run from the `data-plane-proxy` directory:
```bash
cd data-plane-proxy
go run main.go
```
The gateway listens on `https://127.0.0.1:8443` with mTLS strictly required.

### 5. Run the 7-Test Adversarial Suite
Run from inside the `mock-apps/` directory:
```bash
cd mock-apps
python client.py
```

---

## Docker Deployment (V2.0 Containerized Mesh)

Run the entire Zero-Trust mesh with network namespace isolation in Docker:

```bash
# 1. Build and start the mesh (Gateway + isolated backends)
docker compose up --build -d

# 2. Run the 7-test adversarial suite from host
cd mock-apps
python client.py

# 3. Verify backend network isolation (direct host access fails)
curl http://127.0.0.1:9091/orders/list
# Expected: Connection refused

# 4. Tear down
docker compose down
```

> **Network Isolation Guarantee:** The Gateway is the **only** service with an exposed host port (`:8443`). Backends have no port mappings and communicate solely via Docker's internal `zeta-net` bridge network.

---

## The 7-Test Adversarial Matrix

| Test | Scenario | Expected Result | Security Guarantee Demonstrated |
| :--- | :--- | :--- | :--- |
| **1** | Authorized Access (`frontend` → `orders`) | **200 OK** | Valid flow passes. |
| **2** | No Certificate (Anonymous) | **TLS Rejected** | Identity required at transport layer. |
| **3** | Authorized Identity, Unauthorized Path | **403 Forbidden** | Deny-by-default policy enforcement. |
| **4** | Lateral Movement (`orders` → `payments`) | **403 Forbidden** | Micro-segmentation blocks cross-service access. |
| **5** | Authorized Access (Own Domain) | **200 OK** | Service can access its own resources. |
| **6** | Forged Cert (Valid SAN, Untrusted CA) | **TLS Rejected** | Trust is in the Issuer (CA), not the Claim. |
| **7** | Valid Request, Dead Backend (`inventory`) | **503 Fail-Closed** | Availability failure does not grant access. |

---

## Audit Trail

Every decision is logged to `data-plane-proxy/audit.log.jsonl`. Inspect recent activity:
```bash
tail -n 10 data-plane-proxy/audit.log.jsonl
```
**Sample Log:**
```json
{"timestamp":"2026-10-07T13:40:02Z","decision":"DENY","identity":"spiffe://zetashield.local/ns/default/sa/orders-service","method":"GET","path":"/payments/balance","reason":"no matching ALLOW rule"}
```

---

## Testing

Run the 19 table-driven unit tests:
```bash
cd data-plane-proxy
go test -v ./...
```
*   **14 Policy Tests:** Verifies identity/path/method matching and deny-by-default logic.
*   **5 Routing Tests:** Verifies longest-prefix matching for backend selection.

---

## Design Evolution

| Version | Architecture | Change |
| :--- | :--- | :--- |
| **V0.1** | Sidecar Mesh (4 hops) | Initial prototype; high latency. |
| **V1.0** | **Consolidated Gateway (2 hops)** | Reduced latency (~0.6ms), simplified topology, strict mTLS. |
| **V2.0** | **Containerized Mesh** | **Complete:** Docker-Compose deployment, network namespace isolation, zero-downtime policy hot-reload. *(Phase 2: React Admin Console).* |

---

## Academic Context

*   **Course:** DSN4091 Capstone Project Phase 1
*   **Group:** 39
*   **Supervisor:** Dr. Sajjad Ahmed
*   **Team:** Karthik P.H.S.R (Lead), Sahil S. Thakkar, Shaivyaa Sharma, Subeer Srivastava, Sameep Upadhyay.
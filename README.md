
```markdown
![CI](https://github.com/karthik5366/Zero-Trust-Micro-Proxy/actions/workflows/ci.yml/badge.svg)

# ZetaShield: Zero-Trust Micro-Segmentation Gateway

A deployable, identity-aware Layer-7 security gateway for HTTP microservices.
Every service-to-service call must present a cryptographic certificate — the
gateway verifies identity, enforces deny-by-default policy, and blocks
lateral movement between services. **Nothing reaches a backend without
an explicit ALLOW.**

## What It Does

- **Mutual TLS (mTLS)** — every caller must present an x509 certificate
  signed by the gateway's Certificate Authority. No cert = connection
  rejected at the TLS handshake.
- **Cryptographic Identity** — caller identity is extracted from the
  certificate's Subject Alternative Name (SPIFFE URI format) — unforgeable.
- **Micro-Segmentation** — services are isolated from each other.
  `orders-service` cannot reach `payments-api` unless explicitly allowed.
- **Deny-by-Default Policy** — declarative `policy.yaml` rules control
  which identity can call which path with which HTTP method.
  Unmatched = denied + logged.
- **Fail-Closed** — no cert, no rule, or unreachable backend →
  the request dies. Failure is never permission.
- **Full Audit Trail** — every decision (ALLOW/DENY) is logged to
  structured, append-only JSONL with identity, method, path, and reason.

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

## Quick Start

```bash
# 1. Generate certificates (local CA + service certs)
cd certs && bash generate_ca.sh
bash issue_cert.sh frontend-service
bash issue_cert.sh orders-service
bash issue_cert.sh payments-service
bash issue_cert.sh proxy

# 2. Start the backends (each in its own terminal)
python mock-apps/orders_api.py
python mock-apps/payments_api.py

# 3. Start the gateway
cd data-plane-proxy && go run main.go

# 4. Run the 5-test demo
python mock-apps/client.py
```

**Expected:** `200, TLS_REJECTED, 403, 403, 200`

## The 5-Test Demo Sequence

| Test | Caller | Request | Result | Demonstrates |
|------|--------|---------|--------|--------------|
| 1 | frontend-service | GET /orders/ | **200** | Authorized access flows |
| 2 | No certificate | GET /orders/ | **TLS rejected** | No identity = no connection |
| 3 | frontend-service | GET /admin/ | **403** | Deny-by-default (no rule) |
| 4 | orders-service | GET /payments/ | **403** | **Micro-segmentation** |
| 5 | payments-service | GET /payments/ | **200** | Own-domain access allowed |

## Policy (policy.yaml)

```yaml
routes:
  /orders/:   http://127.0.0.1:9091
  /payments/: http://127.0.0.1:9092

rules:
  - identity: spiffe://zetashield.local/ns/default/sa/frontend-service
    path_prefix: /orders/
    methods: [GET]
  # ... only explicit ALLOWs. Everything else: DENIED.
```

## Design Evolution

| Version | Architecture | Change |
|---------|-------------|--------|
| V0.1 | Client proxy → Server proxy → backend (4 hops) | Initial sidecar-mesh pattern |
| **V1.0** | **Single consolidated gateway (2 hops)** | **Per Review 1 feedback: reduced latency, simplified topology, added multi-backend micro-segmentation + mTLS** |
| V2.0 | Docker-Compose deployment + admin console | Phase 2 |

## Tech Stack

- **Gateway**: Go 1.23+ (stdlib `net/http/httputil`, `crypto/tls`)
- **PKI**: OpenSSL (local Root CA, SPIFFE-format SAN identities)
- **Policy**: declarative `policy.yaml` (gopkg.in/yaml.v3)
- **Backends**: Python stdlib (zero dependencies)
- **CI**: GitHub Actions — vet + build + 16 unit tests on every push

## Testing

16 table-driven unit tests cover: allowed rules, method enforcement,
path enforcement, unknown identities, empty identities, and — critically —
**cross-service segmentation** (`orders blocked from payments`, and vice versa).

---

*Group 39 · DSN4091 Capstone · Supervisor: Dr. Sajjad Ahmed*
```

---
# ZetaShield Real-Time SOC Telemetry & Control Console

The **ZetaShield Telemetry Dashboard** is a zero-dependency, real-time Security Operations Center (SOC) console. It connects directly to the ZetaShield Control Plane (`:8444`) to provide live micro-segmentation visibility, instant threat response, and cryptographic ledger attestation.

---

## 1. Core Capabilities

- **Zero-Dependency Architecture:** Pure vanilla HTML5, CSS3, and modern ES6 JavaScript. No Node.js runtime, no npm packages, no external CDN dependencies (100% operational in air-gapped environments).
- **Real-Time Streaming Telemetry:** Ingests live traffic events over Server-Sent Events (SSE) via `/api/v1/events` with zero polling latency.
- **Dynamic Service Topology Map:** Interactive SVG service mesh topology showing real-time animated traffic pulses:
  - 🟢 **Pulsing Green:** Legitimate, authenticated Zero-Trust allowed requests.
  - 🔴 **Flashing Red:** Blocked privilege escalation, unauthorized lateral movement, or dropped TLS handshakes.
  - 🟡 **Pulsing Amber:** Shadow-mode learning requests.
- **1-Click Identity Kill-Switch:** Real-time RAM revocation interface. Operators can immediately cut off compromised service certificates in under 1 millisecond.
- **Runtime Mode Switcher:** Seamlessly toggle between strict Zero-Trust enforcement (`ENFORCE`) and discovery mode (`LEARNING`) without restarting the gateway.
- **Cryptographic Ledger Integrity Badge:** Continuous client-side attestation verifying that the SHA-256 tamper-evident hash chain remains completely unbroken.
- **Policy Discovery Drawer:** Displays auto-synthesized YAML rules for unmapped traffic observed during Learning Mode, with 1-click clipboard export.

---

## 2. Accessing the Dashboard

### Via Embedded Gateway Server (Recommended)
When the ZetaShield Gateway runs (via Docker Compose or local binary), the dashboard is automatically served on port `8444`:
```
http://localhost:8444/
```

### Standalone Local Preview
Alternatively, the static `index.html` file can be opened directly in any modern web browser or served using Python's built-in HTTP server:
```bash
cd telemetry-dashboard
python -m http.server 3000
# Open http://localhost:3000 in your browser
```
*(The dashboard automatically detects its origin and connects to `http://127.0.0.1:8444` for control and SSE streaming).*

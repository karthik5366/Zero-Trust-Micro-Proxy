# ZetaShield V2.0: Capstone Review 2 Visual Presentation Guide

> **Quick Instructions for Review Day**:
> Open the folder `review-assets/` in the Windows Photos app or open `review-assets/index.html` in your browser.
> Press the **Right Arrow key (`->`)** to advance image by image as you speak.
> Below is your exact **30-second presentation script** for each diagram, along with answers to tough questions examiners frequently ask.

---

## Slide-by-Slide Visual Walkthrough

### 📸 `01_Problem_Flat_Network_vs_Zero_Trust.png`
- **What this shows**: Traditional flat network vulnerabilities vs. ZetaShield Layer-7 micro-segmentation.
- **Your 30-Second Script**:
  > *"Respected panel, traditional perimeter firewalls operate at Layer 3 and Layer 4, leaving internal networks completely 'flat'. As shown on the left, once an attacker compromises an edge service, they can move laterally across internal subnets without further authentication, accessing sensitive databases like Payments. OWASP classifies this as Broken Access Control—the #1 web vulnerability. ZetaShield, shown on the right, enforces NIST SP 800-207 Zero-Trust micro-segmentation. Every internal service must present an mTLS cryptographic identity. Unregistered callers are dropped at the TLS handshake, making lateral jumps physically impossible."*
- **Panel Trap Question**: *"Why can't iptables or firewall rules solve this?"*
  > **Answer**: *"IP addresses are dynamic in containerized fleets, and Layer-4 firewalls cannot inspect HTTP paths or verbs. An attacker on an allowed IP can still issue malicious POST or DELETE calls. ZetaShield enforces Layer-7 identity and path-level policies."*

---

### 📸 `02_System_Context_and_Threat_Boundary.png`
- **What this shows**: Formal System Context Diagram demarcating Untrusted Clients, the Enforcement Gateway Boundary, and Protected Backends.
- **Your 30-Second Script**:
  > *"This diagram establishes our formal STRIDE threat boundaries. Zone 0 comprises untrusted client callers. Zone 1 is the ZetaShield Gateway running on port 8443, which acts as the single fail-closed enforcement point. It terminates TLS, parses X.509 certificates against our Root CA, extracts SPIFFE IDs from Subject Alternative Names, and evaluates deny-by-default policy rules. Only verified requests enter Zone 2, our isolated Docker backend fleet."*
- **Panel Trap Question**: *"What happens if the gateway crashes?"*
  > **Answer**: *"The system is fail-closed. If the gateway process is unreachable, the TCP port refuses connections. Failure is never permission."*

---

### 📸 `03_Network_Topology_and_Docker_Isolation.png`
- **What this shows**: Docker bridge network (`zeta-net`) isolation solving the Review 1 deployability critique.
- **Your 30-Second Script**:
  > *"Addressing the feedback from Review 1 requesting an isolated, deployable solution: we engineered complete network containment using a custom Docker bridge network (`zeta-net` on subnet 172.28.0.0/16). The ZetaShield Gateway is the only container with a host-mapped port (8443). The backend containers—Orders on 9091 and Payments on 9092—bind strictly internally with zero published host ports. As highlighted in red, if an attacker on the host machine attempts `curl localhost:9091`, the OS kernel returns 'Connection Refused' immediately."*
- **Panel Trap Question**: *"Can an attacker on the host reach the backends using their container IPs?"*
  > **Answer**: *"In Docker bridge networks on Linux/production hosts, the bridge subnet is isolated via iptables rules unless explicitly routed. In production, we place backends in an internal VPC private subnet."*

---

### 📸 `04_End_to_End_2Hop_Consolidated_Architecture.png`
- **What this shows**: Architectural transition from 4-Hop Sidecar Mesh (V0.1) to 2-Hop Consolidated Gateway (V2.0).
- **Your 30-Second Script**:
  > *"In Review 1, our V0.1 architecture used a 4-hop sidecar mesh modeled after Istio. The panel rightfully noted that 4 hops added over 4 milliseconds of latency and excessive memory overhead. In V2.0, we consolidated this into an optimized 2-hop gateway: Hop 1 is mTLS from caller to gateway, where identity and policies are evaluated; Hop 2 is high-speed plain HTTP over the isolated Docker bridge. This reduced latency overhead by over 80% down to just 0.60 milliseconds."*

---

### 📸 `05_mTLS_Handshake_and_SPIFFE_SAN_Extraction.png`
- **What this shows**: Cryptographic authentication mechanism and why SPIFFE URIs in X.509 SAN extensions cannot be spoofed.
- **Your 30-Second Script**:
  > *"Identity in ZetaShield is not a spoofable HTTP header like `X-User-ID`. We follow the production SPIFFE standard used by CNCF projects like Istio and SPIRE. During the TLS handshake, our gateway validates the client's X.509 certificate against our trusted Root CA (`ca.pem`). We extract the URI from the Subject Alternative Name extension: `spiffe://zetashield.local/ns/default/sa/frontend-service`. If an attacker creates a self-signed cert with that same URI, the handshake drops immediately because the Issuer CA is untrusted."*
- **Panel Trap Question**: *"What prevents a replay attack or cert theft?"*
  > **Answer**: *"TLS 1.3 requires the client to prove possession of the private key during the handshake via the CertificateVerify signature. A stolen public certificate cannot complete the handshake without the corresponding private key."*

---

### 📸 `06_PBAC_Policy_Evaluation_Flowchart.png`
- **What this shows**: Deny-by-default policy decision engine flowchart.
- **Your 30-Second Script**:
  > *"Our policy engine follows strict Policy-Based Access Control (PBAC) with a deny-by-default invariant. When a request arrives with a verified SPIFFE ID, the engine checks: First, does a rule exist for this identity? Second, does the requested URI match the configured `path_prefix` using longest-prefix matching? Third, is the HTTP verb in the allowed methods list? If all three match, it forwards the request with 200 OK. If any condition fails, it drops down to 403 Forbidden. There are zero implicit permissions."*

---

### 📸 `07_Hot_Reload_Engine_State_Machine.png`
- **What this shows**: Zero-downtime policy hot-reload mechanism using Go's `sync.RWMutex` and file modtime watching.
- **Your 30-Second Script**:
  > *"ZetaShield supports live policy hot-reloading without dropping active TCP connections or restarting containers. A dedicated background goroutine polls the `policy.yaml` modification timestamp every 1 second. When changes occur, it parses the YAML and performs an atomic in-memory swap under a write lock (`policyMu.Lock()`), which is held for less than 0.05 milliseconds. Concurrent requests continue reading via read locks (`RLock()`). In our live demo, editing the policy takes effect in under 1 second."*

---

### 📸 `08_Request_Lifecycle_Sequence_Diagram.png`
- **What this shows**: Full chronological packet flow from client connection to JSONL audit logging.
- **Your 30-Second Script**:
  > *"This sequence diagram traces the complete 9-step request lifecycle. Steps 1 and 2 negotiate mTLS. Step 3 dispatches the HTTP request. Step 4 and 5 evaluate PBAC rules in-memory. Steps 6 and 7 reverse-proxy the request to the internal backend and receive the response. Step 8 returns the payload to the caller. Crucially, Step 9 asynchronously writes an immutable event to `audit.log.jsonl`, ensuring forensic traceability without blocking the response pipeline."*

---

### 📸 `09_The_7_Test_Adversarial_Suite_Matrix.png`
- **What this shows**: Complete test verification matrix across all 7 adversarial attack vectors.
- **Your 30-Second Script**:
  > *"To empirically prove our security guarantees, we built an automated 7-test adversarial suite: Test 1 verifies legitimate authorized proxying (200 OK). Test 2 confirms anonymous connections are rejected at the TLS layer. Test 3 validates deny-by-default when an authorized user targets an unconfigured path (403 Forbidden). Test 4 proves micro-segmentation blocks lateral movement from Orders to Payments (403 Forbidden). Test 5 confirms own-domain access (200 OK). Test 6 verifies forged certificates with untrusted CAs are rejected. Test 7 verifies fail-closed resiliency against a dead backend (503 Service Unavailable). All 7 tests pass deterministically in 0.42 seconds."*

---

### 📸 `10_Forensic_Audit_Log_JSONL_Architecture.png`
- **What this shows**: Structured audit logging schema conforming to NIST SP 800-53 and ISO 27001.
- **Your 30-Second Script**:
  > *"Every access decision is recorded in an append-only JSONL audit ledger. Each record captures the UTC timestamp, source IP, authenticated SPIFFE identity, target backend, HTTP method, path, status code, decision, and explicit forensic reason—such as `lateral_movement_blocked`. This satisfies NIST SP 800-53 AU-2 and AU-3 audit compliance and gives security teams immediate non-repudiation telemetry."*

---

### 📸 `11_Latency_Overhead_Benchmark_Comparison.png`
- **What this shows**: Empirical benchmark of 500 requests measuring latency overhead.
- **Your 30-Second Script**:
  > *"We benchmarked 500 sequential requests comparing a direct unprotected backend against the ZetaShield Gateway. The unprotected baseline ran at ~0.75 ms P50. Through ZetaShield, P50 latency was ~1.35 ms. This demonstrates that full mTLS termination, X.509 SAN extraction, in-memory PBAC evaluation, reverse proxying, and audit logging adds only ~0.60 milliseconds of overhead—a sub-millisecond enforcement tax that is completely imperceptible to microservice workloads."*

---

### 📸 `12_Design_Evolution_V01_to_V20.png`
- **What this shows**: Systematic progress across Phase 1 based on formal academic review feedback.
- **Your 30-Second Script**:
  > *"This timeline demonstrates our iterative engineering discipline. In Review 1, the panel provided two primary critiques: first, that a 4-hop sidecar was too complex and slow; second, that the solution needed containerized deployability and automated verification. In V1.0, we consolidated the data plane into a 2-hop Go gateway. In V2.0, we containerized the entire mesh with Docker bridge isolation, implemented zero-downtime hot-reloading, and validated the system with our 7-test adversarial suite."*

---

### 📸 `13_Go_Gateway_Concurrency_and_Internals.png`
- **What this shows**: High-performance Go runtime internals, goroutines, and synchronization primitives.
- **Your 30-Second Script**:
  > *"The gateway engine is implemented in Go for memory safety and concurrency. We utilize `crypto/tls.Listen` configured with `RequireAndVerifyClientCert`. Each TCP connection spawns a lightweight Go goroutine (~2KB memory). We use a `sync.RWMutex` where read locks allow thousands of concurrent policy evaluations without lock contention, while write locks during hot-reloads execute in microseconds. Persistent HTTP transport pools eliminate socket churn."*

---

### 📸 `14_Live_Demo_Execution_Playbook.png`
- **What this shows**: Deterministic 4-step script for the live demonstration.
- **Your 30-Second Script**:
  > *"Our live demonstration follows four distinct verification milestones: Step 1 executes `docker compose up -d` to launch the isolated mesh in seconds. Step 2 attempts `curl localhost:9091` from the host to prove that backends are physically unroutable. Step 3 demonstrates hot-reloading by commenting out a rule in `policy.docker.yaml` and proving instant 403 enforcement without container restart. Step 4 inspects `tail -n 5 audit.log.jsonl` to display the forensic reason for rejection."*

---

## Quick Reference Table for Review Day

| Image File | Primary Topic | Key Number / Term to Quote |
| :--- | :--- | :--- |
| `01_Problem_Flat_Network_vs_Zero_Trust.png` | Problem Statement | OWASP #1 Broken Access Control, Flat Networks |
| `02_System_Context_and_Threat_Boundary.png` | Threat Model | STRIDE, Fail-Closed, Zone 0 vs Zone 1 |
| `03_Network_Topology_and_Docker_Isolation.png` | Network Deployment | `zeta-net` (172.28.0.0/16), Zero Published Ports |
| `04_End_to_End_2Hop_Gateway_Architecture.png` | Architecture | 2-Hop vs 4-Hop, 0.60ms overhead |
| `05_mTLS_Handshake_and_SPIFFE_SAN_Extraction.png` | Authentication | SPIFFE URI in SAN, Root CA trust chain |
| `06_PBAC_Policy_Evaluation_Flowchart.png` | Access Control | Deny-by-Default, Longest-prefix matching |
| `07_Hot_Reload_Engine_State_Machine.png` | Reliability | `sync.RWMutex`, ModTime watcher, <1s reload |
| `08_Request_Lifecycle_Sequence_Diagram.png` | Packet Flow | 9-step UML request-response lifecycle |
| `09_The_7_Test_Adversarial_Suite_Matrix.png` | Testing | 7/7 tests passed in 0.42s (200, TLS_DROP, 403, 503) |
| `10_Forensic_Audit_Log_JSONL_Architecture.png` | Forensics | Append-only JSONL, NIST SP 800-53 AU-2 |
| `11_Latency_Overhead_Benchmark_Comparison.png` | Performance | 500 requests, ~0.75ms -> ~1.35ms (+0.60ms) |
| `12_Design_Evolution_V01_to_V20.png` | Evolution | Review 1 feedback resolved, V0.1 -> V1.0 -> V2.0 |
| `13_Go_Gateway_Concurrency_and_Internals.png` | Engineering | Goroutines, `sync.RWMutex`, zero lock contention |
| `14_Live_Demo_Execution_Playbook.png` | Live Demo | 4 steps: Launch -> Isolate -> Hot-Reload -> Audit |

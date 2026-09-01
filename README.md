![CI](https://github.com/USERNAME/REPOSITORY/actions/workflows/WORKFLOW.yml/badge.svg)

# ZetaShield: Zero-Trust Micro-Segmentation Sidecar Proxy

A lightweight, high-performance, software-defined security mesh designed to enforce **Zero-Trust Network Architecture (ZTNA)** inside containerized microservice environments.

This project addresses the critical vulnerability of lateral network movement (threats spreading inside flat, unsegmented networks) by implementing custom sidecar proxies in **Go (Golang)**, validating service identity via **Mutual TLS (mTLS)**, and enforcing strict access control policies via a centralized Control Plane.

---

## 📐 System Architecture

All application traffic is intercepted, cryptographically verified, and routed through our software-defined data plane before reaching any destination:

```text
+-----------------------+                      +-----------------------+
|  CLIENT APP CONTAINER |                      |  SERVER APP CONTAINER |
|    [Client Web App]   |                      |   [Database Service]  |
|           | (HTTP)    |                      |           ^ (HTTP)    |
|           v           |                      |           |           |
|    [Client Proxy]     | =====( mTLS Tunnel )=====> [Server Proxy]    |
+-----------|-----------+                      +-----------|-----------+
            |                                              |
            +----------( Get Authorization / Policy )------+
                                    |
                                    v
                          +-------------------+
                          |   CONTROL PLANE   |
                          |  (Policy Engine)  |
                          +-------------------+
```

### Request Flow

1.  **Intercept**: The client application service attempts to communicate. Its traffic is intercepted locally by its dedicated Client Sidecar Proxy running on localhost.
2.  **Encapsulate & Authenticate**: The Client Proxy establishes a Mutual TLS (mTLS) handshake with the destination Server Sidecar Proxy, exchanging and validating x509 certificates.
3.  **Authorize**: The Server Proxy intercepts the request and queries the central Control Plane (Policy Engine) to verify if the client has permissions to access the resource.
4.  **Deliver**: If allowed, the Server Proxy decrypts the traffic and forwards it locally to the target application. If unauthorized, the connection is instantly dropped and logged.

---

## 🛠️ Tech Stack

*   **Data Plane (Proxies)**: Go (Golang) — leveraging `httputil` for optimized reverse proxying.
*   **Control Plane (Policy Engine)**: Python / FastAPI / SQLite.
*   **Telemetry Dashboard**: React / Tailwind CSS.
*   **Identity & Cryptography**: OpenSSL (x509 Certificates / RSA Keys).
*   **Deployment & Orchestration**: Docker & Docker-Compose.

---

## 🚀 Core Features

*   **Sidecar Proxy Pattern**: Application services do not handle security or networking; local, isolated sidecar proxies intercept and secure all ingress/egress TCP traffic automatically.
*   **Cryptographic mTLS Identity**: Employs certificates issued by a private, local Certificate Authority (CA) to cryptographically verify service identities.
*   **Dynamic Micro-Segmentation Control Plane**: A lightweight policy engine that dynamically evaluates connection requests against strict access control rules (e.g., *Service A -> Service B* is ALLOWED, but *Service C -> Service B* is DENIED).
*   **Real-time Telemetry & Observability**: A responsive web-based dashboard mapping active nodes, connection attempts, and blocked anomalous traffic in real-time.
*   **100% Software-Defined**: Fully containerized using Docker-Compose for instant local deployment with zero physical hardware dependencies.

---

## 📦 Project Directory Layout

```text
├── control-plane/       # Centralized policy engine, DB schemas, and Auth API
├── data-plane-proxy/    # Lightweight Go reverse proxy, mTLS configuration
├── mock-apps/           # Sample frontend/backend Python services for security testing
├── telemetry-dashboard/ # React web interface mapping live network traffic and attacks
├── certs/               # Scripting to generate and manage local CA and x509 certs
└── docker-compose.yml   # Multi-container orchestration config
```

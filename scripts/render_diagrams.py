import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

out_dir = r'C:\Users\karth\Downloads\Projects\Zero-Trust-Micro-Proxy\report-images\final'
os.makedirs(out_dir, exist_ok=True)

# Helper: Draw rounded box with larger text
def draw_box(ax, x, y, w, h, title, subtitle=None, bg_color="#e2e8f0", border_color="#64748b", text_color="#0f172a", title_size=13, sub_size=11, lw=2.0):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03", 
                                  linewidth=lw, edgecolor=border_color, facecolor=bg_color)
    ax.add_patch(rect)
    if subtitle:
        ax.text(x + w/2, y + h*0.64, title, ha="center", va="center", fontsize=title_size, fontweight="bold", color=text_color)
        ax.text(x + w/2, y + h*0.34, subtitle, ha="center", va="center", fontsize=sub_size, color=text_color)
    else:
        ax.text(x + w/2, y + h/2, title, ha="center", va="center", fontsize=title_size, fontweight="bold", color=text_color)

# Helper: Draw arrow with larger text
def draw_arrow(ax, x1, y1, x2, y2, label=None, color="#2563eb", lw=2.5, label_color="#1e293b", style="->", rad=0.0, ls="-", label_size=10.5):
    connectionstyle = f"arc3,rad={rad}" if rad != 0 else "arc3"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, linestyle=ls, color=color, lw=lw, connectionstyle=connectionstyle))
    if label:
        mx, my = (x1 + x2)/2, (y1 + y2)/2
        ax.text(mx, my + 0.02, label, ha="center", va="bottom", fontsize=label_size, fontweight="bold", color=label_color,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.0, alpha=0.95))

# ==============================================================================
# 1. FIG 1.1: Flat Network vs Zero-Trust Enforcement
# ==============================================================================
def render_fig_1_1():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.2), dpi=200)
    fig.patch.set_facecolor('#f8fafc')
    
    for ax in (ax1, ax2):
        ax.set_facecolor('#f8fafc')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
    # Left: Flat Network
    ax1.text(0.5, 0.94, "Flat Network (Perimeter Trust Model)", ha="center", va="center", fontsize=15, fontweight="bold", color="#b91c1c")
    ax1.text(0.5, 0.88, "Vulnerable: Hard Shell, Soft Interior", ha="center", va="center", fontsize=11, color="#64748b")
    
    border1 = patches.FancyBboxPatch((0.04, 0.06), 0.92, 0.78, boxstyle="round,pad=0.02", lw=2.5, ls="--", edgecolor="#dc2626", facecolor="#fef2f2")
    ax1.add_patch(border1)
    ax1.text(0.5, 0.78, "TRUSTED INTERNAL NETWORK (No Identity Checks)", ha="center", va="center", fontsize=11, fontweight="bold", color="#dc2626")
    
    draw_box(ax1, 0.08, 0.48, 0.24, 0.16, "Ingress API", "Port 80 / 443", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=11)
    draw_box(ax1, 0.38, 0.48, 0.24, 0.16, "Orders API", "127.0.0.1:9091", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=11)
    draw_box(ax1, 0.68, 0.48, 0.24, 0.16, "Payments API", "127.0.0.1:9092", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=11)
    draw_box(ax1, 0.38, 0.12, 0.24, 0.16, "Attacker / Probe", "Compromised Pod", bg_color="#fca5a5", border_color="#dc2626", title_size=13, sub_size=11)
    
    draw_arrow(ax1, 0.32, 0.56, 0.38, 0.56, "HTTP", color="#ea580c")
    draw_arrow(ax1, 0.62, 0.56, 0.68, 0.56, "HTTP", color="#ea580c")
    draw_arrow(ax1, 0.50, 0.28, 0.50, 0.48, "Lateral Jump", color="#dc2626", lw=3.0)
    draw_arrow(ax1, 0.62, 0.20, 0.80, 0.48, "Unrestricted Attack", color="#dc2626", lw=3.0, rad=-0.2)
    
    # Right: Zero-Trust Architecture
    ax2.text(0.5, 0.94, "Zero-Trust Architecture (ZetaShield)", ha="center", va="center", fontsize=15, fontweight="bold", color="#047857")
    ax2.text(0.5, 0.88, "Secure: Never Trust, Always Verify", ha="center", va="center", fontsize=11, color="#64748b")
    
    border2 = patches.FancyBboxPatch((0.04, 0.06), 0.92, 0.78, boxstyle="round,pad=0.02", lw=2.5, ls="--", edgecolor="#059669", facecolor="#ecfdf5")
    ax2.add_patch(border2)
    ax2.text(0.5, 0.78, "ISOLATED WORKLOAD FLEET (mTLS + PBAC)", ha="center", va="center", fontsize=11, fontweight="bold", color="#059669")
    
    draw_box(ax2, 0.08, 0.48, 0.24, 0.16, "Caller Service", "Frontend", bg_color="#bae6fd", border_color="#0284c7", title_size=13, sub_size=11)
    draw_box(ax2, 0.37, 0.40, 0.26, 0.28, "ZetaShield\nGateway", "L7 Data Plane\n:8443 (mTLS)", bg_color="#a7f3d0", border_color="#059669", title_size=14, sub_size=11)
    draw_box(ax2, 0.68, 0.58, 0.24, 0.16, "Orders API", "Isolated Bridge", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=11)
    draw_box(ax2, 0.68, 0.32, 0.24, 0.16, "Payments API", "Isolated Bridge", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=11)
    draw_box(ax2, 0.08, 0.12, 0.24, 0.16, "Attacker", "Rogue / Unknown", bg_color="#fca5a5", border_color="#dc2626", title_size=13, sub_size=11)
    
    draw_arrow(ax2, 0.32, 0.56, 0.37, 0.56, "mTLS + SPIFFE", color="#0284c7", lw=2.5)
    draw_arrow(ax2, 0.63, 0.58, 0.68, 0.66, "ALLOW (200)", color="#059669", lw=2.5)
    draw_arrow(ax2, 0.63, 0.48, 0.68, 0.40, "ALLOW (200)", color="#059669", lw=2.5)
    draw_arrow(ax2, 0.32, 0.20, 0.44, 0.40, "No Cert", color="#dc2626", lw=3.0)
    ax2.text(0.38, 0.29, "✕ TLS_REJECT", color="#dc2626", fontweight="bold", fontsize=10.5, bbox=dict(facecolor="#ffffff", edgecolor="#dc2626", boxstyle="round,pad=0.2"))
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "fig_1_1.png"), dpi=200)
    plt.close()
    print("Saved fig_1_1.png with larger fonts")

# ==============================================================================
# 2. FIG 1.2: Three-Version Design Evolution Timeline
# ==============================================================================
def render_fig_1_2():
    fig, ax = plt.subplots(figsize=(14, 5.5), dpi=200)
    fig.patch.set_facecolor('#f8fafc')
    ax.set_facecolor('#f8fafc')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')
    
    ax.text(5, 3.65, "ZetaShield Architectural Evolution Timeline (V0.1 → V1.0 → V2.0)", ha="center", va="center", fontsize=16, fontweight="bold", color="#0f172a")
    ax.text(5, 3.25, "Systematic Progression Informed by Formal Academic Review Feedback", ha="center", va="center", fontsize=11.5, color="#64748b")
    
    ax.plot([1.2, 8.8], [2.0, 2.0], color="#cbd5e1", lw=5, zorder=1)
    
    ax.plot(1.8, 2.0, marker="o", markersize=16, color="#3b82f6", zorder=2)
    draw_box(ax, 0.7, 0.3, 2.2, 1.4, "Phase 1: V0.1", "Jul–Aug 2026\n• 4-Hop Sidecar Prototype\n• Header-Based Identity\n• Single Backend Loopback\n• 14 Unit Tests", bg_color="#eff6ff", border_color="#3b82f6", text_color="#1e3a8a", title_size=13, sub_size=10.5)
    
    draw_box(ax, 3.2, 2.3, 2.0, 1.0, "Review 1 Critique", "Sep 2026\n• Too many proxy layers\n• Single service ≠ segmentation\n• Localhost only", bg_color="#fff1f2", border_color="#f43f5e", text_color="#9f1239", title_size=12, sub_size=10)
    ax.annotate("", xy=(4.2, 2.0), xytext=(4.2, 2.3), arrowprops=dict(arrowstyle="->", color="#f43f5e", lw=2.5))
    
    ax.plot(5.5, 2.0, marker="o", markersize=16, color="#10b981", zorder=2)
    draw_box(ax, 4.4, 0.3, 2.2, 1.4, "Phase 1: V1.0", "Oct 4–6, 2026\n• 2-Hop Gateway Consolidation\n• mTLS + X.509 SPIFFE SAN\n• Deny-by-Default (policy.yaml)\n• 0.60ms Latency Benchmark", bg_color="#ecfdf5", border_color="#10b981", text_color="#065f46", title_size=13, sub_size=10.5)
    
    ax.plot(8.2, 2.0, marker="o", markersize=16, color="#8b5cf6", zorder=2)
    draw_box(ax, 7.1, 0.3, 2.2, 1.4, "Phase 1: V2.0", "Oct 7, 2026\n• Docker Container Mesh\n• Network Namespace Isolation\n• 7 Adversarial Test Attacks\n• Zero-Downtime Hot-Reload", bg_color="#f5f3ff", border_color="#8b5cf6", text_color="#5b21b6", title_size=13, sub_size=10.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "fig_1_2.png"), dpi=200)
    plt.close()
    print("Saved fig_1_2.png with larger fonts")

# ==============================================================================
# 3. FIG 2.1: Istio Sidecar-Mesh vs Consolidated Gateway
# ==============================================================================
def render_fig_2_1():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=200)
    fig.patch.set_facecolor('#f8fafc')
    for ax in (ax1, ax2):
        ax.set_facecolor('#f8fafc')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
    ax1.text(0.5, 0.94, "Istio Sidecar-Mesh Model (4 Hops)", ha="center", va="center", fontsize=14, fontweight="bold", color="#475569")
    ax1.text(0.5, 0.88, "High Resource Footprint & Operational Complexity", ha="center", va="center", fontsize=10.5, color="#64748b")
    
    draw_box(ax1, 0.06, 0.45, 0.19, 0.24, "Pod A\n(App)", "Service A", bg_color="#e2e8f0", border_color="#64748b", title_size=12, sub_size=10.5)
    draw_box(ax1, 0.27, 0.45, 0.19, 0.24, "Sidecar A\n(Envoy)", "Local Proxy", bg_color="#fee2e2", border_color="#ef4444", title_size=12, sub_size=10.5)
    draw_box(ax1, 0.54, 0.45, 0.19, 0.24, "Sidecar B\n(Envoy)", "Local Proxy", bg_color="#fee2e2", border_color="#ef4444", title_size=12, sub_size=10.5)
    draw_box(ax1, 0.75, 0.45, 0.19, 0.24, "Pod B\n(App)", "Service B", bg_color="#e2e8f0", border_color="#64748b", title_size=12, sub_size=10.5)
    draw_box(ax1, 0.33, 0.10, 0.34, 0.22, "Control Plane (istiod)", "CA + Dynamic Policy Sync", bg_color="#f1f5f9", border_color="#94a3b8", title_size=12, sub_size=10)
    
    draw_arrow(ax1, 0.25, 0.57, 0.27, 0.57, "1", color="#64748b", lw=2)
    draw_arrow(ax1, 0.46, 0.57, 0.54, 0.57, "2 (mTLS)", color="#ef4444", lw=2.5)
    draw_arrow(ax1, 0.73, 0.57, 0.75, 0.57, "3", color="#64748b", lw=2)
    draw_arrow(ax1, 0.42, 0.32, 0.36, 0.45, color="#94a3b8", style="->", lw=1.5)
    draw_arrow(ax1, 0.58, 0.32, 0.64, 0.45, color="#94a3b8", style="->", lw=1.5)
    
    ax2.text(0.5, 0.94, "ZetaShield Consolidated Gateway (2 Hops)", ha="center", va="center", fontsize=14, fontweight="bold", color="#0284c7")
    ax2.text(0.5, 0.88, "Lightweight, Sub-Millisecond, Zero-Downtime Hot-Reload", ha="center", va="center", fontsize=10.5, color="#64748b")
    
    draw_box(ax2, 0.06, 0.45, 0.24, 0.24, "Calling Service\n(Frontend)", "Client Cert", bg_color="#bae6fd", border_color="#0284c7", title_size=13, sub_size=11)
    draw_box(ax2, 0.36, 0.34, 0.28, 0.46, "ZetaShield Gateway\n(:8443)", "• mTLS Termination\n• SPIFFE Extraction\n• Embedded PBAC\n• JSONL Audit Sink", bg_color="#d1fae5", border_color="#059669", title_size=14, sub_size=11)
    draw_box(ax2, 0.70, 0.60, 0.24, 0.22, "Orders API\n(:9091)", "Isolated", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=11)
    draw_box(ax2, 0.70, 0.32, 0.24, 0.22, "Payments API\n(:9092)", "Isolated", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=11)
    
    draw_arrow(ax2, 0.30, 0.57, 0.36, 0.57, "Hop 1: mTLS", color="#0284c7", lw=2.5)
    draw_arrow(ax2, 0.64, 0.62, 0.70, 0.71, "Hop 2: HTTP", color="#059669", lw=2.5)
    draw_arrow(ax2, 0.64, 0.48, 0.70, 0.43, "Hop 2: HTTP", color="#059669", lw=2.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "fig_2_1.png"), dpi=200)
    plt.close()
    print("Saved fig_2_1.png with larger fonts")

# ==============================================================================
# 4. FIG 3.1 & 4.1: System Context & Two-Hop Architecture
# ==============================================================================
def render_fig_3_1():
    fig, ax = plt.subplots(figsize=(13, 6.5), dpi=200)
    fig.patch.set_facecolor('#f8fafc')
    ax.set_facecolor('#f8fafc')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    ax.text(5, 5.65, "ZetaShield System Context Diagram", ha="center", va="center", fontsize=16, fontweight="bold", color="#0f172a")
    ax.text(5, 5.25, "Interaction Boundaries Across Services, PKI, Security Policy, and Audit Streams", ha="center", va="center", fontsize=11, color="#64748b")
    
    draw_box(ax, 0.5, 3.6, 2.2, 1.3, "Authorized Clients", "Frontend / Payments\n(Present CA-Signed Cert)", bg_color="#eff6ff", border_color="#3b82f6", title_size=13, sub_size=10.5)
    draw_box(ax, 0.5, 1.5, 2.2, 1.3, "Unauthorized Callers", "Anonymous / Rogue CA\n(Attack Simulations)", bg_color="#fff1f2", border_color="#f43f5e", title_size=13, sub_size=10.5)
    
    draw_box(ax, 3.6, 1.7, 2.8, 3.2, "ZetaShield L7 Gateway", "• mTLS Termination (TLS 1.2+)\n• SPIFFE SAN Identity Extraction\n• Deny-by-Default Policy Engine\n• Longest-Prefix Reverse Proxy\n• Fail-Closed Error Handler\n• Zero-Downtime Hot-Reload", bg_color="#ecfdf5", border_color="#10b981", title_size=14, sub_size=10.5)
    
    draw_box(ax, 7.3, 3.6, 2.2, 1.3, "Orders Backend", "Internal Port 9091\n(Zero Host Ports)", bg_color="#fef3c7", border_color="#f59e0b", title_size=13, sub_size=10.5)
    draw_box(ax, 7.3, 1.5, 2.2, 1.3, "Payments Backend", "Internal Port 9092\n(Zero Host Ports)", bg_color="#fef3c7", border_color="#f59e0b", title_size=13, sub_size=10.5)
    
    draw_box(ax, 3.6, 0.2, 2.8, 1.1, "Root Certificate Authority", "4096-bit RSA (certs/ca.pem)", bg_color="#f3e8ff", border_color="#a855f7", title_size=12, sub_size=10)
    draw_box(ax, 7.3, 0.2, 2.2, 1.1, "Audit Ledger", "audit.log.jsonl", bg_color="#e2e8f0", border_color="#64748b", title_size=12, sub_size=10)
    
    draw_arrow(ax, 2.7, 4.25, 3.6, 4.0, "mTLS (:8443)", color="#3b82f6", lw=2.5)
    draw_arrow(ax, 2.7, 2.15, 3.6, 2.6, "mTLS (:8443)", color="#f43f5e", lw=2.5)
    draw_arrow(ax, 6.4, 4.0, 7.3, 4.25, "HTTP 200", color="#10b981", lw=2.5)
    draw_arrow(ax, 6.4, 2.8, 7.3, 2.15, "HTTP 200", color="#10b981", lw=2.5)
    draw_arrow(ax, 5.0, 1.7, 5.0, 1.3, color="#a855f7", style="<->", lw=2)
    draw_arrow(ax, 6.4, 2.0, 7.3, 0.8, "JSONL Sink", color="#64748b", lw=2)
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "fig_3_1.png"), dpi=200)
    plt.savefig(os.path.join(out_dir, "fig_4_1.png"), dpi=200)
    plt.close()
    print("Saved fig_3_1.png and fig_4_1.png with larger fonts")

# ==============================================================================
# 5. FIG 4.2: Request Lifecycle Sequence Diagram
# ==============================================================================
def render_fig_4_2():
    fig, ax = plt.subplots(figsize=(13.5, 7.5), dpi=200)
    fig.patch.set_facecolor('#f8fafc')
    ax.set_facecolor('#f8fafc')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    ax.text(5, 9.65, "Request Lifecycle Sequence Diagram (Three-Checkpoint Pipeline)", ha="center", va="center", fontsize=15, fontweight="bold", color="#0f172a")
    
    cols = [1.2, 3.6, 6.1, 8.6]
    names = ["Calling Service", "TLS Ingress (CP-1)", "Policy Engine (CP-2)", "Reverse Proxy / Backend (CP-3)"]
    for c, n in zip(cols, names):
        draw_box(ax, c-1.0, 8.5, 2.0, 0.7, n, bg_color="#e2e8f0", border_color="#475569", title_size=10.5)
        ax.plot([c, c], [0.6, 8.5], color="#cbd5e1", ls="--", lw=2.0)
        
    events = [
        (7.8, 1.2, 3.6, "1. Client Hello + Certificate Presentation", "#2563eb", "->"),
        (7.1, 3.6, 1.2, "   [Fail] Untrusted CA / No Cert -> TLS_REJECT (Drop)", "#dc2626", "-->"),
        (6.4, 3.6, 6.1, "2. Valid Handshake -> Extract SPIFFE SAN Identity", "#059669", "->"),
        (5.7, 6.1, 6.1, "   Evaluate (Identity x Path x Method) vs policy.yaml", "#475569", "-"),
        (5.0, 6.1, 1.2, "   [Fail] No Match -> HTTP 403 Forbidden (Deny-by-Default)", "#dc2626", "-->"),
        (4.2, 6.1, 8.6, "3. Match ALLOW Rule -> Longest-Prefix Routing", "#059669", "->"),
        (3.4, 8.6, 8.6, "   Forward HTTP Request to Private Backend Port", "#d97706", "-"),
        (2.6, 8.6, 1.2, "   [Fail] Upstream Crash -> HTTP 503 (Fail-Closed)", "#dc2626", "-->"),
        (1.8, 8.6, 1.2, "   [Success] Backend Response -> Stream HTTP 200 OK", "#059669", "-->"),
        (1.0, 3.6, 3.6, "4. Write Synchronous Structured Record to audit.log.jsonl", "#475569", "-"),
    ]
    
    for y, x1, x2, label, color, style in events:
        if x1 == x2:
            ax.text(x1 + 0.15, y, label, ha="left", va="center", fontsize=9.5, color=color, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.0))
        else:
            ls = "--" if "--" in style else "-"
            ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->", linestyle=ls, color=color, lw=2.2))
            mx = (x1 + x2)/2
            ax.text(mx, y + 0.22, label, ha="center", va="bottom", fontsize=9.5, color=color, fontweight="bold")
            
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "fig_4_2.png"), dpi=200)
    plt.close()
    print("Saved fig_4_2.png with larger fonts")

# ==============================================================================
# 6. FIG 4.3: Docker Compose Network Topology
# ==============================================================================
def render_fig_4_3():
    fig, ax = plt.subplots(figsize=(13, 6.5), dpi=200)
    fig.patch.set_facecolor('#f8fafc')
    ax.set_facecolor('#f8fafc')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    ax.text(5, 5.65, "Docker Compose Network Topology (zeta-net Bridge Isolation)", ha="center", va="center", fontsize=15, fontweight="bold", color="#0f172a")
    
    host = patches.FancyBboxPatch((0.4, 0.3), 9.2, 5.0, boxstyle="round,pad=0.03", lw=2.5, edgecolor="#64748b", facecolor="#f1f5f9")
    ax.add_patch(host)
    ax.text(0.7, 5.0, "HOST MACHINE (Developer / Production Host)", fontsize=12, fontweight="bold", color="#475569")
    
    bridge = patches.FancyBboxPatch((3.4, 0.7), 5.8, 4.0, boxstyle="round,pad=0.03", lw=2.5, ls="--", edgecolor="#0284c7", facecolor="#e0f2fe")
    ax.add_patch(bridge)
    ax.text(6.3, 4.4, "ISOLATED DOCKER BRIDGE: zeta-net (172.21.0.0/16)", ha="center", fontsize=11.5, fontweight="bold", color="#0369a1")
    
    draw_box(ax, 0.8, 2.4, 2.1, 1.4, "External Caller /\nTest Client", "Runs on Host OS\nCalls https://127.0.0.1:8443", bg_color="#ffffff", border_color="#94a3b8", title_size=12, sub_size=10)
    draw_box(ax, 3.7, 2.0, 2.0, 2.1, "zeta-gateway", "Port 8443:8443\n(ONLY published port\non host)", bg_color="#dcfce7", border_color="#16a34a", title_size=13, sub_size=10.5)
    
    draw_box(ax, 6.7, 3.0, 2.2, 1.3, "zeta-orders", "Internal :9091\nNO HOST PORTS", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=10.5)
    draw_box(ax, 6.7, 1.1, 2.2, 1.3, "zeta-payments", "Internal :9092\nNO HOST PORTS", bg_color="#fed7aa", border_color="#ea580c", title_size=13, sub_size=10.5)
    
    draw_arrow(ax, 2.9, 3.1, 3.7, 3.1, "mTLS :8443", color="#0284c7", lw=2.8)
    draw_arrow(ax, 5.7, 3.3, 6.7, 3.65, "http://orders:9091", color="#16a34a", lw=2.5)
    draw_arrow(ax, 5.7, 2.8, 6.7, 1.75, "http://payments:9092", color="#16a34a", lw=2.5)
    
    draw_arrow(ax, 2.9, 2.6, 6.7, 3.3, "curl :9091", color="#dc2626", lw=2.5, ls="--", rad=-0.2)
    ax.text(4.7, 1.4, "✕ Connection Refused (Bypass Impossible)", color="#dc2626", fontweight="bold", fontsize=10, bbox=dict(facecolor="#ffffff", edgecolor="#dc2626", boxstyle="round,pad=0.25"))
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "fig_4_3.png"), dpi=200)
    plt.close()
    print("Saved fig_4_3.png with larger fonts")

# ==============================================================================
# 7. FIG 6.1: Real-World Fintech Deployment Scenario
# ==============================================================================
def render_fig_6_1():
    fig, ax = plt.subplots(figsize=(13.5, 6.5), dpi=200)
    fig.patch.set_facecolor('#f8fafc')
    ax.set_facecolor('#f8fafc')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    ax.text(5, 5.65, "Real-World Deployment Scenario: Enterprise Fintech Microservice Mesh", ha="center", va="center", fontsize=15, fontweight="bold", color="#0f172a")
    ax.text(5, 5.25, "Enforcing PCI-DSS Least-Privilege Segmentation and Cryptographic Traceability", ha="center", va="center", fontsize=11, color="#64748b")
    
    draw_box(ax, 0.5, 2.3, 2.2, 1.7, "Public Ingress /\nFrontend Pods", "User-Facing Web & Mobile\nspiffe://.../frontend-service", bg_color="#eff6ff", border_color="#3b82f6", title_size=13, sub_size=10.5)
    
    draw_box(ax, 3.6, 1.3, 2.8, 3.6, "ZetaShield L7 Gateway", "• Terminates Internal mTLS\n• Enforces Declarative PBAC\n• Denies Cross-Tenant Lateral Access\n• Synchronous SIEM Audit Output", bg_color="#d1fae5", border_color="#059669", title_size=14, sub_size=11)
    
    draw_box(ax, 7.3, 3.8, 2.3, 1.3, "Account & Profile API", "Zone A: Read Operations\nMethods: [GET]", bg_color="#fef3c7", border_color="#f59e0b", title_size=13, sub_size=10.5)
    draw_box(ax, 7.3, 2.3, 2.3, 1.3, "Payments & Transfer API", "Zone B: PCI-DSS Restricted\nMethods: [POST]", bg_color="#fee2e2", border_color="#ef4444", title_size=13, sub_size=10.5)
    draw_box(ax, 7.3, 0.8, 2.3, 1.3, "Core Ledger & DB", "Zone C: High-Assurance\nMethods: [PUT, POST]", bg_color="#fee2e2", border_color="#ef4444", title_size=13, sub_size=10.5)
    
    draw_arrow(ax, 2.7, 3.15, 3.6, 3.15, "Mutual TLS\n(SPIFFE URI)", color="#3b82f6", lw=2.8)
    draw_arrow(ax, 6.4, 3.5, 7.3, 4.45, "ALLOW: GET", color="#059669", lw=2.5)
    draw_arrow(ax, 6.4, 3.1, 7.3, 2.95, "ALLOW: POST", color="#059669", lw=2.5)
    draw_arrow(ax, 6.4, 2.7, 7.3, 1.45, "DENY: Lateral Jump ✕", color="#dc2626", lw=2.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "fig_6_1.png"), dpi=200)
    plt.close()
    print("Saved fig_6_1.png with larger fonts")

if __name__ == "__main__":
    render_fig_1_1()
    render_fig_1_2()
    render_fig_2_1()
    render_fig_3_1()
    render_fig_4_2()
    render_fig_4_3()
    render_fig_6_1()
    print("All architecture diagrams re-rendered with larger, bolder typography!")

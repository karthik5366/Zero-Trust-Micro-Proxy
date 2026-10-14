import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

out_dir = r'C:\Users\karth\Downloads\Projects\Zero-Trust-Micro-Proxy\report-images\final'

def draw_box(ax, x, y, w, h, title, subtitle=None, bg_color="#e2e8f0", border_color="#64748b", text_color="#0f172a", title_size=13, sub_size=11, lw=2.0):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03", 
                                  linewidth=lw, edgecolor=border_color, facecolor=bg_color)
    ax.add_patch(rect)
    if subtitle:
        ax.text(x + w/2, y + h*0.64, title, ha="center", va="center", fontsize=title_size, fontweight="bold", color=text_color)
        ax.text(x + w/2, y + h*0.34, subtitle, ha="center", va="center", fontsize=sub_size, color=text_color)
    else:
        ax.text(x + w/2, y + h/2, title, ha="center", va="center", fontsize=title_size, fontweight="bold", color=text_color)

def draw_arrow(ax, x1, y1, x2, y2, label=None, color="#2563eb", lw=2.5, label_color="#1e293b", style="->", rad=0.0, ls="-", label_size=10.5):
    connectionstyle = f"arc3,rad={rad}" if rad != 0 else "arc3"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, linestyle=ls, color=color, lw=lw, connectionstyle=connectionstyle))
    if label:
        mx, my = (x1 + x2)/2, (y1 + y2)/2
        ax.text(mx, my + 0.02, label, ha="center", va="bottom", fontsize=label_size, fontweight="bold", color=label_color,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.0, alpha=0.95))

fig, ax = plt.subplots(figsize=(13, 6.5), dpi=200)
fig.patch.set_facecolor('#f8fafc')
ax.set_facecolor('#f8fafc')
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

ax.text(5, 5.65, "V2.0 Consolidated Two-Hop Gateway Architecture", ha="center", va="center", fontsize=16, fontweight="bold", color="#0f172a")
ax.text(5, 5.25, "Consolidation of V0.1 4-Hop Chain into High-Performance L7 Ingress Gateway Hub", ha="center", va="center", fontsize=11, color="#64748b")

draw_box(ax, 0.5, 3.6, 2.2, 1.3, "Calling Services", "frontend-service\norders-service\n(mTLS + SPIFFE SVID)", bg_color="#eff6ff", border_color="#3b82f6", title_size=13, sub_size=10.5)
draw_box(ax, 0.5, 1.5, 2.2, 1.3, "Attacker Workload", "No Cert / Rogue CA\n(Handshake Rejection)", bg_color="#fff1f2", border_color="#f43f5e", title_size=13, sub_size=10.5)

draw_box(ax, 3.6, 1.7, 2.8, 3.2, "ZetaShield Gateway\n(:8443)", "• TLS Handshake & SAN Extractor\n• Embedded PBAC Engine\n• Longest-Prefix Router\n• Fail-Closed Error Handler\n• Zero-Downtime Hot-Reload", bg_color="#ecfdf5", border_color="#10b981", title_size=14, sub_size=10.5)

draw_box(ax, 7.3, 3.6, 2.2, 1.3, "Orders Backend", "Private Port :9091\n(Zero Host Ports)", bg_color="#fef3c7", border_color="#f59e0b", title_size=13, sub_size=10.5)
draw_box(ax, 7.3, 1.5, 2.2, 1.3, "Payments Backend", "Private Port :9092\n(Zero Host Ports)", bg_color="#fef3c7", border_color="#f59e0b", title_size=13, sub_size=10.5)

draw_box(ax, 3.6, 0.2, 2.8, 1.1, "Declarative Policy Engine", "policy.yaml (Deny-by-Default)", bg_color="#f3e8ff", border_color="#a855f7", title_size=12, sub_size=10)
draw_box(ax, 7.3, 0.2, 2.2, 1.1, "Synchronous Audit Sink", "audit.log.jsonl", bg_color="#e2e8f0", border_color="#64748b", title_size=12, sub_size=10)

draw_arrow(ax, 2.7, 4.25, 3.6, 4.0, "Hop 1: mTLS (:8443)", color="#3b82f6", lw=2.5)
draw_arrow(ax, 2.7, 2.15, 3.6, 2.6, "Hop 1: mTLS", color="#f43f5e", lw=2.5)
draw_arrow(ax, 6.4, 4.0, 7.3, 4.25, "Hop 2: HTTP (:9091)", color="#10b981", lw=2.5)
draw_arrow(ax, 6.4, 2.8, 7.3, 2.15, "Hop 2: HTTP (:9092)", color="#10b981", lw=2.5)
draw_arrow(ax, 5.0, 1.7, 5.0, 1.3, color="#a855f7", style="<->", lw=2)
draw_arrow(ax, 6.4, 2.0, 7.3, 0.8, "Append-Only Log", color="#64748b", lw=2)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_4_1.png"), dpi=200)
plt.close()
print("Saved custom fig_4_1.png successfully!")

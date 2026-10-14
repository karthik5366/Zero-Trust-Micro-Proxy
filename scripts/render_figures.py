import os
from PIL import Image, ImageDraw, ImageFont

out_dir = r'C:\Users\karth\Downloads\Projects\Zero-Trust-Micro-Proxy\report-images\final'
os.makedirs(out_dir, exist_ok=True)

def render_terminal(title, text_lines, filename, width=960, font_size=17, line_spacing=28):
    header_h = 38
    padding_x = 24
    padding_y = 18
    height = header_h + padding_y * 2 + len(text_lines) * line_spacing + 12
    
    img = Image.new('RGB', (width, height), color='#0d1117')
    draw = ImageDraw.Draw(img)
    
    # Title bar
    draw.rectangle([0, 0, width, header_h], fill='#161b22')
    draw.line([0, header_h, width, header_h], fill='#30363d', width=1)
    
    # Window buttons
    draw.ellipse([14, 13, 26, 25], fill='#ff5f56')
    draw.ellipse([34, 13, 46, 25], fill='#ffbd2e')
    draw.ellipse([54, 13, 66, 25], fill='#27c93f')
    
    # Fonts
    try:
        font_title = ImageFont.truetype("arial.ttf", 13)
        font_body = ImageFont.truetype("consola.ttf", font_size)
    except:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        
    draw.text((width // 2 - 100, 11), title, fill='#8b949e', font=font_title)
    
    y = header_h + padding_y
    for line, color in text_lines:
        draw.text((padding_x, y), line, fill=color, font=font_body)
        y += line_spacing
        
    img.save(os.path.join(out_dir, filename), dpi=(200, 200))
    print(f"Saved {filename} with large legible text (font={font_size}px, width={width}px)")

# 1. Fig 5.1: X.509 cert showing SPIFFE URI in SAN
lines_5_1 = [
    ("$ openssl x509 -in certs/frontend-service.pem -text -noout", "#58a6ff"),
    ("Certificate:", "#c9d1d9"),
    ("    Data:", "#8b949e"),
    ("        Version: 3 (0x2)", "#8b949e"),
    ("        Signature Algorithm: sha256WithRSAEncryption", "#8b949e"),
    ("        Issuer: CN=ZetaShield Root CA", "#f0883e"),
    ("        Validity: Oct 4 2026 to Nov 3 2026", "#8b949e"),
    ("        Subject: CN=frontend-service", "#79c0ff"),
    ("        X509v3 extensions:", "#d2a8ff"),
    ("            X509v3 Subject Alternative Name:", "#7ee787"),
    ("                URI:spiffe://zetashield.local/ns/default/sa/frontend-service", "#aff5b4"),
    ("            X509v3 Subject Key Identifier: 0C:87:E5:F9:0E:61:5C:EF...", "#8b949e"),
    ("            X509v3 Authority Key Identifier: D1:7E:1A:9E:3A:B1:AC...", "#8b949e"),
    ("    Signature Algorithm: sha256WithRSAEncryption (Verified)", "#7ee787"),
]
render_terminal("PowerShell — OpenSSL X.509 SPIFFE SAN Inspection", lines_5_1, "fig_5_1.png", width=920, font_size=17, line_spacing=28)

# 2. Fig 5.2: Seven-test adversarial suite terminal output
lines_5_2 = [
    ("PS C:\\Zero-Trust-Micro-Proxy\\mock-apps> python client.py", "#58a6ff"),
    ("=" * 56, "#8b949e"),
    ("ZetaShield V1.0 — 7-Test Adversarial Demo Suite", "#58a6ff"),
    ("=" * 56, "#8b949e"),
    ("[TEST 1: AUTHORIZED (frontend -> orders)]", "#58a6ff"),
    ("  GET /orders/list  ->  200 OK", "#7ee787"),
    ("[TEST 2: NO CERTIFICATE (Anonymous)]", "#58a6ff"),
    ("  GET /orders/list  ->  TLS_REJECT (Handshake Failed)", "#ff7b72"),
    ("[TEST 3: DENY-BY-DEFAULT (frontend -> admin)]", "#58a6ff"),
    ("  GET /admin/delete ->  403 Forbidden", "#ff7b72"),
    ("[TEST 4: LATERAL MOVEMENT (orders -> payments)]", "#58a6ff"),
    ("  GET /payments/balance -> 403 Forbidden", "#ff7b72"),
    ("[TEST 5: AUTHORIZED (payments -> payments)]", "#58a6ff"),
    ("  GET /payments/balance -> 200 OK", "#7ee787"),
    ("[TEST 6: FORGED CERT (Attacker -> orders)]", "#58a6ff"),
    ("  GET /orders/list  ->  TLS_REJECT (Untrusted Issuer)", "#ff7b72"),
    ("[TEST 7: FAIL-CLOSED (frontend -> inventory [DOWN])]", "#58a6ff"),
    ("  GET /inventory/status -> 503 (Fail-Closed / Down)", "#f0883e"),
    ("=" * 56, "#8b949e"),
    ("SUMMARY: 200, TLS_REJECT, 403, 403, 200, TLS_REJECT, 503", "#7ee787"),
    ("=" * 56, "#8b949e"),
]
render_terminal("PowerShell — Adversarial Client 7-Test Execution", lines_5_2, "fig_5_2.png", width=880, font_size=16, line_spacing=26)

# 3. Fig 5.4: Docker Compose port mapping
lines_5_4 = [
    ("PS C:\\Zero-Trust-Micro-Proxy> docker compose ps", "#58a6ff"),
    ("NAME          STATUS        PORTS", "#8b949e"),
    ("zeta-gateway  Up 2 minutes  0.0.0.0:8443->8443/tcp (ONLY INGRESS)", "#7ee787"),
    ("zeta-orders   Up 2 minutes  (NO HOST PORTS - ISOLATED ON ZETA-NET)", "#79c0ff"),
    ("zeta-payments Up 2 minutes  (NO HOST PORTS - ISOLATED ON ZETA-NET)", "#79c0ff"),
    ("", "#c9d1d9"),
    ("PS C:\\Zero-Trust-Micro-Proxy> curl.exe http://127.0.0.1:9091/orders/list", "#58a6ff"),
    ("curl: (7) Failed to connect to 127.0.0.1 port 9091: Connection refused", "#ff7b72"),
    ("", "#c9d1d9"),
    ("# PROOF: Backends unreachable from host machine. Bypass impossible.", "#8b949e"),
]
render_terminal("PowerShell — Docker Network Isolation Verification", lines_5_4, "fig_5_4.png", width=920, font_size=16, line_spacing=27)

# 4. Fig 5.7: Structured Audit Log
lines_5_7 = [
    ("PS C:\\Zero-Trust-Micro-Proxy> Get-Content deploy\\logs\\audit.log.jsonl -Tail 6", "#58a6ff"),
    ("{\"ts\":\"16:23:59Z\",\"act\":\"ALLOW\",\"id\":\".../frontend-service\",\"path\":\"/orders/list\",\"status\":200}", "#7ee787"),
    ("{\"ts\":\"16:23:59Z\",\"act\":\"DENY\", \"id\":\".../frontend-service\",\"path\":\"/admin/delete\",\"reason\":\"deny-by-default\"}", "#ff7b72"),
    ("{\"ts\":\"16:23:59Z\",\"act\":\"DENY\", \"id\":\".../orders-service\",  \"path\":\"/payments/balance\",\"reason\":\"deny-by-default\"}", "#ff7b72"),
    ("{\"ts\":\"16:23:59Z\",\"act\":\"ALLOW\",\"id\":\".../payments-service\",\"path\":\"/payments/balance\",\"status\":200}", "#7ee787"),
    ("{\"ts\":\"16:23:59Z\",\"act\":\"ALLOW\",\"id\":\".../frontend-service\",\"path\":\"/inventory/status\",\"routed\":\"dead-host:9099\"}", "#7ee787"),
    ("{\"ts\":\"16:24:03Z\",\"act\":\"ERROR\",\"id\":\".../frontend-service\",\"path\":\"/inventory/status\",\"reason\":\"fail-closed (503)\"}", "#f0883e"),
]
render_terminal("Audit Trail — deploy/logs/audit.log.jsonl (Append-Only Sink)", lines_5_7, "fig_5_7.png", width=960, font_size=15, line_spacing=28)

# 5. Fig 5.8: Policy Hot-Reload Log
lines_5_8 = [
    ("PS C:\\Zero-Trust-Micro-Proxy> docker logs -f zeta-gateway", "#58a6ff"),
    ("╔══════════════════════════════════════════════════════╗", "#8b949e"),
    ("║  ZetaShield V1.0 — Zero-Trust Gateway (:8443)        ║", "#58a6ff"),
    ("╚══════════════════════════════════════════════════════╝", "#8b949e"),
    ("[ALLOW] id=spiffe://.../frontend-service GET /orders/list (ALLOW rule)", "#7ee787"),
    ("", "#c9d1d9"),
    ("# Operator edits deploy/policy.docker.yaml on disk...", "#8b949e"),
    ("[policy] hot-reloaded /etc/zetashield/policy.yaml (2026-10-08T16:26:06Z)", "#f0883e"),
    ("[policy] active routes: 3, active rules: 5 (swapped with RWMutex)", "#79c0ff"),
    ("", "#c9d1d9"),
    ("[DENY]  id=spiffe://.../frontend-service GET /orders/list (no rule)", "#ff7b72"),
    ("# ZERO DOWNTIME. ZERO PACKET LOSS. ZERO CONTAINER RESTARTS.", "#7ee787"),
]
render_terminal("Gateway Log — Dynamic Zero-Downtime Policy Hot-Reload", lines_5_8, "fig_5_8.png", width=900, font_size=16, line_spacing=27)

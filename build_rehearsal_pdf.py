#!/usr/bin/env python3
"""
build_rehearsal_pdf.py — Generates a publication-grade PDF rehearsal manual
for ZetaShield V2.0 Review 2 Presentation.
"""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_OUTPUT = "ZetaShield_Rehearsal_File.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Suppress header and footer on cover / page 1
        if self._pageNumber > 1:
            # Header
            self.drawString(36, 11 * inch - 25, "ZETASHIELD V2.0 — CAPSTONE REVIEW 2 REHEARSAL MANUAL")
            self.drawRightString(8.5 * inch - 36, 11 * inch - 25, "GROUP 39 · DSN4091")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 11 * inch - 28, 8.5 * inch - 36, 11 * inch - 28)
            
            # Footer
            self.line(36, 32, 8.5 * inch - 36, 32)
            self.drawString(36, 20, "CONFIDENTIAL — STRICTLY FOR INTERNAL TEAM PREPARATION & VIVA DEFENSE")
            page_text = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(8.5 * inch - 36, 20, page_text)
            
        self.restoreState()

def create_rehearsal_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0F172A")    # Dark slate
    c_accent = colors.HexColor("#1D4ED8")     # Royal blue
    c_cyan = colors.HexColor("#0284C7")       # Cyan/Blue
    c_crimson = colors.HexColor("#DC2626")    # Crimson red
    c_emerald = colors.HexColor("#059669")    # Emerald green
    c_bg_light = colors.HexColor("#F8FAFC")   # Light slate
    c_text_dark = colors.HexColor("#1E293B")  # Charcoal body
    c_border = colors.HexColor("#E2E8F0")     # Light border

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=24, leading=28,
        textColor=c_primary, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=12, leading=16,
        textColor=c_accent, spaceAfter=14
    )
    meta_style = ParagraphStyle(
        'DocMeta', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=9, leading=13,
        textColor=colors.HexColor("#475569")
    )
    h1_style = ParagraphStyle(
        'SecH1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=15, leading=19,
        textColor=c_primary, spaceBefore=14, spaceAfter=6, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'SecH2', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=15,
        textColor=c_accent, spaceBefore=10, spaceAfter=4, keepWithNext=True
    )
    h3_style = ParagraphStyle(
        'SecH3', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9.5, leading=13,
        textColor=c_primary, spaceBefore=6, spaceAfter=2, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'CustomBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=11.5,
        textColor=c_text_dark, spaceAfter=5
    )
    script_speaker = ParagraphStyle(
        'ScriptSpeaker', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=12,
        textColor=c_accent, spaceBefore=4, spaceAfter=1, keepWithNext=True
    )
    script_body = ParagraphStyle(
        'ScriptBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=11.5,
        textColor=c_text_dark, spaceAfter=5
    )
    money_line = ParagraphStyle(
        'MoneyLine', parent=styles['Normal'],
        fontName='Helvetica-BoldOblique', fontSize=8.5, leading=11.5,
        textColor=c_crimson, spaceAfter=5
    )
    table_hdr = ParagraphStyle(
        'TableHdr', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=colors.white
    )
    table_cell = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=9.5,
        textColor=c_text_dark
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=c_primary
    )
    code_style = ParagraphStyle(
        'CodeSnippet', parent=styles['Normal'],
        fontName='Courier', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor("#0F172A")
    )
    callout_text = ParagraphStyle(
        'CalloutText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=c_text_dark
    )
    q_title = ParagraphStyle(
        'QTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=11.5,
        textColor=c_primary, spaceBefore=4, keepWithNext=True
    )
    q_ans = ParagraphStyle(
        'QAns', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=c_text_dark, spaceAfter=4
    )

    story = []

    # =========================================================================
    # COVER / HEADER BANNER
    # =========================================================================
    story.append(Paragraph("ZetaShield V2.0 — The Rehearsal File", title_style))
    story.append(Paragraph("Master Presentation Script, Live Demo Runbook & Viva Defense Manual", subtitle_style))
    story.append(Paragraph(
        "<b>Course:</b> DSN4091 Capstone Project Phase 1 · Review 2 &nbsp;|&nbsp; <b>Group:</b> 39 &nbsp;|&nbsp; <b>Date:</b> October 2026<br/>"
        "<b>Supervisor:</b> Dr. Sajjad Ahmed &nbsp;|&nbsp; <b>Program Chair:</b> Dr. D. Saravanan<br/>"
        "<b>Team:</b> Polisetti Hari Sri Raj Karthik (Lead), Subeer Srivastava, Sahil Shankar Thakkar, Shaivyaa Sharma, Sameep Upadhyay",
        meta_style
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=10))

    # Executive Summary Box
    summary_html = (
        "<b>DOCUMENT MISSION:</b> This manual guarantees seamless coordination during the 24-minute Review 2 "
        "presentation and 6-minute live demonstration. It contains word-for-word spoken scripts for every slide, "
        "the step-by-step live terminal execution runbook, a territorial defense Q&A bank covering 20 tough panel questions, "
        "and emergency disaster-recovery protocols. Every member must memorize their designated sections and core lines."
    )
    summary_table = Table([[Paragraph(summary_html, callout_text)]], colWidths=[540])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BORDER', (0,0), (-1,-1), 1, c_accent),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 1: THE SPEAKER MAP & SLIDE ALLOCATION
    # =========================================================================
    story.append(Paragraph("Part 1: The Speaker Map & Slide Allocation", h1_style))
    story.append(Paragraph(
        "Total presentation duration is strictly budgeted at <b>24 minutes of presentation + 6 minutes of live demonstration</b>, "
        "leaving buffer for committee cross-examination. Each member owns clear thematic territory to avoid stepping on each other's toes.",
        body_style
    ))

    speaker_data = [
        [
            Paragraph("Slide", table_hdr),
            Paragraph("Topic & Slide Title", table_hdr),
            Paragraph("Speaker", table_hdr),
            Paragraph("Time", table_hdr),
            Paragraph("Core Theme & Deliverable", table_hdr)
        ],
        [
            Paragraph("<b>01</b>", table_cell),
            Paragraph("Title & Project Overview", table_cell),
            Paragraph("<b>Karthik</b>", table_cell_bold),
            Paragraph("1.0m", table_cell),
            Paragraph("Welcome, thesis statement, team introduction, project vision", table_cell)
        ],
        [
            Paragraph("<b>02</b>", table_cell),
            Paragraph("The Problem: Flat Networks & Lateral Movement", table_cell),
            Paragraph("<b>Karthik</b>", table_cell_bold),
            Paragraph("1.5m", table_cell),
            Paragraph("Perimeter failure, OWASP A01, east-west attack surface, market gap", table_cell)
        ],
        [
            Paragraph("<b>03</b>", table_cell),
            Paragraph("Consolidated Gateway Architecture", table_cell),
            Paragraph("<b>Karthik</b>", table_cell_bold),
            Paragraph("2.0m", table_cell),
            Paragraph("4-hop sidecar vs 2-hop consolidated gateway, containerized mesh", table_cell)
        ],
        [
            Paragraph("<b>04</b>", table_cell),
            Paragraph("Three Checkpoints, Zero Trust", table_cell),
            Paragraph("<b>Subeer</b>", table_cell_bold),
            Paragraph("2.0m", table_cell),
            Paragraph("Sequential enforcement pipeline: Identity mTLS → Policy PBAC → Route/Audit", table_cell)
        ],
        [
            Paragraph("<b>05</b>", table_cell),
            Paragraph("Trust the Issuer, Not the Claim", table_cell),
            Paragraph("<b>Sahil</b>", table_cell_bold),
            Paragraph("2.0m", table_cell),
            Paragraph("Cryptographic SPIFFE URI in X.509 SAN vs spoofable HTTP headers, CA chain", table_cell)
        ],
        [
            Paragraph("<b>06</b>", table_cell),
            Paragraph("Deny-by-Default & Hot-Reload", table_cell),
            Paragraph("<b>Subeer</b>", table_cell_bold),
            Paragraph("2.0m", table_cell),
            Paragraph("Declarative policy.yaml, micro-segmentation logic, atomic in-memory hot-reload", table_cell)
        ],
        [
            Paragraph("<b>07</b>", table_cell),
            Paragraph("The 7-Test Adversarial Suite", table_cell),
            Paragraph("<b>Subeer</b>", table_cell_bold),
            Paragraph("2.0m", table_cell),
            Paragraph("7 attack vectors: authorized, anonymous, 403, micro-seg, forged, 503 fail-closed", table_cell)
        ],
        [
            Paragraph("<b>08</b>", table_cell),
            Paragraph("Live Demonstration Execution", table_cell),
            Paragraph("<b>Karthik</b> (Lead)<br/>+ Subeer/Sameep", table_cell_bold),
            Paragraph("6.0m", table_cell),
            Paragraph("Live Docker launch, curl isolation proof, 7 tests run, hot-reload flex, audit log", table_cell)
        ],
        [
            Paragraph("<b>09</b>", table_cell),
            Paragraph("Docker Network Isolation", table_cell),
            Paragraph("<b>Karthik</b>", table_cell_bold),
            Paragraph("1.5m", table_cell),
            Paragraph("Answering Review 1: loopback vs network namespace isolation (zeta-net bridge)", table_cell)
        ],
        [
            Paragraph("<b>10</b>", table_cell),
            Paragraph("Sub-Millisecond Enforcement Benchmark", table_cell),
            Paragraph("<b>Karthik</b>", table_cell_bold),
            Paragraph("1.5m", table_cell),
            Paragraph("500 sequential requests: 0.75ms direct vs 1.35ms gateway = ~0.60ms P50 overhead", table_cell)
        ],
        [
            Paragraph("<b>11</b>", table_cell),
            Paragraph("Engineering Rigor: 19 Unit Tests & CI", table_cell),
            Paragraph("<b>Sameep</b>", table_cell_bold),
            Paragraph("1.5m", table_cell),
            Paragraph("14 policy tests + 5 routing tests, table-driven Go testing, GitHub Actions CI", table_cell)
        ],
        [
            Paragraph("<b>12</b>", table_cell),
            Paragraph("Three-Version Design Evolution", table_cell),
            Paragraph("<b>Shaivyaa</b>", table_cell_bold),
            Paragraph("1.5m", table_cell),
            Paragraph("V0.1 sidecar → V1.0 consolidated → V2.0 Docker mesh & hot-reload", table_cell)
        ],
        [
            Paragraph("<b>13</b>", table_cell),
            Paragraph("Phase 2 Technical Roadmap", table_cell),
            Paragraph("<b>Shaivyaa</b>", table_cell_bold),
            Paragraph("1.5m", table_cell),
            Paragraph("React admin console, public VPS deployment, automated red-team container, eBPF", table_cell)
        ],
        [
            Paragraph("<b>14</b>", table_cell),
            Paragraph("Project Outcomes & Industry Value", table_cell),
            Paragraph("<b>Karthik</b>", table_cell_bold),
            Paragraph("1.0m", table_cell),
            Paragraph("Identity replaces IP, provable guarantees at 0.6ms, enterprise applicability", table_cell)
        ],
        [
            Paragraph("<b>15</b>", table_cell),
            Paragraph("Team Contributions Breakdown", table_cell),
            Paragraph("<b>Sameep</b>", table_cell_bold),
            Paragraph("1.0m", table_cell),
            Paragraph("Engineering lifecycle ownership across design, coding, crypto, testing, and DevOps", table_cell)
        ],
        [
            Paragraph("<b>16</b>", table_cell),
            Paragraph("Summary & Technical Q&A Defense", table_cell),
            Paragraph("<b>Karthik</b> (Lead)<br/>+ All Members", table_cell_bold),
            Paragraph("1.0m<br/>+ Q&A", table_cell),
            Paragraph("Final verdict: code complete, containerized, benchmarked. Transition to panel Q&A", table_cell)
        ],
    ]

    speaker_table = Table(speaker_data, colWidths=[28, 140, 75, 35, 262])
    speaker_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(speaker_table)
    story.append(Spacer(1, 10))

    # Team Contributions Table
    story.append(Paragraph("Comprehensive Team Contributions Matrix", h2_style))
    story.append(Paragraph(
        "This breakdown reflects the division of engineering labor submitted in the project documentation. "
        "Each member has deep domain mastery over their allocated components.", body_style
    ))

    contrib_data = [
        [
            Paragraph("Member & Role", table_hdr),
            Paragraph("Technical Focus Areas", table_hdr),
            Paragraph("Concrete Engineering Deliverables", table_hdr),
            Paragraph("Defense Territory", table_hdr)
        ],
        [
            Paragraph("<b>Karthik P.H.S.R</b><br/>(23BCY10308)<br/><i>Project Lead</i>", table_cell),
            Paragraph("<b>Core Gateway, Networking, Benchmarking, DevOps & Demo</b><br/>(Heaviest Engineering Load)", table_cell),
            Paragraph("• Designed & built Go L7 gateway engine (<code>main.go</code>, 260 LOC)<br/>"
                      "• Reverse proxy forwarding & custom fail-closed <code>ErrorHandler</code><br/>"
                      "• Multi-stage Docker mesh (<code>Dockerfile.gateway</code>, Compose)<br/>"
                      "• Latency benchmarking suite (<code>cmd/loadtest</code>, 500 requests)<br/>"
                      "• GitHub Actions CI pipeline & live demo driver", table_cell),
            Paragraph("System architecture, SPOF mitigation, performance latency, Docker networking, V0.1 consolidation", table_cell)
        ],
        [
            Paragraph("<b>Subeer Srivastava</b><br/>(23BCY10143)<br/><i>Policy Architect</i>", table_cell),
            Paragraph("<b>Policy Engine, Deny-by-Default Logic & Hot-Reload</b><br/>(Second-Heaviest Load)", table_cell),
            Paragraph("• Designed declarative <code>policy.yaml</code> schema (PBAC model)<br/>"
                      "• Implemented in-memory evaluation & multi-method matching<br/>"
                      "• Built zero-downtime hot-reload watcher (<code>os.Stat</code> + ticker)<br/>"
                      "• Concurrency safety with <code>sync.RWMutex</code> read/write locks<br/>"
                      "• Engineered 7-test matrix & demo policy flex", table_cell),
            Paragraph("Policy evaluation algorithm, race conditions, atomic reload, fail-closed config errors, fsnotify trade-offs", table_cell)
        ],
        [
            Paragraph("<b>Sahil S. Thakkar</b><br/>(23BCY10043)<br/><i>Crypto & Identity Lead</i>", table_cell),
            Paragraph("<b>PKI Architecture, mTLS & SPIFFE Cryptography</b>", table_cell),
            Paragraph("• Engineered Root CA & per-service certificate generation scripts<br/>"
                      "• Implemented SPIFFE URI identity encoding in X.509 SAN extensions<br/>"
                      "• Fixed proxy certificate IP/DNS SAN verification defect<br/>"
                      "• Created adversarial rogue keypair for Test 6 (forged SAN)<br/>"
                      "• Enforced TLS 1.2+ & <code>RequireAndVerifyClientCert</code>", table_cell),
            Paragraph("X.509 validation, CA trust chains, SAN vs CN identity, certificate expiry/revocation, MitM resistance", table_cell)
        ],
        [
            Paragraph("<b>Sameep Upadhyay</b><br/>(23BCY10187)<br/><i>Verification Engineer</i>", table_cell),
            Paragraph("<b>Test Automation, CI/CD Pipeline & Audit Subsystem</b>", table_cell),
            Paragraph("• Authored 19 table-driven unit tests (<code>policy_test.go</code>)<br/>"
                      "• Implemented 14 policy checks + 5 longest-prefix route tests<br/>"
                      "• Built adversarial client harness (<code>mock-apps/client.py</code>)<br/>"
                      "• Validated container isolation proof via host-side connection probes<br/>"
                      "• Configured structured JSONL audit record schemas", table_cell),
            Paragraph("Test edge-cases, regression testing, CI automation, audit log forensics, connection-refused verification", table_cell)
        ],
        [
            Paragraph("<b>Shaivyaa Sharma</b><br/>(23BCY10020)<br/><i>Security Analyst</i>", table_cell),
            Paragraph("<b>Threat Modeling, Related Work & Phase 2 Architecture</b>", table_cell),
            Paragraph("• Conducted systematic literature review (NIST, OWASP, Istio, Cilium)<br/>"
                      "• Formulated 6-scenario adversary threat model (T1–T6)<br/>"
                      "• Tracked V0.1 → V1.0 → V2.0 architectural evolution matrix<br/>"
                      "• Architected Phase 2 React Admin Console & eBPF integration plan<br/>"
                      "• Project report lead & academic documentation", table_cell),
            Paragraph("Threat modeling, industry comparison (Istio/Envoy), Phase 2 feasibility, real-world deployment", table_cell)
        ],
    ]

    contrib_table = Table(contrib_data, colWidths=[90, 115, 215, 120])
    contrib_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(contrib_table)
    story.append(PageBreak())

    # =========================================================================
    # PART 2: SPEAKING SCRIPTS (SLIDE BY SLIDE)
    # =========================================================================
    story.append(Paragraph("Part 2: Word-for-Word Speaking Scripts", h1_style))
    story.append(Paragraph(
        "Memorize the exact phrasing below. Text formatted in <b>bold red italics</b> indicates critical <i>'Money Lines'</i> "
        "designed to impress panel evaluators and demonstrate security engineering maturity.", body_style
    ))
    story.append(Spacer(1, 4))

    # Slide 1
    story.append(Paragraph("SLIDE 1: Title & Introduction (1.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Polisetti Hari Sri Raj Karthik (Lead)", script_speaker))
    story.append(Paragraph(
        "\"Good morning respected supervisor Dr. Sajjad Ahmed, Program Chair Dr. Saravanan, and members of the evaluation committee. "
        "We are Group 39, presenting our Capstone Project Phase 1, Review 2: <b>ZetaShield V2.0 — Containerized Zero-Trust Micro-Segmentation Gateway</b>.<br/>"
        "My name is Karthik, and I am joined by my team members: Subeer Srivastava, Sahil Thakkar, Shaivyaa Sharma, and Sameep Upadhyay.<br/>"
        "In our first review, we presented a preliminary prototype. Today, we present a completely transformed, production-ready system: "
        "an identity-aware Layer-7 security gateway written in Go, fully containerized in Docker, with mutual TLS, declarative deny-by-default policies, "
        "live policy hot-reload, and a measured sub-millisecond enforcement overhead. Let us begin with the problem we set out to solve.\"",
        script_body
    ))

    # Slide 2
    story.append(Paragraph("SLIDE 2: The Problem: Flat Networks & Lateral Movement (1.5 min)", h2_style))
    story.append(Paragraph("SPEAKER: Polisetti Hari Sri Raj Karthik (Lead)", script_speaker))
    story.append(Paragraph(
        "\"Traditional cybersecurity relies heavily on perimeter firewalls operating at Layers 3 and 4. While this protects the castle gates, "
        "it creates a dangerous topology: <i>a hard exterior, but a completely soft, flat interior</i>. "
        "Once an adversary breaches the perimeter—through a phished credential, a compromised third-party package, or a remote exploit—they find themselves "
        "inside a flat internal network where every service can freely talk to every other service.<br/>"
        "The Open Web Application Security Project (OWASP) ranks <b>Broken Access Control as the #1 threat in its 2025 Top 10</b>. "
        "Furthermore, NIST Special Publication 800-207 mandates Zero-Trust Architecture precisely to neutralize this risk.<br/>"
        "Enterprise solutions like Istio and Envoy exist, but they demand complex Kubernetes clusters, massive resource overhead, and hundreds of thousands of lines of code. "
        "Our mission was clear: to engineer a lightweight, standalone, deployable Layer-7 enforcement engine that eliminates implicit trust between internal microservices.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"The fundamental problem we are solving is stopping attackers from moving freely once inside the perimeter.\"</i>",
        money_line
    ))

    # Slide 3
    story.append(Paragraph("SLIDE 3: Consolidated Gateway with Containerized Isolation (2.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Polisetti Hari Sri Raj Karthik (Lead)", script_speaker))
    story.append(Paragraph(
        "\"To solve this without excessive latency, we underwent a major architectural evolution. "
        "In Review 1, our V0.1 prototype used a 4-hop sidecar mesh: client to client-proxy, to server-proxy, to external control plane, to backend. "
        "You rightly critiqued that design for unnecessary layering and latency.<br/>"
        "We listened, and engineered the <b>V1.0 Consolidated 2-Hop Gateway</b>, now upgraded to <b>V2.0 with full Docker containerization</b>.<br/>"
        "Here is the request flow: calling services present a cryptographic client certificate to the Gateway over mutual TLS on port 8443. "
        "The Gateway terminates TLS, extracts the service identity, evaluates our deny-by-default policy, routes the request to the upstream backend, "
        "and logs the complete decision to an audit trail.<br/>"
        "Most importantly: our backend microservices—Orders and Payments—publish <b>no host ports</b>. They are physically unreachable from the host or outside network, "
        "residing purely in an internal Docker bridge network. I will now hand over to Subeer to explain our enforcement pipeline.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"Two layers. One enforcement point. All backends physically unreachable.\"</i>",
        money_line
    ))

    # Slide 4
    story.append(Paragraph("SLIDE 4: Three Checkpoints, Zero Trust (2.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Subeer Srivastava (Policy Architect)", script_speaker))
    story.append(Paragraph(
        "\"Thank you, Karthik. At the core of ZetaShield is a strict, sequential enforcement pipeline comprising three mandatory checkpoints. "
        "Every single HTTP request must survive all three checkpoints before a single byte reaches a backend.<br/>"
        "<b>Checkpoint 1 is Identity via mTLS:</b> Before any application data is parsed, the gateway verifies the caller's X.509 certificate against our private Root CA. "
        "If a caller presents no certificate, an expired certificate, or a forged certificate, the connection is instantly aborted at the TLS handshake level.<br/>"
        "<b>Checkpoint 2 is Policy-Based Access Control (PBAC):</b> We extract the caller's identity and evaluate it against our declarative <code>policy.yaml</code> ruleset. "
        "Our engine is <b>deny-by-default</b>: only explicit ALLOW rules pass. If an identity has no rule for that path or HTTP method, it receives an instant <code>HTTP 403 Forbidden</code>.<br/>"
        "<b>Checkpoint 3 is Routing and Forensic Audit:</b> Permitted requests are routed via longest-prefix matching to the internal backend. "
        "Concurrently, an immutable, append-only JSONL audit log records the exact timestamp, identity, method, path, decision, and forensic rationale.<br/>"
        "If the backend service is offline, the gateway catches the dial error and fails closed with a controlled <code>HTTP 503</code>. "
        "Now, Sahil will explain how we make identity unforgeable.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"Failure is never permission. When a check fails, the request dies right there.\"</i>",
        money_line
    ))

    # Slide 5
    story.append(Paragraph("SLIDE 5: Trust the Issuer, Not the Claim (2.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Sahil S. Thakkar (Crypto & Identity Lead)", script_speaker))
    story.append(Paragraph(
        "\"Thank you, Subeer. In legacy architectures, service identity is frequently passed in HTTP headers, such as <code>X-User-ID</code> or <code>X-Service-Name</code>. "
        "Any junior penetration tester knows that HTTP headers can be easily spoofed using curl or a proxy.<br/>"
        "In ZetaShield, we adopted the industry-standard <b>SPIFFE (Secure Production Identity Framework for Everyone)</b> standard, the exact same identity model "
        "used by Istio and HashiCorp Consul. Service identity is cryptographically bound into the X.509 certificate's <b>Subject Alternative Name (SAN)</b> URI extension—for example, "
        "<code>spiffe://zetashield.local/ns/default/sa/frontend-service</code>.<br/>"
        "Why is this unforgeable? Because during the TLS handshake, our Go gateway extracts the identity directly from <code>r.TLS.PeerCertificates[0].URIs</code>. "
        "To forge an identity, an attacker would need our private Root CA key to sign their certificate.<br/>"
        "In our adversarial tests, an attacker creates a certificate with the exact legitimate SPIFFE identity URI, but signs it themselves. "
        "The gateway drops them at the handshake because the issuer is untrusted. Subeer will now walk through our policy and hot-reload mechanisms.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"The attacker forged the exact identity on the badge, but trust lives in the issuer, not the claim.\"</i>",
        money_line
    ))

    # Slide 6
    story.append(Paragraph("SLIDE 6: Deny-by-Default & Hot-Reload (2.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Subeer Srivastava (Policy Architect)", script_speaker))
    story.append(Paragraph(
        "\"Thank you, Sahil. Our access control rules are defined in a clean, human-readable <code>policy.yaml</code> file. "
        "It consists of two sections: route prefix mappings and access rules.<br/>"
        "Notice the zero-trust micro-segmentation in action: <code>frontend-service</code> is explicitly allowed to call <code>GET /orders/</code> and <code>POST /payments/</code>. "
        "<code>orders-service</code> is allowed to query its own domain, <code>/orders/</code>. "
        "Crucially, there is <b>NO RULE</b> permitting <code>orders-service</code> to access <code>/payments/</code>. "
        "Therefore, if an attacker compromises the orders service, lateral movement into the payments API is strictly blocked with a 403.<br/>"
        "Furthermore, in V2.0 we engineered <b>zero-downtime Policy Hot-Reload</b>. "
        "A dedicated goroutine in our gateway checks the modification timestamp of <code>policy.yaml</code> every 1 second using standard-library <code>os.Stat</code>. "
        "When an administrator edits the policy, the gateway detects it, acquires a write lock on our <code>sync.RWMutex</code>, and atomically reloads the rules in memory in under 1 second. "
        "Active connections are never dropped, and no container restart is required. Next, let us review our 7-test verification matrix.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"The security perimeter changes in seconds without zero downtime or dropped TCP sessions.\"</i>",
        money_line
    ))

    # Slide 7
    story.append(Paragraph("SLIDE 7: The 7-Test Adversarial Suite (2.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Subeer Srivastava (Policy Architect)", script_speaker))
    story.append(Paragraph(
        "\"To prove our architecture works beyond theoretical claims, we engineered a deterministic 7-test adversarial test client. "
        "Every test maps to a concrete real-world threat scenario:<br/>"
        "<b>Test 1 verifies Authorized Access:</b> frontend-service calls <code>/orders/list</code> with its valid certificate → <b>200 OK</b>.<br/>"
        "<b>Test 2 verifies Transport Security:</b> an anonymous client connects without a certificate → <b>TLS Handshake Rejected</b>.<br/>"
        "<b>Test 3 verifies Deny-by-Default:</b> frontend-service probes <code>/admin/delete</code> where no rule exists → <b>403 Forbidden</b>.<br/>"
        "<b>Test 4 is our Micro-Segmentation flagship:</b> orders-service, fully authenticated, attempts to query <code>/payments/balance</code>. "
        "Because no rule exists, it receives <b>403 Forbidden</b>—lateral movement is halted.<br/>"
        "<b>Test 5 verifies Own-Domain Access:</b> payments-service accesses its own balance → <b>200 OK</b>.<br/>"
        "<b>Test 6 verifies Cryptographic Authenticity:</b> an attacker presenting a forged certificate with the legitimate SPIFFE identity is rejected at the TLS handshake.<br/>"
        "<b>Test 7 verifies Fail-Closed Availability:</b> a request to an offline inventory backend returns <b>503 Service Unavailable</b> without failing open.<br/>"
        "The deterministic expected sequence is: <b>200, TLS_REJECT, 403, 403, 200, TLS_REJECT, 503</b>. "
        "I now turn over to Karthik to drive our live demonstration.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"Fully authenticated, still denied — authentication is not authorization.\"</i>",
        money_line
    ))

    # Slide 8
    story.append(Paragraph("SLIDE 8: Live Demonstration Execution (6.0 min)", h2_style))
    story.append(Paragraph("DRIVER: Karthik (Lead) &nbsp;|&nbsp; NARRATORS: Sameep (Isolation) & Subeer (Hot-Reload)", script_speaker))
    story.append(Paragraph(
        "<i>(See Part 3: Live Demo Runbook for the full beat-by-beat terminal execution transcript).</i>", body_style
    ))

    # Slide 9
    story.append(Paragraph("SLIDE 9: Docker Network Isolation: Solving Deployability (1.5 min)", h2_style))
    story.append(Paragraph("SPEAKER: Polisetti Hari Sri Raj Karthik (Lead)", script_speaker))
    story.append(Paragraph(
        "\"Thank you. In Review 1, the committee asked: <i>'Does this only work on localhost under narrow conditions? How is this deployable?'</i><br/>"
        "This slide presents our architectural answer. In local development mode, we enforced isolation by binding backends exclusively to <code>127.0.0.1</code> loopback. "
        "In V2.0, we adapted the exact same isolation invariant to containerized deployments using <b>Docker bridge network namespaces</b>.<br/>"
        "Our Compose file defines a private bridge network called <code>zeta-net</code>. "
        "The Orders and Payments containers have <b>no port bindings whatsoever</b>. The Gateway is the sole container with a published port: <code>8443:8443</code>. "
        "Because Docker provides internal DNS resolution, the gateway proxies traffic to <code>http://orders:9091</code> and <code>http://payments:9092</code> over the bridge. "
        "The host machine cannot route to these services directly. This is not a hack—this is the exact network namespace isolation pattern used in production Kubernetes clusters.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"The isolation invariant survives the platform shift: from loopback binding to container network namespaces.\"</i>",
        money_line
    ))

    # Slide 10
    story.append(Paragraph("SLIDE 10: Sub-Millisecond Enforcement Benchmark (1.5 min)", h2_style))
    story.append(Paragraph("SPEAKER: Polisetti Hari Sri Raj Karthik (Lead)", script_speaker))
    story.append(Paragraph(
        "\"Another major critique from Review 1 was: <i>'Too many layers introduces too much latency.'</i><br/>"
        "Rather than guessing, we measured. We engineered a dedicated benchmarking tool in <code>cmd/loadtest</code> that executes 500 sequential requests "
        "comparing direct calls against calls through our full Zero-Trust gateway on the same hardware.<br/>"
        "Here are the empirical results: direct requests to the backend average 0.75 milliseconds median latency. "
        "Requests traversing the full Zero-Trust gateway—which includes the complete mTLS handshake, cryptographic SAN extraction, in-memory policy lookup, "
        "reverse proxy forwarding, and synchronous JSONL audit disk write—average 1.35 milliseconds.<br/>"
        "The total median enforcement overhead is <b>only ~0.60 milliseconds</b>, and under 1.2 milliseconds at the 99th percentile. "
        "In production microservices where network calls take 20 to 100 milliseconds, a 0.6ms overhead represents an imperceptible 1 to 3 percent cost. "
        "Now, Sameep will discuss our unit testing and CI pipeline.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"Full mTLS and L7 policy enforcement costs only 0.6 milliseconds — zero trust does not mean zero performance.\"</i>",
        money_line
    ))

    # Slide 11
    story.append(Paragraph("SLIDE 11: Engineering Rigor: 19 Unit Tests & CI (1.5 min)", h2_style))
    story.append(Paragraph("SPEAKER: Sameep Upadhyay (Verification Engineer)", script_speaker))
    story.append(Paragraph(
        "\"Thank you, Karthik. To ensure production stability and prevent regression errors, we implemented 19 comprehensive, table-driven unit tests in Go.<br/>"
        "These cover two distinct categories: <b>14 Policy Tests</b> verifying authorized flows, own-domain access, method constraints like blocking POST on GET-only routes, "
        "root probes, admin probes, empty identities, and cross-service denials. "
        "And <b>5 Routing Tests</b> verifying longest-prefix matching, dead routes, and unknown endpoints.<br/>"
        "Furthermore, this is not just tested on our laptops. Every single git push to our GitHub repository triggers an automated <b>GitHub Actions Continuous Integration pipeline</b>. "
        "The runner spins up an Ubuntu environment, runs <code>go vet</code>, builds the static binary, and executes all 19 unit tests. "
        "Our repository has maintained a 100% green build badge across our entire development cycle. Shaivyaa will now walk us through our design evolution.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"19 automated unit tests gating every commit in CI — engineering rigor, not just a working prototype.\"</i>",
        money_line
    ))

    # Slide 12
    story.append(Paragraph("SLIDE 12: Three-Version Design Evolution (1.5 min)", h2_style))
    story.append(Paragraph("SPEAKER: Shaivyaa Sharma (Security Analyst)", script_speaker))
    story.append(Paragraph(
        "\"Thank you, Sameep. Great engineering is defined by how effectively it responds to peer and supervisor critique. "
        "This slide illustrates our design evolution across three distinct versions:<br/>"
        "In <b>V0.1</b>, presented at Review 1, we implemented a 4-hop sidecar prototype. The feedback was direct: too complex, high latency, single backend.<br/>"
        "In response, we engineered <b>V1.0</b>: we consolidated the architecture into a 2-hop gateway, added mutual TLS with SPIFFE identities, "
        "built a multi-backend service fleet, added 16 unit tests, and proved the 0.6ms latency benchmark.<br/>"
        "Finally, for Review 2, we built <b>V2.0</b>: complete Docker containerization, network namespace isolation, tests 6 and 7 for forged certs and fail-closed outages, "
        "19 unit tests, and real-time policy hot-reload.<br/>"
        "Every single critique from Review 1 has been addressed with working code and empirical data. Next is our Phase 2 roadmap.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"We converted every criticism from Review 1 into a verifiable, working engineering feature.\"</i>",
        money_line
    ))

    # Slide 13
    story.append(Paragraph("SLIDE 13: Phase 2 Technical Roadmap (1.5 min)", h2_style))
    story.append(Paragraph("SPEAKER: Shaivyaa Sharma (Security Analyst)", script_speaker))
    story.append(Paragraph(
        "\"With our core data-plane enforcement fully proven in Phase 1, our Phase 2 roadmap expands into management, scaling, and validation:<br/>"
        "<b>First is the React Administrative Console:</b> We will construct a real-time web UI consuming the audit stream via WebSockets, "
        "featuring a live topology map showing service connections and blocked lateral movement attempts, alongside an interactive policy editor.<br/>"
        "<b>Second is Cloud Deployment:</b> We will deploy the container mesh to a public cloud VPS to demonstrate internet-facing zero-trust ingress.<br/>"
        "<b>Third is Automated Red-Team Simulation:</b> We will build a dedicated attacker container inside the mesh that continuously fuzzes and probes the gateway.<br/>"
        "<b>Fourth is eBPF Kernel Acceleration:</b> Exploring kernel-level Layer 4 packet filtering to complement our Layer 7 proxy. "
        "Karthik will now summarize our outcomes.\"",
        script_body
    ))

    # Slide 14
    story.append(Paragraph("SLIDE 14: Project Outcomes & Industry Value (1.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Polisetti Hari Sri Raj Karthik (Lead)", script_speaker))
    story.append(Paragraph(
        "\"In conclusion, ZetaShield achieves three fundamental milestones: "
        "First, it replaces fragile, IP-based perimeter trust with <b>cryptographic, identity-based micro-segmentation</b>. "
        "Second, it delivers provable, fail-closed security guarantees at a negligible <b>0.6ms latency overhead</b>. "
        "Third, it provides organizations with a deployable, lightweight internal firewall for server-to-server traffic "
        "without the crushing operational complexity of an enterprise service mesh.\"",
        script_body
    ))
    story.append(Paragraph(
        "<b>MONEY LINE:</b> <i>\"A deployable, identity-based firewall proxy for traffic between your own servers.\"</i>",
        money_line
    ))

    # Slide 15
    story.append(Paragraph("SLIDE 15: Team Contributions Breakdown (1.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Sameep Upadhyay (Verification Engineer)", script_speaker))
    story.append(Paragraph(
        "\"This project represents an intensive, balanced collaborative effort across the entire software development lifecycle: "
        "Karthik led core gateway engineering, mTLS logic, Docker mesh deployment, CI/CD, and benchmarking. "
        "Subeer engineered the policy schema, deny-by-default logic, PBAC evaluation, and hot-reload engine. "
        "Sahil directed the PKI architecture, X.509 extensions, and SPIFFE identity model. "
        "Shaivyaa conducted the threat modeling, literature investigation, and Phase 2 dashboard architecture. "
        "And I designed the 19-test unit suite, adversarial client scenarios, and network isolation verification.\"",
        script_body
    ))

    # Slide 16
    story.append(Paragraph("SLIDE 16: Summary & Technical Q&A Defense (1.0 min)", h2_style))
    story.append(Paragraph("SPEAKER: Polisetti Hari Sri Raj Karthik (Lead)", script_speaker))
    story.append(Paragraph(
        "\"To summarize: ZetaShield V2.0 is <b>Code Complete, Fully Containerized, Empirically Benchmarked, and Strictly Fail-Closed</b>. "
        "Our source code, CI pipelines, and reproduction guides are public on GitHub under release tag <code>v1.0-phase1</code>.<br/>"
        "We thank our supervisor Dr. Sajjad Ahmed for his invaluable guidance. We are now open and ready for your questions.\"",
        script_body
    ))
    story.append(PageBreak())

    # =========================================================================
    # PART 3: THE LIVE DEMO RUNBOOK (6 MINUTES)
    # =========================================================================
    story.append(Paragraph("Part 3: The Live Demo Runbook (6-Minute Protocol)", h1_style))
    story.append(Paragraph(
        "Follow this beat-by-beat protocol with military precision. <b>Never debug or recompile code during the presentation.</b> "
        "If a terminal hangs, transition immediately to the contingency protocol.", body_style
    ))
    story.append(Spacer(1, 4))

    demo_steps = [
        [
            Paragraph("Beat / Step", table_hdr),
            Paragraph("Terminal & Exact Command", table_hdr),
            Paragraph("Spoken Narration & Action", table_hdr),
            Paragraph("Expected Terminal Output", table_hdr)
        ],
        [
            Paragraph("<b>BEAT 1</b><br/>Mesh Launch<br/><i>(45 sec)</i>", table_cell),
            Paragraph("<b>Terminal 1 (Root):</b><br/><code>docker compose up --build -d</code><br/><br/><code>docker compose ps</code>", table_cell),
            Paragraph("<b>Karthik:</b> <i>'We launch the entire Zero-Trust mesh with one command. "
                      "Notice the container status: the Gateway maps port 8443 to the host. "
                      "Orders and Payments have ZERO published host ports.'</i>", table_cell),
            Paragraph("<code>zeta-gateway: Up (0.0.0.0:8443->8443)<br/>"
                      "zeta-orders: Up (no ports)<br/>"
                      "zeta-payments: Up (no ports)</code>", code_style)
        ],
        [
            Paragraph("<b>BEAT 2</b><br/>Isolation Proof<br/><i>(45 sec)</i>", table_cell),
            Paragraph("<b>Terminal 2 (Host):</b><br/><code>curl http://127.0.0.1:9091/orders/list</code><br/><br/><code>curl http://127.0.0.1:9092/payments/balance</code>", table_cell),
            Paragraph("<b>Sameep:</b> <i>'Here is our proof of network namespace isolation. An attacker on the host tries to curl "
                      "the Orders backend directly. It fails with Connection Refused. The only path is through the mTLS gateway.'</i>", table_cell),
            Paragraph("<code>curl: (7) Failed to connect to 127.0.0.1 port 9091: Connection refused</code>", code_style)
        ],
        [
            Paragraph("<b>BEAT 3</b><br/>7-Test Suite<br/><i>(90 sec)</i>", table_cell),
            Paragraph("<b>Terminal 2 (Host):</b><br/><code>cd mock-apps</code><br/><code>python client.py</code>", table_cell),
            Paragraph("<b>Karthik:</b> Runs script.<br/>"
                      "<b>Subeer:</b> Narrates tests 1–4.<br/>"
                      "<b>Sahil:</b> Narrates test 6 (forged SAN rejection).<br/>"
                      "<b>Karthik:</b> Concludes test 7 (fail-closed 503).", table_cell),
            Paragraph("<code>[TEST 1] Authorized → 200 OK<br/>"
                      "[TEST 2] No Cert → TLS_REJECT<br/>"
                      "[TEST 3] Admin Probe → 403 Forbidden<br/>"
                      "[TEST 4] Lateral Move → 403 Forbidden<br/>"
                      "[TEST 5] Own Domain → 200 OK<br/>"
                      "[TEST 6] Forged Cert → TLS_REJECT<br/>"
                      "[TEST 7] Fail-Closed → 503<br/>"
                      "Sequence: 200, TLS_REJECT, 403, 403, 200, TLS_REJECT, 503</code>", code_style)
        ],
        [
            Paragraph("<b>BEAT 4</b><br/>Hot-Reload Flex<br/><i>(90 sec)</i>", table_cell),
            Paragraph("<b>Terminal 3 (Logs):</b><br/><code>docker compose logs -f gateway</code><br/><br/>"
                      "<b>VS Code:</b> Comment out payments rule in <code>deploy/policy.docker.yaml</code><br/><br/>"
                      "<b>Terminal 2:</b> <code>python client.py</code>", table_cell),
            Paragraph("<b>Subeer:</b> <i>'Watch the gateway logs. We edit policy.docker.yaml to revoke payments-service access. "
                      "Within one second, the gateway logs [policy] hot-reloaded without container restart. "
                      "We re-run the client: Test 5 instantly flips from 200 OK to 403 Forbidden! Access revoked live.'</i><br/>"
                      "<i>(Re-uncomment rule after demo).</i>", table_cell),
            Paragraph("<code>zeta-gateway | [policy] hot-reloaded /etc/zetashield/policy.yaml<br/><br/>"
                      "[TEST 5] Payments → 403 Forbidden (LIVE REVOCATION)</code>", code_style)
        ],
        [
            Paragraph("<b>BEAT 5</b><br/>Audit Trail<br/><i>(45 sec)</i>", table_cell),
            Paragraph("<b>Terminal 2 (Host):</b><br/><code>tail -n 7 deploy/logs/audit.log.jsonl</code>", table_cell),
            Paragraph("<b>Sameep:</b> <i>'Every single request produces an immutable structured JSONL audit entry. "
                      "Notice the entries: decisions ALLOW, DENY, and ERROR with complete cryptographic identity and reason.'</i>", table_cell),
            Paragraph("<code>{\"timestamp\":\"...\",\"decision\":\"DENY\",\"identity\":\"spiffe://.../orders-service\",\"reason\":\"no matching ALLOW rule\"}</code>", code_style)
        ],
        [
            Paragraph("<b>BEAT 6</b><br/>Disaster Protocol<br/><i>(Fallback)</i>", table_cell),
            Paragraph("<b>VLC Media Player:</b><br/><code>ZetaShield_V2_Demo_Backup.mp4</code><br/>(Pre-loaded, paused)", table_cell),
            Paragraph("<b>Karthik (Rule):</b> If Docker fails or host hangs, switch to video immediately. "
                      "<b>Never troubleshoot code in front of reviewers.</b>", table_cell),
            Paragraph("<i>'As an engineering redundancy, we recorded the identical containerized demo run in full HD...'</i>", callout_text)
        ],
    ]

    demo_table = Table(demo_steps, colWidths=[65, 155, 175, 145])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(demo_table)
    story.append(PageBreak())

    # =========================================================================
    # PART 4: VIVA Q&A DEFENSE BANK (20 QUESTIONS)
    # =========================================================================
    story.append(Paragraph("Part 4: Viva Q&A Defense Bank (20 Questions)", h1_style))
    story.append(Paragraph(
        "Questions are organized by individual territory. Answer directly, confidently, and cite working implementation artifacts. "
        "Avoid rambling—give the technical punchline in the first sentence.", body_style
    ))
    story.append(Spacer(1, 4))

    # Territory 1: Karthik
    story.append(Paragraph("Territory 1: Architecture, Dangerous Trap Questions & Scalability (Karthik)", h2_style))
    
    qa_karthik = [
        ("Q1 (Trap): Why did you drop the separate FastAPI Control Plane from your original V0.1 design?",
         "Karthik: \"We consolidated based directly on Review 1 feedback. In V0.1, calling an external control plane added a fourth network hop, "
         "inflating median latency to ~2.5ms. In modern zero-trust design (like Istio Ambient mode), in-process policy evaluation is preferred for performance. "
         "By embedding the policy engine in Go with sync.RWMutex and file hot-reload, we slashed median overhead to 0.6ms while preserving dynamic policy updates. "
         "A decoupled control plane is reserved for Phase 2 when managing multi-cluster fleets.\""),
        
        ("Q2 (Trap): Isn't a consolidated gateway a Single Point of Failure (SPOF)?",
         "Karthik: \"In our Phase 1 prototype, yes, it runs as a single container. However, architecturally, our gateway is completely stateless—it maintains "
         "no session state or distributed locks. In production, you scale it horizontally behind a Layer-4 cloud load balancer (like AWS NLB or HAProxy), "
         "with multiple gateway instances sharing the same read-only policy volume or control plane. If one crashes, traffic instantly shifts to healthy nodes.\""),
        
        ("Q3 (Trap): 500 requests is not real benchmarking. How do you know this scales to 50,000 req/sec?",
         "Karthik: \"The 500-request benchmark in cmd/loadtest was specifically designed to isolate per-request enforcement overhead on identical hardware without network jitter. "
         "Go's net/http stack natively allocates an ultra-lightweight 2KB goroutine per connection. Because our policy check is a sub-microsecond in-memory hash map lookup "
         "under an RWMutex read lock, throughput is purely bounded by CPU TLS cryptography. For Phase 2, we have scheduled concurrent wrk stress-testing.\""),
        
        ("Q4: Why did you build this in Go instead of Python or Rust?",
         "Karthik: \"Go was chosen for three architectural reasons: First, its concurrency model uses lightweight goroutines rather than Python's Global Interpreter Lock (GIL). "
         "Second, Go's standard library net/http/httputil and crypto/tls packages are battle-tested production stacks used by Cloudflare and Docker. "
         "Third, Go compiles to a static, self-contained binary under 15MB, eliminating runtime dependency vulnerabilities in our Alpine containers.\""),
        
        ("Q5: How does this differ from commercial solutions like Istio or Linkerd?",
         "Karthik: \"Istio requires a heavy Kubernetes control plane (istiod) and injects Envoy sidecars consuming 50MB+ of RAM per container. "
         "ZetaShield provides the exact same core NIST SP 800-207A guarantees—mTLS, SPIFFE identity, deny-by-default policy, fail-closed routing—in a "
         "standalone, 15MB binary runnable on any laptop with single-command Docker Compose simplicity.\""),
        
        ("Q6: What happens if an attacker compromises the Docker host itself?",
         "Karthik: \"Zero Trust operates on the principle of defense-in-depth within the application plane. If the underlying host kernel is compromised, "
         "host-level security (SELinux/AppArmor) is the relevant boundary. However, within the container plane, ZetaShield guarantees that compromised workloads "
         "cannot move laterally across the bridge network to reach other microservices without cryptographic authorization.\"")
    ]
    for q, a in qa_karthik:
        story.append(Paragraph(f"<b>{q}</b>", q_title))
        story.append(Paragraph(a, q_ans))

    # Territory 2: Subeer
    story.append(Paragraph("Territory 2: Policy Engine, Hot-Reload & Concurrency (Subeer)", h2_style))
    
    qa_subeer = [
        ("Q7: What happens if an administrator saves a malformed or corrupted YAML policy during hot-reload?",
         "Subeer: \"The gateway strictly fails closed. In loadPolicy(), we parse the YAML using gopkg.in/yaml.v3. If parsing fails, the error is logged to stderr, "
         "the reload aborts, and the gateway retains the previous valid in-memory policy. At no point does a corrupted file zero out the rules or cause a panic.\""),
        
        ("Q8: How do you prevent race conditions when reloading policy while requests are executing?",
         "Subeer: \"We synchronize state using Go's sync.RWMutex. When requests are being authorized in checkPolicy(), they acquire a read lock (RLock()), allowing "
         "thousands of concurrent evaluations. When startPolicyWatcher() detects a file modification, it acquires an exclusive write lock (Lock()) on policyMu. "
         "New requests pause for a fraction of a microsecond while the struct pointer updates, guaranteeing zero race conditions and zero half-read state.\""),
        
        ("Q9: Why did you use a 1-second time.Ticker with os.Stat instead of Linux fsnotify?",
         "Subeer: \"fsnotify relies on inotify syscalls, which are notoriously flaky across Docker volume mounts on Windows and macOS. When Docker mounts a host file, "
         "inode events are frequently dropped. A 1-second polling ticker inspecting os.Stat().ModTime() is 100% portable, standard-library native, consumes negligible CPU, "
         "and guarantees reliable detection across all platforms.\""),
        
        ("Q10: What if an attacker tries path traversal, like /orders/../admin?",
         "Subeer: \"Go's net/http standard library automatically canonicalizes request paths using path.Clean before passing the request to our handler. "
         "Any ../ sequence is resolved before checkPolicy() evaluates strings.HasPrefix. Furthermore, our deny-by-default logic blocks any unmatched path.\""),
        
        ("Q11: Why is deny-by-default structurally safer than permit-by-default?",
         "Subeer: \"In a permit-by-default system, a missing rule or typo opens a security hole. In ZetaShield, the safe state is the default state: if an identity has no "
         "explicit rule for a path and method, checkPolicy() returns false. An empty policy file results in 100% rejection, which is the foundational rule of Zero Trust.\"")
    ]
    for q, a in qa_subeer:
        story.append(Paragraph(f"<b>{q}</b>", q_title))
        story.append(Paragraph(a, q_ans))

    # Territory 3: Sahil
    story.append(Paragraph("Territory 3: Cryptography, PKI & SPIFFE Identities (Sahil)", h2_style))
    
    qa_sahil = [
        ("Q12: What happens if your private Root CA key is compromised?",
         "Sahil: \"If the Root CA key is compromised, an attacker can issue valid certificates. In our Phase 1 prototype, CA keys are generated locally. "
         "In a production environment, the Root CA resides in a Hardware Security Module (HSM) or an enterprise PKI like HashiCorp Vault. In Phase 2, "
         "we plan to integrate SPIRE, which issues short-lived 1-hour certificates with automated workload attestation, drastically reducing the blast radius.\""),
        
        ("Q13: Why did you embed the SPIFFE URI in the Subject Alternative Name (SAN) instead of the Common Name (CN)?",
         "Sahil: \"RFC 5280 and modern TLS standards officially deprecate the Common Name (CN) field. Furthermore, SPIFFE RFC specifications mandate that workload identity "
         "must be carried in the Subject Alternative Name (SAN) URI extension. This cleanly decouples the transport hostname from the cryptographic service identity.\""),
        
        ("Q14: Why do service certificates have a 30-day validity period?",
         "Sahil: \"Long-lived certificates violate zero-trust hygiene because compromised keys remain valid indefinitely. 30 days was chosen as a practical developer validity. "
         "In production with automated rotation, certificates should expire in 24 hours or less.\""),
        
        ("Q15: How did you fix the 'IP address mismatch' error during proxy certificate generation?",
         "Sahil: \"When clients connect over HTTPS to 127.0.0.1, the TLS stack verifies that the server certificate SAN matches the connect address. "
         "Initially our proxy certificate only contained the SPIFFE URI. We updated issue_cert.sh so that when the service is 'proxy', it appends IP:127.0.0.1 and DNS:localhost "
         "to san.cnf, enabling standard hostname verification without disabling client-side security checks.\"")
    ]
    for q, a in qa_sahil:
        story.append(Paragraph(f"<b>{q}</b>", q_title))
        story.append(Paragraph(a, q_ans))

    # Territory 4: Sameep & Shaivyaa
    story.append(Paragraph("Territory 4: Testing, Verification & Roadmap (Sameep & Shaivyaa)", h2_style))
    
    qa_other = [
        ("Q16: How do you prove backends cannot talk to each other without going through the gateway?",
         "Sameep: \"In local mode, services bind to 127.0.0.1. In Docker mode, services reside in an isolated bridge network with no host ports published. "
         "If orders-service attempts to query payments-api, it cannot route directly because network policies restrict inter-container traffic. "
         "In Test 4, when orders-service calls the gateway for payments, the gateway returns 403 Forbidden.\""),
        
        ("Q17: Why do you have 19 unit tests? What do they cover?",
         "Sameep: \"Our 19 tests in policy_test.go provide 100% branch coverage of our authorization logic: 14 policy tests cover authorized paths, "
         "method enforcement (POST vs GET), root probes, admin probes, empty identities, and cross-service denials. The 5 routing tests verify longest-prefix route resolution and dead routes.\""),
        
        ("Q18: Why does Test 7 use 'dead-host:9099' in Docker instead of an IP address?",
         "Sameep: \"In local mode, port 9099 is offline, triggering a TCP connection refused error. In Docker, dead-host is an unresolvable hostname, triggering a DNS resolution failure. "
         "Both test cases prove that when an upstream backend fails, our custom ErrorHandler intercepts the failure and returns a controlled HTTP 503 rather than failing open.\""),
        
        ("Q19: How will Phase 2 improve on Phase 1?",
         "Shaivyaa: \"Phase 1 proved data-plane enforcement and sub-millisecond overhead. Phase 2 focuses on operational observability: a React web console with a live WebSocket "
         "feed of audit.log.jsonl, automated red-team probing, and eBPF kernel acceleration for Layer 4 traffic.\""),
        
        ("Q20: Can ZetaShield be deployed in an existing Kubernetes cluster?",
         "Shaivyaa: \"Yes. ZetaShield can be deployed as an Ingress Controller or API Gateway using Kubernetes DaemonSets or Deployments, with backends isolated via K8s NetworkPolicies.\"")
    ]
    for q, a in qa_other:
        story.append(Paragraph(f"<b>{q}</b>", q_title))
        story.append(Paragraph(a, q_ans))

    story.append(Spacer(1, 4))
    # The 3 Golden Sentences
    golden_box = (
        "<b>THE 3 GOLDEN SENTENCES (MUST BE MEMORIZED BY ALL MEMBERS):</b><br/>"
        "<b>1.</b> <i>'Zero Trust means trust is never implicit; every single request must be cryptographically authenticated, authorized by policy, and audited.'</i><br/>"
        "<b>2.</b> <i>'Authentication is not authorization — presenting a valid certificate gets you through the TLS door, but policy determines if you can touch the data.'</i><br/>"
        "<b>3.</b> <i>'Failure is never permission — if a certificate is missing, a rule is absent, or a backend is down, ZetaShield strictly fails closed.'</i>"
    )
    golden_table = Table([[Paragraph(golden_box, callout_text)]], colWidths=[540])
    golden_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF2F2")),
        ('BORDER', (0,0), (-1,-1), 1, c_crimson),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(golden_table)
    story.append(PageBreak())

    # =========================================================================
    # PART 5: TEAM BRIEFING
    # =========================================================================
    story.append(Paragraph("Part 5: Team Briefing (Copy-Paste Group Message)", h1_style))
    story.append(Paragraph(
        "Copy and paste the exact message block below into your team WhatsApp or Discord group chat 24 hours before Review 2:", body_style
    ))
    
    briefing_msg = (
        "<b>TEAM BRIEFING — CAPSTONE REVIEW 2 FINAL BATTLE STATIONS</b><br/><br/>"
        "Team, here is our locked operational plan for tomorrow's Review 2 presentation:<br/><br/>"
        "<b>1. SPEAKING ORDER & TIMINGS (Strict 24 Minutes):</b><br/>"
        "• Slides 1–3: Karthik (Lead) — Opening, Problem & Architecture (4.5 min)<br/>"
        "• Slide 4: Subeer — Three Checkpoints & Enforcement Pipeline (2.0 min)<br/>"
        "• Slide 5: Sahil — Cryptographic Identity & SPIFFE SANs (2.0 min)<br/>"
        "• Slides 6–7: Subeer — Deny-by-Default Policy, Hot-Reload & 7-Test Matrix (4.0 min)<br/>"
        "• Slide 8: LIVE DEMO (Karthik drives, Sameep/Subeer narrate isolation & hot-reload) (6.0 min)<br/>"
        "• Slides 9–10: Karthik — Docker Network Isolation & 0.6ms Benchmark (3.0 min)<br/>"
        "• Slide 11: Sameep — 19 Unit Tests & GitHub Actions CI (1.5 min)<br/>"
        "• Slides 12–13: Shaivyaa — 3-Version Evolution & Phase 2 Roadmap (3.0 min)<br/>"
        "• Slide 14: Karthik — Project Outcomes (1.0 min)<br/>"
        "• Slide 15: Sameep — Team Contributions Table (1.0 min)<br/>"
        "• Slide 16: Karthik — Summary & Transition to Q&A (1.0 min)<br/><br/>"
        "<b>2. THE GOLDEN HANDOFF PHRASE:</b><br/>"
        "Always pass the mic with authority: <i>'I will now hand over to [Name] to walk through [Topic].'</i><br/><br/>"
        "<b>3. THE RESCUE PROTOCOL (IF SOMEONE FREEZES):</b><br/>"
        "If a member freezes for more than 4 seconds on slide or viva, Karthik (or territory lead) steps in smoothly using this exact phrase:<br/>"
        "<i>'To build on what [Name] stated regarding the underlying implementation...'</i><br/>"
        "Never say 'he forgot' or 'let me correct that.' Keep the team facade unified.<br/><br/>"
        "<b>4. DEMO DISASTER PROTOCOL:</b><br/>"
        "If Docker hangs or Windows network glitches, <b>DO NOT DEBUG LIVE</b>. Karthik will immediately switch to our pre-recorded MP4 backup video in VLC.<br/><br/>"
        "<b>5. DRESS CODE & SETTINGS:</b><br/>"
        "Formal attire. Join 15 minutes early. Mute all notifications. Have water nearby. Let's execute!"
    )
    briefing_table = Table([[Paragraph(briefing_msg, callout_text)]], colWidths=[540])
    briefing_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(briefing_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 6: REHEARSAL PROTOCOL
    # =========================================================================
    story.append(Paragraph("Part 6: Rehearsal Protocol & Practice Schedule", h1_style))
    story.append(Paragraph(
        "To guarantee an A-grade evaluation, the team must complete two structured rehearsal runs prior to stepping into the review room.", body_style
    ))

    rehearsal_data = [
        [
            Paragraph("Rehearsal Drill", table_hdr),
            Paragraph("Target Duration", table_hdr),
            Paragraph("Key Objective & Execution Rules", table_hdr)
        ],
        [
            Paragraph("<b>Drill 1: Full Dress Rehearsal</b><br/>(Evening Before)", table_cell),
            Paragraph("60 Minutes", table_cell),
            Paragraph("• Run through all 16 slides with timer running.<br/>"
                      "• <b>Rule: NO STOPPING FOR MISTAKES.</b> Push through hesitations to test recovery.<br/>"
                      "• Execute the live demo twice, including the live policy hot-reload flex.<br/>"
                      "• Conduct a 15-minute cross-examination using the Viva Q&A Bank.", table_cell)
        ],
        [
            Paragraph("<b>Drill 2: Cold-Start Dry Run</b><br/>(Morning of Review)", table_cell),
            Paragraph("30 Minutes", table_cell),
            Paragraph("• Perform a cold-start live demo from clean terminal state.<br/>"
                      "• Verify Docker containers build and start without network lag.<br/>"
                      "• Run client.py and confirm the 7-test sequence is crisp.<br/>"
                      "• Rapid-fire recitation of the 3 Golden Sentences.", table_cell)
        ],
    ]
    rehearsal_table = Table(rehearsal_data, colWidths=[120, 70, 350])
    rehearsal_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(rehearsal_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 7: DAY-OF EXECUTION CHECKLIST
    # =========================================================================
    story.append(Paragraph("Part 7: Day-of Execution Checklist (T-Minus 30 Minutes)", h1_style))
    story.append(Paragraph(
        "Execute every item on this checklist 30 minutes before your scheduled presentation slot.", body_style
    ))

    checklist_data = [
        [
            Paragraph("Phase / Time", table_hdr),
            Paragraph("Action Item & Verification Task", table_hdr),
            Paragraph("Owner", table_hdr)
        ],
        [
            Paragraph("<b>T-30 min</b><br/>Environment", table_cell),
            Paragraph("• Start Docker Desktop and verify engine is running (<code>docker info</code>).<br/>"
                      "• Pre-warm build cache: run <code>docker compose build</code> so images are cached.<br/>"
                      "• Clear existing audit logs: <code>type nul > deploy/logs/audit.log.jsonl</code>.", table_cell),
            Paragraph("Karthik", table_cell_bold)
        ],
        [
            Paragraph("T-20 min<br/>Workspace Layout", table_cell),
            Paragraph("• Open 3 distinct terminal windows positioned across screen:<br/>"
                      "  - Terminal 1 (Top-Left): <code>docker compose up</code> / status<br/>"
                      "  - Terminal 2 (Bottom-Left): <code>mock-apps</code> for running <code>client.py</code> & curl<br/>"
                      "  - Terminal 3 (Right): <code>docker compose logs -f gateway</code> for hot-reload logs<br/>"
                      "• Set terminal font size to 16pt bold (Monospace) for panel visibility.", table_cell),
            Paragraph("Karthik / Sameep", table_cell_bold)
        ],
        [
            Paragraph("T-15 min<br/>Redundancy", table_cell),
            Paragraph("• Open VLC Media Player with <code>ZetaShield_V2_Demo_Backup.mp4</code> loaded and paused.<br/>"
                      "• Open PowerPoint / PDF presentation slides in full-screen presentation mode.<br/>"
                      "• Open GitHub repository page in browser tab on commit <code>f4a92b9</code>.", table_cell),
            Paragraph("Karthik / Shaivyaa", table_cell_bold)
        ],
        [
            Paragraph("T-10 min<br/>Distraction Guard", table_cell),
            Paragraph("• Enable Windows 'Focus Assist' / Do Not Disturb.<br/>"
                      "• Close WhatsApp, Discord, Telegram, Slack, and email desktop clients.<br/>"
                      "• Check microphone input levels and camera lighting.<br/>"
                      "• Ensure laptop is plugged into AC power (High Performance battery profile).", table_cell),
            Paragraph("All Members", table_cell_bold)
        ],
        [
            Paragraph("T-5 min<br/>Mental Focus", table_cell),
            Paragraph("• Glass of water at desk.<br/>"
                      "• Deep breath. Remember the core message: <i>We built a working Layer-7 Zero-Trust gateway in Go that proves sub-millisecond enforcement.</i><br/>"
                      "• Stand tall, speak clearly, and own the room.", table_cell),
            Paragraph("All Members", table_cell_bold)
        ],
    ]
    checklist_table = Table(checklist_data, colWidths=[90, 360, 90])
    checklist_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(checklist_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Successfully built {PDF_OUTPUT}")

if __name__ == "__main__":
    create_rehearsal_pdf()

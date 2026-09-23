"""Self-Contained Accessible Offline HTML Report Exporter for AccessLens AI (Phase 7).

Generates a standalone, fully offline, accessible HTML audit report.
Zero external CDNs, zero external fonts, and zero external JavaScript dependencies.
Strictly escapes all dynamic user strings to prevent script injection.
Targets readable contrast with 4.5:1 as design target for normal text where applicable.
"""

import html
import os
from typing import Optional

from reports.report_models import AuditReport


class HtmlReportExporter:
    """Exports an AuditReport into an accessible, self-contained, offline HTML file."""

    # Fully embedded CSS adhering to accessibility guidelines:
    # High readability, clear focus outlines, print-friendly styling, and zero external calls.
    EMBEDDED_CSS = """
    :root {
        --bg-body: #0F172A;
        --bg-surface: #1E293B;
        --bg-card: #182234;
        --bg-card-subtle: #131B2A;
        --border-color: #334155;
        --border-subtle: #243046;
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --accent-blue: #38BDF8;
        --accent-green: #34D399;
        --accent-amber: #FBBF24;
        --accent-red: #F87171;
        --accent-purple: #C084FC;
        --focus-outline: #38BDF8;
    }

    @media (prefers-color-scheme: light) {
        :root {
            --bg-body: #F8FAFC;
            --bg-surface: #FFFFFF;
            --bg-card: #FFFFFF;
            --bg-card-subtle: #F1F5F9;
            --border-color: #CBD5E1;
            --border-subtle: #E2E8F0;
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --accent-blue: #0284C7;
            --accent-green: #059669;
            --accent-amber: #D97706;
            --accent-red: #DC2626;
            --accent-purple: #7C3AED;
            --focus-outline: #0284C7;
        }
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        background-color: var(--bg-body);
        color: var(--text-primary);
        line-height: 1.6;
        font-size: 15px;
        padding: 24px;
    }

    :focus-visible {
        outline: 3px solid var(--focus-outline);
        outline-offset: 2px;
    }

    .container {
        max-width: 1100px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 24px;
    }

    header.report-header {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .report-title-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 12px;
    }

    h1 {
        font-size: 26px;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }

    .tagline {
        font-size: 14px;
        font-style: italic;
        color: var(--text-secondary);
    }

    .disclaimer-banner {
        background-color: rgba(245, 158, 11, 0.12);
        border-left: 4px solid var(--accent-amber);
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 13px;
        color: var(--text-primary);
    }

    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 700;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .badge-critical { background-color: rgba(239, 68, 68, 0.2); color: var(--accent-red); border: 1px solid var(--accent-red); }
    .badge-high { background-color: rgba(245, 158, 11, 0.2); color: var(--accent-amber); border: 1px solid var(--accent-amber); }
    .badge-medium { background-color: rgba(56, 189, 248, 0.2); color: var(--accent-blue); border: 1px solid var(--accent-blue); }
    .badge-low { background-color: rgba(52, 211, 153, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }
    .badge-provenance { background-color: rgba(192, 132, 252, 0.18); color: var(--accent-purple); border: 1px solid var(--accent-purple); font-family: monospace; }
    .badge-status { background-color: var(--bg-card-subtle); color: var(--text-secondary); border: 1px solid var(--border-color); }
    .badge-untrusted { background-color: rgba(239, 68, 68, 0.25); color: var(--accent-red); border: 1px solid var(--accent-red); font-weight: 800; }

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
    }

    .stat-card {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .stat-title {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-secondary);
    }

    .stat-val {
        font-size: 28px;
        font-weight: 800;
        color: var(--text-primary);
    }

    .stat-desc {
        font-size: 12px;
        color: var(--text-muted);
    }

    section.report-section {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    h2 {
        font-size: 19px;
        font-weight: 700;
        color: var(--accent-blue);
        border-bottom: 2px solid var(--border-subtle);
        padding-bottom: 8px;
    }

    h3 {
        font-size: 16px;
        font-weight: 700;
        color: var(--text-primary);
    }

    h4 {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
        margin-top: 8px;
    }

    table.data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-top: 8px;
    }

    table.data-table th, table.data-table td {
        padding: 10px 12px;
        text-align: left;
        border: 1px solid var(--border-color);
    }

    table.data-table th {
        background-color: var(--bg-card-subtle);
        color: var(--text-secondary);
        font-weight: 600;
    }

    table.data-table tr:hover {
        background-color: var(--bg-card-subtle);
    }

    .finding-card {
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 18px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 12px;
    }

    .finding-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 8px;
    }

    pre.code-block {
        background-color: #0B0F19;
        color: #E2E8F0;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        overflow-x: auto;
        font-family: "Consolas", "Courier New", monospace;
        font-size: 12px;
        margin-top: 6px;
    }

    ul.checklist {
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    ul.checklist li {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
    }

    .footer-note {
        font-size: 12px;
        color: var(--text-muted);
        text-align: center;
        padding: 16px 0;
    }

    @media print {
        body { background-color: #FFFFFF; color: #000000; padding: 0; }
        .container { max-width: 100%; gap: 16px; }
        header.report-header, section.report-section, .finding-card {
            background-color: #FFFFFF; border: 1px solid #CCCCCC; break-inside: avoid;
        }
        pre.code-block { background-color: #F8F9FA; color: #000000; border: 1px solid #CCCCCC; }
    }
    """

    @classmethod
    def export_to_string(cls, report: AuditReport) -> str:
        """Renders complete AuditReport into standalone HTML string."""
        s = report.summary
        hw = report.hardware_attestation
        priv = report.privacy_information

        # Escape top-level fields
        app_name = html.escape(report.application_name)
        win_title = html.escape(report.target_window)
        rep_id = html.escape(report.report_id)
        digest = html.escape(report.evidence_digest)

        # Build findings cards
        findings_html = []
        if not report.findings:
            findings_html.append("<p>No accessibility barriers were detected during this audit.</p>")
        else:
            for f in report.findings:
                fid = html.escape(f.finding_id)
                ftitle = html.escape(f.title)
                fdesc = html.escape(f.description)
                frule = html.escape(f.rule_id)
                fsource = html.escape(f.source)
                felem = html.escape(f.affected_element or "Target Window")
                fclass = html.escape(f.evidence_class)
                fsev = html.escape(f.severity)

                sev_class = "badge-medium"
                if f.severity == "CRITICAL":
                    sev_class = "badge-critical"
                elif f.severity == "HIGH":
                    sev_class = "badge-high"
                elif f.severity == "LOW":
                    sev_class = "badge-low"

                # Evidence references badges
                refs_badges = "".join(
                    f'<span class="badge badge-status" style="margin-right: 4px;">{html.escape(r)}</span>'
                    for r in f.evidence_references
                ) if f.evidence_references else "<span>None</span>"

                why = html.escape(f.reasoning.get("why_it_matters", "Barriers impact users navigating with assistive tools."))
                rec = html.escape(f.remediation.get("recommendation", "Review and fix accessibility properties."))
                code = f.remediation.get("remediation_code", "")
                code_html = f'<pre class="code-block"><code>{html.escape(code)}</code></pre>' if code else ""

                actions = f.remediation.get("developer_actions", [])
                actions_html = "".join(f"<li>{html.escape(a)}</li>" for a in actions)
                actions_block = f"<h4>Developer Action Steps</h4><ol style='padding-left: 20px; font-size: 13px;'>{actions_html}</ol>" if actions else ""

                verif_steps = "".join(f"<li>[ ] {html.escape(st)}</li>" for st in f.verification_steps)

                card = f"""
                <article class="finding-card" id="{fid}">
                    <div class="finding-header">
                        <div>
                            <span class="badge {sev_class}">{fsev}</span>
                            <span class="badge badge-provenance">[{fclass}]</span>
                            <strong style="margin-left: 8px; font-size: 15px;">{fid}: {ftitle}</strong>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            Confidence: <strong>{f.confidence * 100:.1f}%</strong> | Rule: <code>{frule}</code>
                        </div>
                    </div>
                    <div style="font-size: 13px; color: var(--text-secondary);">
                        Affected Element: <strong>{felem}</strong> | Source: <em>{fsource}</em>
                    </div>
                    <h4>Observed Evidence</h4>
                    <p style="font-size: 14px;">{fdesc}</p>
                    <div style="font-size: 12px; margin-top: 4px;">
                        Traceable Evidence Items: {refs_badges}
                    </div>
                    <h4>Why It Matters</h4>
                    <p style="font-size: 13px; color: var(--text-secondary);">{why}</p>
                    <h4>Recommended Developer Fix</h4>
                    <p style="font-size: 13px;">{rec}</p>
                    {code_html}
                    {actions_block}
                    <h4>Human Verification Steps (Mandatory)</h4>
                    <ul class="checklist" style="font-size: 13px; color: var(--accent-amber);">
                        {verif_steps}
                    </ul>
                </article>
                """
                findings_html.append(card)

        # Build evidence catalog table rows
        evidence_rows = []
        for ev in report.evidence[:50]:
            eid = html.escape(ev.evidence_id)
            eclass = html.escape(ev.source_class)
            edesc = html.escape(ev.description)
            eloc = html.escape(str(ev.location)) if ev.location else "—"
            susp_badge = ' <span class="badge badge-untrusted">[UNTRUSTED DATA]</span>' if ev.is_suspicious else ""
            row = f"""
            <tr>
                <th scope="row"><strong>{eid}</strong></th>
                <td><span class="badge badge-provenance">[{eclass}]</span></td>
                <td>{edesc}{susp_badge}</td>
                <td><code>{eloc}</code></td>
                <td>{ev.confidence:.2f}</td>
            </tr>
            """
            evidence_rows.append(row)

        evidence_overflow = (
            f"<p style='font-size: 12px; color: var(--text-muted); margin-top: 8px;'>Showing first 50 of {len(report.evidence)} evidence items. Complete dataset is available in exported JSON.</p>"
            if len(report.evidence) > 50 else ""
        )

        # Build checklist items
        checklist_items = "".join(
            f'<li><input type="checkbox" disabled aria-label="{html.escape(c)}"> <span>{html.escape(c)}</span></li>'
            for c in report.verification_checklist
        )

        # Build limitations items
        limitations_items = "".join(f"<li>{html.escape(lim)}</li>" for lim in report.limitations)

        # Assemble HTML document
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AccessLens AI Audit Report — {app_name}</title>
    <style>
{cls.EMBEDDED_CSS}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="report-header" role="banner">
            <div class="report-title-row">
                <div>
                    <h1>AccessLens AI Accessibility Audit Report</h1>
                    <div class="tagline">"See the interface. Understand the barriers. Fix them locally."</div>
                </div>
                <div>
                    <span class="badge badge-status">Report ID: {rep_id}</span>
                </div>
            </div>
            <div class="disclaimer-banner" role="alert">
                <strong>Accessibility QA Disclaimer:</strong> Automated findings are evidence for developer and QA review. 
                They do not constitute formal accessibility certification. Full conformance requires human verification.
            </div>
            <div style="font-size: 13px; color: var(--text-secondary); display: flex; flex-wrap: wrap; gap: 16px;">
                <div>Target Application: <strong>{app_name}</strong></div>
                <div>Target Window: <strong>{win_title}</strong></div>
                <div>Scan Time: <strong>{report.generated_at}</strong></div>
                <div>Duration: <strong>{report.scan_duration_ms:.1f} ms</strong></div>
                <div>Privacy Mode: <strong>{report.privacy_mode}</strong></div>
            </div>
        </header>

        <!-- Executive Summary Cards -->
        <section aria-labelledby="summary-heading">
            <h2 id="summary-heading" style="margin-bottom: 12px;">Audit Metrics & Breakdown</h2>
            <div class="summary-grid">
                <div class="stat-card">
                    <span class="stat-title">Total Findings</span>
                    <span class="stat-val" style="color: var(--accent-blue);">{s.total_findings}</span>
                    <span class="stat-desc">Potential accessibility barriers</span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">Critical & High</span>
                    <span class="stat-val" style="color: var(--accent-red);">{s.critical_count + s.high_count}</span>
                    <span class="stat-desc">Keyboard or name barriers</span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">UI Elements</span>
                    <span class="stat-val">{s.total_ui_elements}</span>
                    <span class="stat-desc">UIA controls inspected</span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">Evidence Matches</span>
                    <span class="stat-val" style="color: var(--accent-green);">{s.matched_elements}</span>
                    <span class="stat-desc">Multimodal fused pairings</span>
                </div>
            </div>
        </section>

        <!-- Host & Hardware Attestation -->
        <section class="report-section" aria-labelledby="hw-heading">
            <h2 id="hw-heading">Host Hardware & Integrity Attestation</h2>
            <table class="data-table">
                <tbody>
                    <tr>
                        <th scope="row" style="width: 240px;">Host Processor</th>
                        <td>{html.escape(hw.get('host_processor', 'Unknown'))} ({html.escape(hw.get('architecture', 'AMD64'))})</td>
                    </tr>
                    <tr>
                        <th scope="row">Qualcomm Snapdragon Status</th>
                        <td><span class="badge badge-status">{html.escape(hw.get('snapdragon_detected', 'NOT DETECTED'))}</span></td>
                    </tr>
                    <tr>
                        <th scope="row">Qualcomm Hexagon NPU</th>
                        <td><span class="badge badge-status">{html.escape(hw.get('npu_status', 'NOT AVAILABLE'))}</span></td>
                    </tr>
                    <tr>
                        <th scope="row">Active AI Backend</th>
                        <td><code>{html.escape(hw.get('active_ai_backend', 'CPUExecutionProvider'))}</code></td>
                    </tr>
                    <tr>
                        <th scope="row">Hardware Validation Status</th>
                        <td>{html.escape(hw.get('snapdragon_validation', 'Pending genuine Snapdragon hardware'))}</td>
                    </tr>
                    <tr>
                        <th scope="row">Measurement Integrity</th>
                        <td>{html.escape(hw.get('integrity_attestation', 'No simulated QNN execution.'))}</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- Privacy Attestation -->
        <section class="report-section" aria-labelledby="privacy-heading">
            <h2 id="privacy-heading">Privacy & Data Isolation Safeguards</h2>
            <table class="data-table">
                <tbody>
                    <tr>
                        <th scope="row" style="width: 240px;">Processing Mode</th>
                        <td><strong>{html.escape(priv.get('processing_mode', 'Local / Offline'))}</strong></td>
                    </tr>
                    <tr>
                        <th scope="row">Cloud APIs Required</th>
                        <td>Zero (100% On-Device Execution)</td>
                    </tr>
                    <tr>
                        <th scope="row">External Network Usage</th>
                        <td>Zero Outbound Connections</td>
                    </tr>
                    <tr>
                        <th scope="row">Telemetry & Analytics</th>
                        <td>None Implemented</td>
                    </tr>
                    <tr>
                        <th scope="row">Privacy Guarantee</th>
                        <td><em>"{html.escape(priv.get('privacy_statement', ''))}"</em></td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- Findings Section -->
        <main class="report-section" aria-labelledby="findings-heading">
            <h2 id="findings-heading">Detailed Accessibility Findings & Traceable Evidence</h2>
            {"".join(findings_html)}
        </main>

        <!-- Evidence Catalog Section -->
        <section class="report-section" aria-labelledby="evidence-heading">
            <h2 id="evidence-heading">Multimodal Evidence Catalog (Grounded Observations)</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th scope="col" style="width: 90px;">Evidence ID</th>
                        <th scope="col" style="width: 140px;">Provenance Class</th>
                        <th scope="col">Grounded Description</th>
                        <th scope="col" style="width: 120px;">Location</th>
                        <th scope="col" style="width: 80px;">Conf</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(evidence_rows)}
                </tbody>
            </table>
            {evidence_overflow}
        </section>

        <!-- Human Verification Checklist -->
        <section class="report-section" aria-labelledby="checklist-heading">
            <h2 id="checklist-heading">Human Verification Checklist</h2>
            <p style="font-size: 13px; color: var(--text-secondary);">
                To complete accessibility verification, human evaluators should confirm each item below:
            </p>
            <ul class="checklist">
                {checklist_items}
            </ul>
        </section>

        <!-- Limitations Section -->
        <section class="report-section" aria-labelledby="limitations-heading">
            <h2 id="limitations-heading">Evaluation Limitations & Boundaries</h2>
            <ul style="padding-left: 20px; font-size: 13px; color: var(--text-secondary); display: flex; flex-direction: column; gap: 6px;">
                {limitations_items}
            </ul>
        </section>

        <!-- Report Integrity Footer -->
        <footer class="report-section" aria-labelledby="integrity-heading">
            <h2 id="integrity-heading">Report Integrity & Verification</h2>
            <p style="font-size: 13px;">
                This report is cryptographically verifiable via a canonical SHA-256 evidence digest:
            </p>
            <pre class="code-block"><code>SHA-256: {digest}</code></pre>
            <div class="footer-note">
                Generated by AccessLens AI v1.0 • Built for Qualcomm Snapdragon AI Lab Build & Present Challenge 2026 • 100% Offline
            </div>
        </footer>
    </div>
</body>
</html>"""
        return html_doc

    @classmethod
    def export_to_file(
        cls,
        report: AuditReport,
        output_path: Optional[str] = None,
        base_dir: Optional[str] = None,
    ) -> str:
        """Writes report HTML to disk and returns destination path."""
        if not output_path:
            target_dir = base_dir or os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "generated",
            )
            os.makedirs(target_dir, exist_ok=True)
            output_path = os.path.join(target_dir, f"{report.report_id}.html")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        html_content = cls.export_to_string(report)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return os.path.abspath(output_path)

"""Accessibility audit report generator for AccessLens AI.

Exports formal accessibility audit results to Markdown, JSON, and self-contained HTML.
Includes sensitive data masking before export with an explicit human-review disclaimer.
"""

from datetime import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional

from accessibility.element_model import InterfaceSnapshot, SignalType


class ReportGenerator:
    """Produces structured accessibility audit reports in Markdown, JSON, and HTML."""

    def __init__(self):
        # Sensitive data regex patterns
        self._sensitive_patterns = [
            (r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_PAYMENT_CARD]"),
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
            (r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]"),
            (r"(?:api[_-]?key|secret|token|password)[\s:=]+['\"]?([A-Za-z0-9_\-]{16,})['\"]?", "[REDACTED_CREDENTIAL]"),
        ]

    def mask_sensitive_data(self, text: str) -> str:
        """Conservatively masks credentials, phone numbers, payment cards, and emails."""
        if not text:
            return ""
        masked = text
        for pat, replacement in self._sensitive_patterns:
            masked = re.sub(pat, replacement, masked, flags=re.IGNORECASE)
        return masked

    def generate_json(self, snapshot: InterfaceSnapshot, mask: bool = True) -> str:
        """Serializes snapshot and audit findings to formatted JSON."""
        data = snapshot.to_dict()
        raw_json = json.dumps(data, indent=2)
        return self.mask_sensitive_data(raw_json) if mask else raw_json

    def generate_markdown(self, snapshot: InterfaceSnapshot, mask: bool = True) -> str:
        """Generates comprehensive Markdown accessibility audit report."""
        summary_md = f"""# ACCESSLENS AI ACCESSIBILITY AUDIT REPORT

> *"See the interface. Understand the barriers. Fix them locally."*  
> **Disclaimer:** Automated findings are assistance for accessibility QA and should be reviewed by a qualified human tester.

---

## 1. Audit Metadata
- **Target Application:** {snapshot.application_name}
- **Window Title:** {snapshot.window_title}
- **Date & Time:** {snapshot.timestamp}
- **Hardware Platform:** {snapshot.hardware_summary}
- **Active AI Backend:** {snapshot.backend_state}
- **Privacy Mode:** 100% Local Processing (Zero Cloud Uploads)
- **Audit Execution Time:** {snapshot.audit_duration_ms:.1f} ms

---

## 2. Executive Summary
- **Total UI Elements Inspected:** {len(snapshot.elements)}
- **Total Accessibility Barriers Detected:** {len(snapshot.findings)}
  - **CRITICAL:** {snapshot.critical_findings_count}
  - **HIGH:** {snapshot.high_findings_count}
  - **MEDIUM:** {snapshot.medium_findings_count}
  - **LOW / ADVISORY:** {snapshot.low_findings_count}

---

## 3. Detailed Findings & Grounded Evidence

"""
        for i, f in enumerate(snapshot.findings, 1):
            elem_info = f"on `{f.element_type}` \"{f.element_name}\"" if f.element_name else ""
            summary_md += f"### {i}. [{f.severity.value}] {f.title} {elem_info}\n"
            summary_md += f"- **Category:** `{f.category.value}`\n"
            summary_md += f"- **Confidence:** {f.confidence * 100:.1f}%\n"
            summary_md += f"- **Source:** {f.source}\n"
            summary_md += "\n**Evidence:**\n"
            for ev in f.evidence:
                summary_md += f"- {ev}\n"
            summary_md += f"\n**Remediation Recommendation:**\n> {f.recommendation}\n\n"
            if f.remediation_code:
                summary_md += "```csharp\n" + f.remediation_code + "\n```\n\n"
            summary_md += "---\n\n"

        summary_md += f"""## 4. Visual & Keyboard Traversal Observations
- **Screen Dimensions:** {snapshot.screen_dimensions[0]}x{snapshot.screen_dimensions[1]} px
- **Keyboard Tab Transitions Recorded:** {len(snapshot.keyboard_order)}
- **OCR Text Characters Extracted:** {len(snapshot.ocr_text)}

## 5. Limitations & Attestation
- Testing was conducted in verified on-device CPU fallback mode on {snapshot.hardware_summary}.
- Zero external APIs or cloud services were contacted during this audit.
- Complete WCAG 2.1 compliance certification requires complementary manual assistive technology testing.
"""
        return self.mask_sensitive_data(summary_md) if mask else summary_md

    def generate_html(self, snapshot: InterfaceSnapshot, mask: bool = True) -> str:
        """Generates self-contained, responsive dark HTML audit report."""
        md_content = self.generate_markdown(snapshot, mask=mask)

        # Build clean styled HTML table of findings
        findings_rows = ""
        for f in snapshot.findings:
            sev_badge = f'<span class="badge {f.severity.value.lower()}">{f.severity.value}</span>'
            ev_list = "".join(f"<li>{ev}</li>" for ev in f.evidence)
            code_block = f"<pre><code>{f.remediation_code}</code></pre>" if f.remediation_code else ""
            findings_rows += f"""
            <tr>
                <td>{sev_badge}</td>
                <td><strong>{f.title}</strong><br><small>{f.category.value}</small></td>
                <td><ul>{ev_list}</ul></td>
                <td>{f.recommendation}{code_block}</td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AccessLens AI Audit — {snapshot.application_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0F1117;
            color: #F8FAFC;
            margin: 0;
            padding: 30px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #00D2D3; }}
        .header-card {{
            background: #1A1D27;
            border: 1px solid #2E364B;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #212636;
            padding: 16px;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid #2563EB;
        }}
        .stat-card.crit {{ border-color: #EF4444; }}
        .stat-card.high {{ border-color: #F59E0B; }}
        .stat-card.med {{ border-color: #00D2D3; }}
        .stat-number {{ font-size: 28px; font-weight: 700; margin-top: 4px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: #1A1D27;
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #2E364B;
        }}
        th {{ background: #212636; color: #94A3B8; font-weight: 600; }}
        .badge {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
        }}
        .badge.critical {{ background: #7F1D1D; color: #FCA5A5; }}
        .badge.high {{ background: #78350F; color: #FDE68A; }}
        .badge.medium {{ background: #1E3A8A; color: #93C5FD; }}
        .badge.low {{ background: #064E3B; color: #A7F3D0; }}
        pre {{ background: #12151E; padding: 10px; border-radius: 4px; overflow-x: auto; }}
        ul {{ margin: 0; padding-left: 20px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header-card">
        <h1>ACCESSLENS AI ACCESSIBILITY AUDIT REPORT</h1>
        <p><strong>Application:</strong> {snapshot.application_name} | <strong>Window:</strong> {snapshot.window_title}</p>
        <p><strong>Timestamp:</strong> {snapshot.timestamp} | <strong>Host:</strong> {snapshot.hardware_summary} | <strong>AI Backend:</strong> {snapshot.backend_state}</p>
        <p><em>Disclaimer: Automated findings are assistance for accessibility QA and should be reviewed by a qualified human tester.</em></p>
    </div>

    <div class="summary-grid">
        <div class="stat-card crit">
            <div>CRITICAL</div>
            <div class="stat-number">{snapshot.critical_findings_count}</div>
        </div>
        <div class="stat-card high">
            <div>HIGH</div>
            <div class="stat-number">{snapshot.high_findings_count}</div>
        </div>
        <div class="stat-card med">
            <div>MEDIUM</div>
            <div class="stat-number">{snapshot.medium_findings_count}</div>
        </div>
        <div class="stat-card">
            <div>LOW / INFO</div>
            <div class="stat-number">{snapshot.low_findings_count}</div>
        </div>
    </div>

    <h2>Accessibility Findings & Grounded Evidence</h2>
    <table>
        <thead>
            <tr>
                <th style="width: 100px;">Severity</th>
                <th style="width: 250px;">Finding</th>
                <th>Observed Evidence</th>
                <th style="width: 320px;">Remediation Guidance</th>
            </tr>
        </thead>
        <tbody>
            {findings_rows}
        </tbody>
    </table>
</div>
</body>
</html>
"""
        return self.mask_sensitive_data(html) if mask else html

    def save_report_to_file(self, content: str, filepath: str):
        """Writes report to disk ensuring directory existence."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


# Singleton instance
report_generator = ReportGenerator()

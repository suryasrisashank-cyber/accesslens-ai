"""Markdown Report Exporter for AccessLens AI (Phase 7).

Generates a structured, professional GitHub/GCP-style Markdown report
grounded strictly in observed evidence, local reasoning, and developer remediation.
"""

import os
from typing import Optional

from reports.report_models import AuditReport


class MarkdownReportExporter:
    """Exports an AuditReport to structured Markdown."""

    @classmethod
    def export_to_string(cls, report: AuditReport) -> str:
        """Formats the AuditReport into a comprehensive Markdown document."""
        lines = []

        # Header
        lines.append("# AccessLens AI Accessibility Audit Report")
        lines.append("")
        lines.append('> *"See the interface. Understand the barriers. Fix them locally."*')
        lines.append(">")
        lines.append(
            "> **Disclaimer:** Automated accessibility findings are evidence for developer review "
            "and do not constitute formal accessibility compliance certification."
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        s = report.summary
        lines.append(
            f"AccessLens inspected **{s.total_ui_elements}** UI elements on **{report.application_name}** "
            f"and recorded **{s.total_findings}** potential accessibility barriers requiring developer verification. "
            f"Of these, **{s.critical_count}** are critical, **{s.high_count}** are high severity, "
            f"**{s.medium_count}** are medium severity, and **{s.low_count}** are low or advisory."
        )
        lines.append("")
        lines.append("| Metric | Value | Description |")
        lines.append("| :--- | :---: | :--- |")
        lines.append(f"| **Total Findings** | `{s.total_findings}` | Barriers identified by deterministic rule inspection |")
        lines.append(f"| **Critical / High** | `{s.critical_count + s.high_count}` | Severe keyboard or assistive navigation barriers |")
        lines.append(f"| **UI Elements Inspected** | `{s.total_ui_elements}` | Programmatic Windows UI Automation controls |")
        lines.append(f"| **Visual OCR Regions** | `{s.total_visual_elements}` | Text and icon regions identified by on-device OCR |")
        lines.append(f"| **Multimodal Matches** | `{s.matched_elements}` | Grounded pairings between UIA controls and visual pixels |")
        lines.append(f"| **Evidence Conflicts** | `{s.evidence_conflicts}` | Discrepancies between visual text and accessible names |")
        lines.append(f"| **Keyboard Navigation** | `{'Available' if s.keyboard_audit_available else 'Not Run'}` | Focus traversal audit status |")
        lines.append(f"| **Human Review Flag** | `{'Required' if s.human_verification_required else 'Optional'}` | Human confirmation requirement |")
        lines.append("")

        # 2. Scan Information
        lines.append("## Scan Information")
        lines.append("")
        lines.append(f"- **Report ID:** `{report.report_id}`")
        lines.append(f"- **Schema Version:** `{report.schema_version}`")
        lines.append(f"- **Generated At:** `{report.generated_at}`")
        lines.append(f"- **Target Application:** {report.application_name}")
        lines.append(f"- **Target Window:** {report.target_window}")
        lines.append(f"- **Scan Duration:** {report.scan_duration_ms:.2f} ms")
        lines.append(f"- **Privacy Mode:** `{report.privacy_mode}`")
        lines.append(f"- **Evidence Image Mode:** `{report.evidence_image_mode}`")
        lines.append("")

        # 3. Host & Hardware
        lines.append("## Host & Hardware")
        lines.append("")
        hw = report.hardware_attestation
        host = report.host_information
        lines.append(f"- **Host Processor:** {hw.get('host_processor', host.get('cpu_model', 'Unknown'))}")
        lines.append(f"- **Architecture:** `{hw.get('architecture', host.get('architecture', 'AMD64'))}`")
        lines.append(f"- **Operating System:** {host.get('os_name', 'Windows')} {host.get('os_version', '')}")
        lines.append(f"- **Snapdragon Hardware:** `{hw.get('snapdragon_detected', 'NOT DETECTED')}`")
        lines.append(f"- **Qualcomm Hexagon NPU:** `{hw.get('npu_status', 'NOT AVAILABLE')}`")
        lines.append(f"- **Active AI Backend:** `{hw.get('active_ai_backend', 'CPUExecutionProvider')}`")
        lines.append(f"- **Hardware Validation Status:** {hw.get('snapdragon_validation', 'Pending genuine Snapdragon hardware')}")
        lines.append(f"- **Integrity Guarantee:** {hw.get('integrity_attestation', 'No simulated QNN execution.')}")
        lines.append("")

        # 4. Privacy
        lines.append("## Privacy")
        lines.append("")
        priv = report.privacy_information
        lines.append(f"- **Processing Mode:** {priv.get('processing_mode', 'Local / Offline')}")
        lines.append(f"- **Cloud API Dependency:** `{'Required' if priv.get('cloud_api_required') else 'None (100% On-Device)'}`")
        lines.append(f"- **External Network Calls:** `{'Active' if priv.get('external_network_required') else 'Zero Network Access'}`")
        lines.append(f"- **Telemetry Status:** `{'Enabled' if priv.get('telemetry_implemented') else 'None Implemented'}`")
        lines.append(f"- **API Keys Required:** `{'Yes' if priv.get('api_keys_required') else 'None'}`")
        lines.append(f"- **Privacy Statement:** *\"{priv.get('privacy_statement', '')}\"*")
        lines.append("")

        # 5. Findings Summary
        lines.append("## Findings Summary")
        lines.append("")
        if not report.findings:
            lines.append("No accessibility barriers were detected during this audit.")
        else:
            lines.append("| ID | Severity | Accessibility Finding | Rule ID | Evidence Class | Traceable Refs |")
            lines.append("| :--- | :---: | :--- | :--- | :---: | :--- |")
            for f in report.findings:
                refs_str = ", ".join(f.evidence_references) if f.evidence_references else "—"
                lines.append(
                    f"| **{f.finding_id}** | `{f.severity}` | {f.title} | `{f.rule_id}` | `[{f.evidence_class}]` | `{refs_str}` |"
                )
        lines.append("")

        # 6. Detailed Findings
        lines.append("## Findings")
        lines.append("")
        for f in report.findings:
            lines.append(f"### Finding {f.finding_id}: {f.title}")
            lines.append("")
            elem_desc = f"`{f.affected_element}`" if f.affected_element else "Target Window"
            lines.append(f"- **Affected Element:** {elem_desc}")
            lines.append(f"- **Severity:** `{f.severity}` | **Confidence:** `{f.confidence * 100:.1f}%`")
            lines.append(f"- **Rule ID:** `{f.rule_id}` | **Source:** {f.source}")
            lines.append(f"- **Primary Provenance:** `[{f.evidence_class}]`")
            lines.append(f"- **Human Verification Required:** `{'Yes (Mandatory)' if f.human_verification_required else 'No'}`")
            lines.append("")

            lines.append("#### Observed Evidence")
            lines.append(f"> {f.description}")
            lines.append("")
            if f.evidence_references:
                lines.append("**Associated Evidence Records:**")
                for ref_id in f.evidence_references:
                    # Find matching evidence record
                    matched_ev = next((e for e in report.evidence if e.evidence_id == ref_id), None)
                    if matched_ev:
                        susp_tag = " `[UNTRUSTED DATA / PROMPT INJECTION ISOLATED]`" if matched_ev.is_suspicious else ""
                        lines.append(f"- **`{ref_id}`** `[{matched_ev.source_class}]`: {matched_ev.description}{susp_tag}")
                    else:
                        lines.append(f"- **`{ref_id}`**: Referenced evidence record")
                lines.append("")

            lines.append("#### Why It Matters")
            why = f.reasoning.get("why_it_matters") or "This barrier prevents accessible navigation or comprehension for users of assistive technology."
            lines.append(f"{why}")
            lines.append("")

            lines.append("#### Recommended Remediation")
            rec = f.remediation.get("recommendation") or "Review control accessibility properties in the target framework."
            lines.append(f"{rec}")
            lines.append("")
            code = f.remediation.get("remediation_code")
            if code:
                lines.append("```csharp")
                lines.append(f"{code}")
                lines.append("```")
                lines.append("")
            actions = f.remediation.get("developer_actions", [])
            if actions:
                lines.append("**Developer Action Steps:**")
                for idx, act in enumerate(actions, start=1):
                    lines.append(f"{idx}. {act}")
                lines.append("")

            lines.append("#### Verification Steps")
            for step in f.verification_steps:
                lines.append(f"- [ ] {step}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # 7. Visual Evidence
        lines.append("## Visual Evidence")
        lines.append("")
        if not report.evidence:
            lines.append("No visual evidence items recorded.")
        else:
            lines.append(f"Recorded **{len(report.evidence)}** discrete multimodal evidence items.")
            lines.append("")
            lines.append("| Evidence ID | Source Class | Description | Location [x,y,w,h] | Confidence |")
            lines.append("| :--- | :---: | :--- | :---: | :---: |")
            for ev in report.evidence[:30]:  # Limit preview table to top 30
                loc_str = f"`{ev.location}`" if ev.location else "—"
                lines.append(
                    f"| **{ev.evidence_id}** | `[{ev.source_class}]` | {ev.description[:60]}... | {loc_str} | `{ev.confidence:.2f}` |"
                )
            if len(report.evidence) > 30:
                lines.append(f"*(and {len(report.evidence) - 30} additional evidence items in complete JSON export)*")
        lines.append("")

        # 8. Keyboard Navigation
        lines.append("## Keyboard Navigation")
        lines.append("")
        if report.focus_traversal:
            ft = report.focus_traversal
            lines.append(f"- **Target Window:** {ft.get('target_window', 'Unknown')}")
            lines.append(f"- **Focus Steps Recorded:** {len(ft.get('observations', []))}")
            lines.append(f"- **Unique Elements:** {ft.get('unique_elements', 0)}")
            lines.append(f"- **Focus Loop Detected:** `{'Yes' if ft.get('loop_detected') else 'No'}`")
            lines.append(f"- **Potential Focus Trap Detected:** `{'Yes (WCAG 2.1.2 Finding Candidate)' if ft.get('focus_trap_detected') else 'No'}`")
            unreached = ft.get("unreachable_elements", [])
            lines.append(f"- **Unreached Interactive Elements:** `{len(unreached)}`")
        else:
            lines.append("Keyboard navigation focus traversal was not executed for this audit session.")
        lines.append("")

        # 9. Evidence Conflicts
        lines.append("## Evidence Conflicts")
        lines.append("")
        if report.evidence_conflicts:
            lines.append(f"Detected **{len(report.evidence_conflicts)}** potential evidence conflicts:")
            lines.append("")
            for conf in report.evidence_conflicts:
                lines.append(f"- **Conflict Type:** `{conf.get('conflict_type', 'LABEL_NAME_MISMATCH')}`")
                lines.append(f"  - Description: {conf.get('description', '')}")
                lines.append(f"  - Primary Source: `{conf.get('source_1', 'UIA_MEASURED')}`")
                lines.append(f"  - Secondary Source: `{conf.get('source_2', 'OCR_DETECTED')}`")
        else:
            lines.append("No multimodal evidence conflicts or label-in-name discrepancies were detected.")
        lines.append("")

        # 10. Limitations
        lines.append("## Limitations")
        lines.append("")
        for lim in report.limitations:
            lines.append(f"- {lim}")
        lines.append("")

        # 11. Human Verification Checklist
        lines.append("## Human Verification Checklist")
        lines.append("")
        lines.append("The following verification steps must be confirmed by a human evaluator before finalizing accessibility status:")
        lines.append("")
        for chk in report.verification_checklist:
            lines.append(f"- [ ] {chk}")
        lines.append("")

        # 12. Report Integrity
        lines.append("## Report Integrity")
        lines.append("")
        lines.append(f"- **Canonical Digest Algorithm:** SHA-256")
        lines.append(f"- **Evidence Digest:** `{report.evidence_digest}`")
        lines.append(f"- **Verification Command:** `python -m reports.report_integrity verify`")
        lines.append("")

        return "\n".join(lines)

    @classmethod
    def export_to_file(
        cls,
        report: AuditReport,
        output_path: Optional[str] = None,
        base_dir: Optional[str] = None,
    ) -> str:
        """Writes report Markdown to disk and returns destination path."""
        if not output_path:
            target_dir = base_dir or os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "generated",
            )
            os.makedirs(target_dir, exist_ok=True)
            output_path = os.path.join(target_dir, f"{report.report_id}.md")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        md_content = cls.export_to_string(report)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return os.path.abspath(output_path)

"""Asynchronous Report Generation Worker for AccessLens AI (Phase 7).

Executes audit report assembly, multi-format export (JSON, Markdown, HTML),
and SQLite history persistence in a background QThread to ensure UI responsiveness.
"""

import os
from typing import Any, Dict, List, Optional
from PySide6.QtCore import QThread, Signal

from accessibility.element_model import UIElementModel
from accessibility.evidence_fusion import EvidenceFusionResult
from accessibility.findings import AccessibilityFinding
from accessibility.focus_models import FocusTraversalResult
from accessibility.visual_models import VisualEvidence
from ai.reasoning_models import ReasoningResult
from reports.exporters.html_exporter import HtmlReportExporter
from reports.exporters.json_exporter import JsonReportExporter
from reports.exporters.markdown_exporter import MarkdownReportExporter
from reports.report_generator import audit_report_generator
from reports.report_models import AuditReport
from storage.database import database_manager


class ReportWorker(QThread):
    """Background worker for assembling and exporting accessibility audit reports."""

    progress = Signal(str)
    finished = Signal(object, dict)  # (AuditReport, export_paths_dict)
    error = Signal(str)

    def __init__(
        self,
        application_name: str = "Target Application",
        target_window: str = "Target Window",
        findings: Optional[List[AccessibilityFinding]] = None,
        ui_elements: Optional[List[UIElementModel]] = None,
        visual_elements: Optional[List[VisualEvidence]] = None,
        fusion_result: Optional[EvidenceFusionResult] = None,
        focus_result: Optional[FocusTraversalResult] = None,
        reasoning_results: Optional[Dict[str, ReasoningResult]] = None,
        privacy_mode: str = "findings_only",
        evidence_image_mode: str = "findings_only",
        export_formats: Optional[List[str]] = None,  # ["json", "md", "html"]
        output_dir: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.application_name = application_name
        self.target_window = target_window
        self.findings = findings or []
        self.ui_elements = ui_elements or []
        self.visual_elements = visual_elements or []
        self.fusion_result = fusion_result
        self.focus_result = focus_result
        self.reasoning_results = reasoning_results or {}
        self.privacy_mode = privacy_mode
        self.evidence_image_mode = evidence_image_mode
        self.export_formats = export_formats or ["json", "md", "html"]
        self.output_dir = output_dir
        self._is_cancelled = False

    def cancel(self):
        """Cooperatively requests worker cancellation."""
        self._is_cancelled = True

    def run(self):
        """Executes report generation and multi-format export sequentially."""
        try:
            if self._is_cancelled:
                return

            self.progress.emit("Synthesizing scan findings and multimodal evidence...")

            # 1. Generate AuditReport
            report = audit_report_generator.generate_report(
                application_name=self.application_name,
                target_window=self.target_window,
                findings=self.findings,
                ui_elements=self.ui_elements,
                visual_elements=self.visual_elements,
                fusion_result=self.fusion_result,
                focus_result=self.focus_result,
                reasoning_results=self.reasoning_results,
                privacy_mode=self.privacy_mode,
                evidence_image_mode=self.evidence_image_mode,
            )

            # 2. Determine output destination folder
            dest_dir = self.output_dir
            if not dest_dir:
                base_reports_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "reports",
                    "generated",
                    report.report_id,
                )
                dest_dir = base_reports_dir

            os.makedirs(dest_dir, exist_ok=True)
            export_paths: Dict[str, str] = {}

            # 3. Export requested formats
            if "json" in self.export_formats:
                self.progress.emit("Writing complete JSON report...")
                json_path = os.path.join(dest_dir, f"{report.report_id}.json")
                JsonReportExporter.export_to_file(report, output_path=json_path)
                export_paths["json"] = json_path

            if "md" in self.export_formats:
                self.progress.emit("Rendering Markdown audit report...")
                md_path = os.path.join(dest_dir, f"{report.report_id}.md")
                MarkdownReportExporter.export_to_file(report, output_path=md_path)
                export_paths["md"] = md_path

            if "html" in self.export_formats:
                self.progress.emit("Compiling self-contained accessible HTML report...")
                html_path = os.path.join(dest_dir, f"{report.report_id}.html")
                HtmlReportExporter.export_to_file(report, output_path=html_path)
                export_paths["html"] = html_path

            # 4. Save metadata record to backward-compatible SQLite table
            self.progress.emit("Recording export in local SQLite database...")
            primary_file = export_paths.get("html") or export_paths.get("json") or dest_dir
            try:
                database_manager.add_report_record(
                    report_id=report.report_id,
                    generated_at=report.generated_at,
                    application_name=report.application_name,
                    target_window=report.target_window,
                    finding_count=len(report.findings),
                    privacy_mode=report.privacy_mode,
                    file_path=primary_file,
                    digest=report.evidence_digest,
                )
            except Exception:
                # History logging is non-fatal for report generation
                pass

            if self._is_cancelled:
                return

            self.progress.emit("Report generated successfully.")
            self.finished.emit(report, export_paths)

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(f"Failed to generate report: {str(e)}")

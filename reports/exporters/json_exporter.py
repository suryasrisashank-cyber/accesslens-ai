"""JSON Report Exporter for AccessLens AI (Phase 7).

Serializes complete, validated AuditReport data into a structured, machine-readable
JSON file preserving all evidence, findings, provenance classes, and SHA-256 digest.
"""

import json
import os
from typing import Optional

from reports.report_models import AuditReport


class JsonReportExporter:
    """Exports an AuditReport to formatted JSON on disk or string."""

    @staticmethod
    def export_to_string(report: AuditReport, indent: int = 2) -> str:
        """Serializes report to a formatted JSON string."""
        return json.dumps(report.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def export_to_file(
        cls,
        report: AuditReport,
        output_path: Optional[str] = None,
        base_dir: Optional[str] = None,
        indent: int = 2,
    ) -> str:
        """Writes report JSON to disk and returns destination path."""
        if not output_path:
            target_dir = base_dir or os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "generated",
            )
            os.makedirs(target_dir, exist_ok=True)
            output_path = os.path.join(target_dir, f"{report.report_id}.json")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        json_content = cls.export_to_string(report, indent=indent)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_content)

        return os.path.abspath(output_path)

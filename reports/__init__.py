"""AccessLens AI Reporting and Evidence Export Package (Phase 7).

Provides auditable, reproducible, evidence-backed accessibility audit reports
across JSON, Markdown, and self-contained offline HTML formats.
"""

from reports.report_models import (
    AuditReport,
    EvidenceReportItem,
    FindingReportModel,
    ReportSummary,
    VALID_PROVENANCE_CLASSES,
)
from reports.report_generator import AuditReportGenerator, audit_report_generator
from reports.report_validator import ReportValidator, validate_report_schema, validate_or_raise
from reports.report_integrity import (
    calculate_report_digest,
    verify_report_digest,
)

__all__ = [
    "AuditReport",
    "EvidenceReportItem",
    "FindingReportModel",
    "ReportSummary",
    "VALID_PROVENANCE_CLASSES",
    "AuditReportGenerator",
    "audit_report_generator",
    "ReportValidator",
    "validate_report_schema",
    "validate_or_raise",
    "calculate_report_digest",
    "verify_report_digest",
]

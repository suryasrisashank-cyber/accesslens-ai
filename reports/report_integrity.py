"""Report Integrity and SHA-256 Reproducibility Engine for AccessLens AI (Phase 7).

Provides deterministic canonical serialization and SHA-256 evidence digest calculation
to ensure exported accessibility audit reports are verifiable and tamper-evident.
"""

import hashlib
import json
from typing import Any, Dict, Union

from reports.report_models import AuditReport


def _normalize_report_for_hashing(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts a canonical dictionary stripped of volatile or self-referential digest fields."""
    normalized = dict(data)
    # Exclude self-referential digest field
    normalized.pop("evidence_digest", None)
    return normalized


def calculate_report_digest(report: Union[AuditReport, Dict[str, Any]]) -> str:
    """Calculates a deterministic SHA-256 evidence digest from an AuditReport or report dictionary."""
    if isinstance(report, AuditReport):
        raw_dict = report.to_dict()
    elif isinstance(report, dict):
        raw_dict = dict(report)
    else:
        raise TypeError("Report must be an AuditReport instance or dictionary.")

    clean_dict = _normalize_report_for_hashing(raw_dict)

    # Canonical deterministic JSON string: sorted keys, compact separators, UTF-8 encoded
    canonical_json = json.dumps(
        clean_dict,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return digest


def verify_report_digest(
    report: Union[AuditReport, Dict[str, Any]],
    expected_digest: Optional[str] = None
) -> bool:
    """Verifies that the report's computed SHA-256 digest matches the embedded or expected digest."""
    if isinstance(report, AuditReport):
        raw_dict = report.to_dict()
        digest_to_check = expected_digest or report.evidence_digest
    elif isinstance(report, dict):
        raw_dict = dict(report)
        digest_to_check = expected_digest or raw_dict.get("evidence_digest")
    else:
        return False

    if not digest_to_check:
        return False

    calculated = calculate_report_digest(raw_dict)
    return calculated == digest_to_check

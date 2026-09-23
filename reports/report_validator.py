"""Audit Report Validator for AccessLens AI (Phase 7).

Validates complete schema conformance, evidence ID reference integrity,
provenance class validity, and mandatory human verification indicators.
"""

from typing import Any, Dict, List, Set, Tuple, Union

from reports.report_models import AuditReport, VALID_PROVENANCE_CLASSES


class ReportValidationError(ValueError):
    """Raised when an accessibility report fails schema or integrity validation."""
    pass


class ReportValidator:
    """Enforces strict structural and referential integrity on accessibility reports."""

    REQUIRED_ROOT_FIELDS: List[str] = [
        "report_id",
        "schema_version",
        "generated_at",
        "summary",
        "findings",
        "evidence",
        "hardware_attestation",
        "privacy_information",
        "limitations",
    ]

    REQUIRED_FINDING_FIELDS: List[str] = [
        "finding_id",
        "rule_id",
        "title",
        "severity",
        "confidence",
        "human_verification_required",
    ]

    @classmethod
    def validate(cls, report: Union[AuditReport, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Performs comprehensive validation of an AuditReport or report dictionary.
        
        Returns:
            (is_valid, error_list)
        """
        errors: List[str] = []

        if isinstance(report, AuditReport):
            data = report.to_dict()
        elif isinstance(report, dict):
            data = report
        else:
            return False, ["Report must be an AuditReport instance or dictionary."]

        # 1. Check required root fields
        for field in cls.REQUIRED_ROOT_FIELDS:
            if field not in data or data[field] is None:
                errors.append(f"Missing required root field: '{field}'")
            elif isinstance(data[field], str) and not data[field].strip():
                errors.append(f"Required root field '{field}' is empty.")

        # 2. Check evidence list and build evidence ID index
        evidence_list = data.get("evidence", [])
        if not isinstance(evidence_list, list):
            errors.append("'evidence' must be a list.")
            evidence_list = []

        evidence_ids: Set[str] = set()
        for idx, ev in enumerate(evidence_list):
            if not isinstance(ev, dict):
                errors.append(f"Evidence item at index {idx} is not a dictionary.")
                continue

            eid = ev.get("evidence_id")
            if not eid or not str(eid).strip():
                errors.append(f"Evidence item at index {idx} has missing or empty 'evidence_id'.")
            else:
                evidence_ids.add(str(eid))

            # Validate provenance class
            s_class = ev.get("source_class")
            if not s_class or s_class not in VALID_PROVENANCE_CLASSES:
                errors.append(
                    f"Evidence '{eid or idx}' has invalid source_class '{s_class}'. "
                    f"Must be one of: {sorted(list(VALID_PROVENANCE_CLASSES))}."
                )

        # 3. Check findings list and evidence reference integrity
        findings_list = data.get("findings", [])
        if not isinstance(findings_list, list):
            errors.append("'findings' must be a list.")
            findings_list = []

        for idx, f in enumerate(findings_list):
            if not isinstance(f, dict):
                errors.append(f"Finding at index {idx} is not a dictionary.")
                continue

            fid = f.get("finding_id", f"idx_{idx}")

            # Required finding fields
            for rff in cls.REQUIRED_FINDING_FIELDS:
                if rff not in f or f[rff] is None:
                    errors.append(f"Finding '{fid}' missing required field: '{rff}'.")

            # Validate finding's primary evidence class
            ev_class = f.get("evidence_class")
            if ev_class and ev_class not in VALID_PROVENANCE_CLASSES:
                errors.append(
                    f"Finding '{fid}' has invalid evidence_class '{ev_class}'. "
                    f"Must be one of: {sorted(list(VALID_PROVENANCE_CLASSES))}."
                )

            # Validate evidence references (every reference must exist in evidence_ids)
            refs = f.get("evidence_references", [])
            if isinstance(refs, list):
                for ref_id in refs:
                    if str(ref_id) not in evidence_ids:
                        errors.append(
                            f"Finding '{fid}' references non-existent evidence_id '{ref_id}'."
                        )
            else:
                errors.append(f"Finding '{fid}' 'evidence_references' must be a list.")

        # 4. Check hardware attestation completeness
        hw = data.get("hardware_attestation", {})
        if isinstance(hw, dict):
            if "host_processor" not in hw and "cpu_model" not in hw:
                errors.append("hardware_attestation missing host processor information.")
        else:
            errors.append("'hardware_attestation' must be a dictionary.")

        # 5. Check privacy information completeness
        priv = data.get("privacy_information", {})
        if isinstance(priv, dict):
            if "processing_mode" not in priv:
                errors.append("privacy_information missing 'processing_mode'.")
        else:
            errors.append("'privacy_information' must be a dictionary.")

        return len(errors) == 0, errors

    @classmethod
    def validate_or_raise(cls, report: Union[AuditReport, Dict[str, Any]]):
        """Validates report and raises ReportValidationError if any errors occur."""
        is_valid, errors = cls.validate(report)
        if not is_valid:
            err_msg = "\n  - ".join(errors)
            raise ReportValidationError(f"Report validation failed with {len(errors)} error(s):\n  - {err_msg}")


# Functional convenience aliases
validate_report_schema = ReportValidator.validate
validate_or_raise = ReportValidator.validate_or_raise

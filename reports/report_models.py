"""Structured Data Models for Accessibility Reports and Evidence Export (Phase 7).

Defines normalized models for audit reports, findings, summary metrics,
traceable evidence records, and provenance attestation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Set


VALID_PROVENANCE_CLASSES: Set[str] = {
    "UIA_MEASURED",
    "SCREENSHOT_MEASURED",
    "OCR_DETECTED",
    "KEYBOARD_MEASURED",
    "FUSED",
    "INFERRED",
    "RECOMMENDED",
}


@dataclass
class ReportSummary:
    """Aggregated numerical and status metrics for an accessibility audit report."""
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    total_ui_elements: int = 0
    total_visual_elements: int = 0
    matched_elements: int = 0
    unmatched_uia: int = 0
    unmatched_visual: int = 0
    evidence_conflicts: int = 0

    keyboard_audit_available: bool = False
    focus_elements_observed: int = 0
    human_verification_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes summary to a dictionary."""
        return {
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "total_ui_elements": self.total_ui_elements,
            "total_visual_elements": self.total_visual_elements,
            "matched_elements": self.matched_elements,
            "unmatched_uia": self.unmatched_uia,
            "unmatched_visual": self.unmatched_visual,
            "evidence_conflicts": self.evidence_conflicts,
            "keyboard_audit_available": self.keyboard_audit_available,
            "focus_elements_observed": self.focus_elements_observed,
            "human_verification_required": self.human_verification_required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReportSummary":
        """Instantiates ReportSummary from a dictionary."""
        return cls(
            total_findings=data.get("total_findings", 0),
            critical_count=data.get("critical_count", 0),
            high_count=data.get("high_count", 0),
            medium_count=data.get("medium_count", 0),
            low_count=data.get("low_count", 0),
            total_ui_elements=data.get("total_ui_elements", 0),
            total_visual_elements=data.get("total_visual_elements", 0),
            matched_elements=data.get("matched_elements", 0),
            unmatched_uia=data.get("unmatched_uia", 0),
            unmatched_visual=data.get("unmatched_visual", 0),
            evidence_conflicts=data.get("evidence_conflicts", 0),
            keyboard_audit_available=data.get("keyboard_audit_available", False),
            focus_elements_observed=data.get("focus_elements_observed", 0),
            human_verification_required=data.get("human_verification_required", True),
        )


@dataclass
class EvidenceReportItem:
    """Discrete, traceable evidence record supporting an accessibility finding."""
    evidence_id: str
    source_class: str  # Must be one of VALID_PROVENANCE_CLASSES
    description: str
    value: Any = None
    confidence: float = 1.0
    element_id: Optional[str] = None
    location: Optional[List[int]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_suspicious: bool = False
    human_verification_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes evidence record to dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "source_class": self.source_class,
            "description": self.description,
            "value": self.value,
            "confidence": round(float(self.confidence), 3),
            "element_id": self.element_id,
            "location": list(self.location) if self.location else None,
            "timestamp": self.timestamp,
            "is_suspicious": self.is_suspicious,
            "human_verification_required": self.human_verification_required,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceReportItem":
        """Instantiates EvidenceReportItem from a dictionary."""
        return cls(
            evidence_id=str(data.get("evidence_id", "")),
            source_class=str(data.get("source_class", "INFERRED")),
            description=str(data.get("description", "")),
            value=data.get("value"),
            confidence=float(data.get("confidence", 1.0)),
            element_id=data.get("element_id"),
            location=data.get("location"),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            is_suspicious=bool(data.get("is_suspicious", False)),
            human_verification_required=bool(data.get("human_verification_required", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class FindingReportModel:
    """Evidence-grounded accessibility finding formatted for formal report export."""
    finding_id: str  # Stable ID (e.g. "F-001")
    rule_id: str
    title: str
    description: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    confidence: float
    evidence_class: str  # Primary provenance class
    evidence_references: List[str] = field(default_factory=list)  # Stable evidence IDs (e.g. ["E-001", "E-002"])
    affected_element: Optional[str] = None
    affected_bounds: Optional[List[int]] = None
    source: str = "Windows UI Automation"
    reasoning: Dict[str, Any] = field(default_factory=dict)
    remediation: Dict[str, Any] = field(default_factory=dict)
    verification_steps: List[str] = field(default_factory=list)
    human_verification_required: bool = True
    limitations: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serializes finding report model to dictionary."""
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "confidence": round(float(self.confidence), 3),
            "evidence_class": self.evidence_class,
            "evidence_references": list(self.evidence_references),
            "affected_element": self.affected_element,
            "affected_bounds": list(self.affected_bounds) if self.affected_bounds else None,
            "source": self.source,
            "reasoning": dict(self.reasoning),
            "remediation": dict(self.remediation),
            "verification_steps": list(self.verification_steps),
            "human_verification_required": self.human_verification_required,
            "limitations": self.limitations,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FindingReportModel":
        """Instantiates FindingReportModel from a dictionary."""
        return cls(
            finding_id=str(data.get("finding_id", "")),
            rule_id=str(data.get("rule_id", "RULE_UNKNOWN")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            severity=str(data.get("severity", "MEDIUM")),
            confidence=float(data.get("confidence", 0.8)),
            evidence_class=str(data.get("evidence_class", "INFERRED")),
            evidence_references=list(data.get("evidence_references", [])),
            affected_element=data.get("affected_element"),
            affected_bounds=data.get("affected_bounds"),
            source=str(data.get("source", "")),
            reasoning=dict(data.get("reasoning", {})),
            remediation=dict(data.get("remediation", {})),
            verification_steps=list(data.get("verification_steps", [])),
            human_verification_required=bool(data.get("human_verification_required", True)),
            limitations=str(data.get("limitations", "")),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
        )


@dataclass
class AuditReport:
    """Complete, reproducible, evidence-backed accessibility audit report."""
    report_id: str
    schema_version: str = "1.0.0"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    application_name: str = "Target Application"
    target_window: str = "Target Window"
    application_version: str = "1.0.0"
    scan_duration_ms: float = 0.0

    host_information: Dict[str, Any] = field(default_factory=dict)
    hardware_attestation: Dict[str, Any] = field(default_factory=dict)
    privacy_information: Dict[str, Any] = field(default_factory=dict)

    privacy_mode: str = "findings_only"  # "findings_only", "redacted", "local_full"
    evidence_image_mode: str = "findings_only"  # "none", "findings_only", "all_evidence"

    summary: ReportSummary = field(default_factory=ReportSummary)
    findings: List[FindingReportModel] = field(default_factory=list)
    evidence: List[EvidenceReportItem] = field(default_factory=list)

    focus_traversal: Optional[Dict[str, Any]] = None
    visual_evidence: Optional[List[Dict[str, Any]]] = None
    evidence_conflicts: Optional[List[Dict[str, Any]]] = None
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    verification_checklist: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    evidence_digest: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes complete audit report to standard dictionary."""
        return {
            "report_id": self.report_id,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "application_name": self.application_name,
            "target_window": self.target_window,
            "application_version": self.application_version,
            "scan_duration_ms": round(float(self.scan_duration_ms), 2),
            "host_information": dict(self.host_information),
            "hardware_attestation": dict(self.hardware_attestation),
            "privacy_information": dict(self.privacy_information),
            "privacy_mode": self.privacy_mode,
            "evidence_image_mode": self.evidence_image_mode,
            "summary": self.summary.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "evidence": [e.to_dict() for e in self.evidence],
            "focus_traversal": dict(self.focus_traversal) if self.focus_traversal else None,
            "visual_evidence": list(self.visual_evidence) if self.visual_evidence else None,
            "evidence_conflicts": list(self.evidence_conflicts) if self.evidence_conflicts else None,
            "recommendations": list(self.recommendations),
            "verification_checklist": list(self.verification_checklist),
            "limitations": list(self.limitations),
            "evidence_digest": self.evidence_digest,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditReport":
        """Deserializes AuditReport from dictionary."""
        raw_summary = data.get("summary", {})
        summary = ReportSummary.from_dict(raw_summary) if isinstance(raw_summary, dict) else ReportSummary()

        findings = [
            FindingReportModel.from_dict(f)
            for f in data.get("findings", [])
            if isinstance(f, dict)
        ]

        evidence = [
            EvidenceReportItem.from_dict(e)
            for e in data.get("evidence", [])
            if isinstance(e, dict)
        ]

        return cls(
            report_id=str(data.get("report_id", "")),
            schema_version=str(data.get("schema_version", "1.0.0")),
            generated_at=str(data.get("generated_at", datetime.now(timezone.utc).isoformat())),
            application_name=str(data.get("application_name", "Target Application")),
            target_window=str(data.get("target_window", "Target Window")),
            application_version=str(data.get("application_version", "1.0.0")),
            scan_duration_ms=float(data.get("scan_duration_ms", 0.0)),
            host_information=dict(data.get("host_information", {})),
            hardware_attestation=dict(data.get("hardware_attestation", {})),
            privacy_information=dict(data.get("privacy_information", {})),
            privacy_mode=str(data.get("privacy_mode", "findings_only")),
            evidence_image_mode=str(data.get("evidence_image_mode", "findings_only")),
            summary=summary,
            findings=findings,
            evidence=evidence,
            focus_traversal=data.get("focus_traversal"),
            visual_evidence=data.get("visual_evidence"),
            evidence_conflicts=data.get("evidence_conflicts"),
            recommendations=list(data.get("recommendations", [])),
            verification_checklist=list(data.get("verification_checklist", [])),
            limitations=list(data.get("limitations", [])),
            evidence_digest=str(data.get("evidence_digest", "")),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serializes report to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "AuditReport":
        """Deserializes report from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

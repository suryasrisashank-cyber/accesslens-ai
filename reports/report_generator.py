"""Audit Report Generator for AccessLens AI (Phase 7).

Orchestrates the synthesis of Windows UI Automation data, on-device OCR,
multimodal evidence fusion, keyboard traversal logs, local reasoning, and
remediation advice into a complete, validated, reproducible AuditReport.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from accessibility.element_model import UIElementModel
from accessibility.evidence_engine import EvidenceItem
from accessibility.evidence_fusion import EvidenceFusionResult
from accessibility.findings import AccessibilityFinding, FindingSeverity
from accessibility.focus_models import FocusTraversalResult
from accessibility.visual_models import VisualEvidence
from ai.prompt_guard import PromptGuard
from ai.reasoning_models import ReasoningResult
from hardware.hardware_detector import HardwareDetector
from privacy.privacy_manager import privacy_manager
from reports.report_integrity import calculate_report_digest
from reports.report_models import (
    AuditReport,
    EvidenceReportItem,
    FindingReportModel,
    ReportSummary,
    VALID_PROVENANCE_CLASSES,
)
from reports.report_validator import ReportValidator
from reports.sensitive_data_detector import sensitive_data_detector


class AuditReportGenerator:
    """Generates structured, validated, evidence-backed accessibility audit reports."""

    DEFAULT_LIMITATIONS: List[str] = [
        "Automated accessibility findings are evidence for review, not formal accessibility certification.",
        "Complete WCAG 2.1 compliance requires complementary manual verification with assistive technology.",
        "Visual OCR and color contrast calculations reflect captured pixels at inspection time and may vary with dynamic theme changes.",
        "Testing was conducted locally on-device without cloud APIs or external telemetry.",
    ]

    DEFAULT_CHECKLIST: List[str] = [
        "Verify affected control manually in the target application",
        "Confirm accessible name matches visual context and user intent",
        "Confirm keyboard reachability via Tab and Shift+Tab traversal",
        "Confirm visual focus indicator meets visibility and contrast requirements",
        "Confirm contrast manually where automated pixel measurement is uncertain",
        "Verify remediation in target framework accessibility tree (Inspect.exe / Narrator)",
        "Re-run AccessLens audit to confirm barrier removal",
    ]

    def __init__(self, hardware_detector: Optional[HardwareDetector] = None):
        self._hardware_detector = hardware_detector or HardwareDetector()

    def generate_report(
        self,
        application_name: str = "Target Application",
        target_window: str = "Target Window",
        findings: Optional[List[AccessibilityFinding]] = None,
        ui_elements: Optional[List[UIElementModel]] = None,
        visual_elements: Optional[List[VisualEvidence]] = None,
        fusion_result: Optional[EvidenceFusionResult] = None,
        focus_result: Optional[FocusTraversalResult] = None,
        reasoning_results: Optional[Dict[str, ReasoningResult]] = None,
        privacy_mode: str = "findings_only",  # "findings_only", "redacted", "local_full"
        evidence_image_mode: str = "findings_only",  # "none", "findings_only", "all_evidence"
        scan_duration_ms: float = 0.0,
        custom_report_id: Optional[str] = None,
    ) -> AuditReport:
        """Constructs, validates, and hashes a comprehensive AuditReport."""
        now_dt = datetime.now(timezone.utc)
        generated_at = now_dt.isoformat()
        report_id = custom_report_id or f"accesslens-report-{now_dt.strftime('%Y%m%d-%H%M%S')}"

        findings_list = findings or []
        ui_elements_list = ui_elements or []
        visual_elements_list = visual_elements or []
        reasoning_map = reasoning_results or {}

        # 1. Collect Hardware Information & Attestation
        hw_profile = self._hardware_detector.inspect()
        host_info = {
            "os_name": hw_profile.os_name,
            "os_version": hw_profile.os_version,
            "architecture": hw_profile.architecture,
            "cpu_model": hw_profile.cpu_model,
            "ram_gb": hw_profile.ram_gb,
            "gpu_info": hw_profile.gpu_info,
        }

        hw_attestation = {
            "host_processor": hw_profile.cpu_model,
            "architecture": hw_profile.architecture,
            "snapdragon_detected": "DETECTED" if hw_profile.is_snapdragon else "NOT DETECTED",
            "npu_status": "AVAILABLE" if hw_profile.is_npu_available else "NOT AVAILABLE",
            "active_ai_backend": "CPUExecutionProvider (Local CPU Fallback)",
            "snapdragon_validation": (
                "Verified on Snapdragon hardware" if hw_profile.is_snapdragon and hw_profile.is_npu_available
                else "Pending genuine Snapdragon hardware"
            ),
            "integrity_attestation": "No simulated QNN execution or fabricated Snapdragon benchmarks.",
        }

        # 2. Collect Privacy Information
        privacy_info = {
            "processing_mode": "Local / Offline",
            "cloud_api_required": False,
            "external_network_required": False,
            "telemetry_implemented": False,
            "api_keys_required": False,
            "privacy_mode": privacy_mode,
            "privacy_statement": privacy_manager.privacy_statement,
        }

        # 3. Build Global Traceable Evidence Catalog
        evidence_catalog: List[EvidenceReportItem] = []
        evidence_key_to_id: Dict[str, str] = {}
        ev_counter = 1

        def _get_or_create_evidence_item(
            source_class: str,
            desc: str,
            value: Any = None,
            conf: float = 1.0,
            eid: Optional[str] = None,
            loc: Optional[List[int]] = None,
            is_susp: bool = False,
            meta: Optional[Dict[str, Any]] = None,
        ) -> str:
            nonlocal ev_counter
            # Sanitize source class
            s_class = source_class.upper().strip()
            if s_class not in VALID_PROVENANCE_CLASSES:
                s_class = "INFERRED"

            # Check for prompt injection patterns
            if not is_susp and desc:
                is_susp = PromptGuard.is_suspicious_text(desc)
            if not is_susp and isinstance(value, str) and value:
                is_susp = PromptGuard.is_suspicious_text(value)

            # Apply privacy mode redaction to descriptions and string values
            clean_desc = desc
            clean_val = value
            if privacy_mode == "redacted":
                clean_desc = sensitive_data_detector.redact_text(clean_desc)
                if isinstance(clean_val, str):
                    clean_val = sensitive_data_detector.redact_text(clean_val)

            cache_key = f"{s_class}::{clean_desc}::{eid or ''}::{loc or ''}"
            if cache_key in evidence_key_to_id:
                return evidence_key_to_id[cache_key]

            stable_id = f"E-{ev_counter:03d}"
            ev_counter += 1

            item = EvidenceReportItem(
                evidence_id=stable_id,
                source_class=s_class,
                description=clean_desc,
                value=clean_val,
                confidence=conf,
                element_id=eid,
                location=loc,
                is_suspicious=is_susp,
                human_verification_required=True,
                metadata=meta or {},
            )
            evidence_catalog.append(item)
            evidence_key_to_id[cache_key] = stable_id
            return stable_id

        # Index evidence from Fusion Result if available
        fused_items = (
            getattr(fusion_result, "fused_evidence", None)
            or getattr(fusion_result, "fused_evidence_items", None)
        )
        if fused_items:
            for item in fused_items:
                _get_or_create_evidence_item(
                    source_class=self._map_source_to_class(item.source, item.type),
                    desc=item.description,
                    value=item.value,
                    conf=item.confidence,
                    eid=item.element_id,
                    loc=item.location,
                )

        # Index evidence from Visual Elements
        if privacy_mode != "findings_only":
            for vis in visual_elements_list:
                vis_text = vis.text
                if privacy_mode == "redacted":
                    vis_text = sensitive_data_detector.redact_text(vis_text)
                _get_or_create_evidence_item(
                    source_class="OCR_DETECTED",
                    desc=f"On-device OCR detected text: '{vis_text}'" if vis_text else "Visual bounding region without detected text",
                    value=vis_text,
                    conf=vis.confidence,
                    eid=vis.evidence_id,
                    loc=vis.bounds,
                    is_susp=vis.is_suspicious,
                    meta={"screenshot_ref": vis.screenshot_reference},
                )

        # 4. Construct Traceable Finding Models
        finding_models: List[FindingReportModel] = []
        finding_counter = 1

        for f in findings_list:
            fid = f"F-{finding_counter:03d}"
            finding_counter += 1

            # Map finding's evidence items into global catalog and collect references
            ref_ids: List[str] = []
            for ev in f.evidence:
                if isinstance(ev, EvidenceItem):
                    ref_id = _get_or_create_evidence_item(
                        source_class=self._map_source_to_class(ev.source, ev.type),
                        desc=ev.description,
                        value=ev.value,
                        conf=ev.confidence,
                        eid=ev.element_id,
                        loc=ev.location,
                    )
                    ref_ids.append(ref_id)
                elif isinstance(ev, dict):
                    ref_id = _get_or_create_evidence_item(
                        source_class=self._map_source_to_class(ev.get("source", "INFERRED"), ev.get("type", "INFERRED")),
                        desc=ev.get("description", str(ev)),
                        value=ev.get("value"),
                        conf=float(ev.get("confidence", 1.0)),
                        eid=ev.get("element_id"),
                        loc=ev.get("location"),
                    )
                    ref_ids.append(ref_id)
                else:
                    ref_id = _get_or_create_evidence_item(
                        source_class="INFERRED",
                        desc=str(ev),
                    )
                    ref_ids.append(ref_id)

            # If finding had no specific evidence attached, create a baseline observation item
            if not ref_ids:
                primary_class = self._map_signal_to_class(f.signal_type)
                ref_id = _get_or_create_evidence_item(
                    source_class=primary_class,
                    desc=f.observation or f.title,
                    eid=f.affected_element_id,
                    loc=f.element_bounds,
                )
                ref_ids.append(ref_id)

            # Retrieve associated local AI reasoning if available
            f_reasoning: Dict[str, Any] = {}
            f_remediation: Dict[str, Any] = {
                "recommendation": f.recommendation,
                "remediation_code": f.remediation_code,
                "developer_actions": [],
            }
            f_verif_steps: List[str] = [
                f"Inspect affected element '{f.element_name or f.affected_element_id}' in target interface",
                "Verify with keyboard focus / accessibility inspection tools",
                "Re-audit with AccessLens after code fix",
            ]

            original_fid = f.finding_id or f.id
            if original_fid in reasoning_map:
                rr = reasoning_map[original_fid]
                f_reasoning = {
                    "summary": rr.summary,
                    "why_it_matters": rr.why_it_matters,
                    "confidence_explanation": rr.confidence_explanation,
                    "limitations": rr.limitations,
                    "generated_by": rr.generated_by,
                }
                f_remediation["recommendation"] = rr.remediation or f.recommendation
                f_remediation["developer_actions"] = list(rr.developer_actions)
                if rr.verification_steps:
                    f_verif_steps = list(rr.verification_steps)

            # Sanitize text fields if redacted privacy mode is active
            f_title = f.title
            f_desc = f.observation or f.title
            if privacy_mode == "redacted":
                f_title = sensitive_data_detector.redact_text(f_title)
                f_desc = sensitive_data_detector.redact_text(f_desc)
                f_remediation = sensitive_data_detector.sanitize_dictionary(f_remediation)
                f_reasoning = sensitive_data_detector.sanitize_dictionary(f_reasoning)

            sev_val = f.severity.value if hasattr(f.severity, "value") else str(f.severity).upper()

            finding_model = FindingReportModel(
                finding_id=fid,
                rule_id=getattr(f, "rule_id", "RULE_UNKNOWN"),
                title=f_title,
                description=f_desc,
                severity=sev_val,
                confidence=round(f.confidence, 3),
                evidence_class=self._map_signal_to_class(f.signal_type),
                evidence_references=ref_ids,
                affected_element=f.element_name or f.affected_element_id,
                affected_bounds=f.element_bounds,
                source=f.source or "Windows UI Automation",
                reasoning=f_reasoning,
                remediation=f_remediation,
                verification_steps=f_verif_steps,
                human_verification_required=True,
                limitations=getattr(f, "limitations", ""),
                timestamp=f.created_at or generated_at,
            )
            finding_models.append(finding_model)

        # 5. Build Aggregated Summary
        summary = ReportSummary(
            total_findings=len(finding_models),
            critical_count=sum(1 for f in finding_models if f.severity in ("CRITICAL", "1")),
            high_count=sum(1 for f in finding_models if f.severity in ("HIGH", "2")),
            medium_count=sum(1 for f in finding_models if f.severity in ("MEDIUM", "3")),
            low_count=sum(1 for f in finding_models if f.severity in ("LOW", "INFO", "4", "5")),
            total_ui_elements=len(ui_elements_list),
            total_visual_elements=len(visual_elements_list),
            matched_elements=fusion_result.matched_count if fusion_result else 0,
            unmatched_uia=fusion_result.unmatched_uia_count if fusion_result else 0,
            unmatched_visual=fusion_result.unmatched_visual_count if fusion_result else 0,
            evidence_conflicts=fusion_result.conflicts_count if fusion_result else 0,
            keyboard_audit_available=focus_result is not None,
            focus_elements_observed=len(focus_result.observations) if focus_result else 0,
            human_verification_required=True,
        )

        # 6. Aggregate Recommendations
        recommendations: List[Dict[str, Any]] = []
        for fm in finding_models:
            if fm.remediation.get("recommendation"):
                recommendations.append({
                    "finding_id": fm.finding_id,
                    "title": fm.title,
                    "recommendation": fm.remediation.get("recommendation"),
                    "remediation_code": fm.remediation.get("remediation_code"),
                    "actions": fm.remediation.get("developer_actions", []),
                })

        # 7. Collect Focus & Visual Evidence Summaries
        focus_dict = focus_result.to_dict() if focus_result else None
        visual_dict_list = (
            [v.to_dict() for v in visual_elements_list]
            if privacy_mode != "findings_only" and visual_elements_list else None
        )
        conflicts_list = fusion_result.evidence_conflicts if fusion_result else None

        # Build initial report
        report = AuditReport(
            report_id=report_id,
            schema_version="1.0.0",
            generated_at=generated_at,
            application_name=application_name,
            target_window=target_window,
            application_version="1.0.0",
            scan_duration_ms=scan_duration_ms,
            host_information=host_info,
            hardware_attestation=hw_attestation,
            privacy_information=privacy_info,
            privacy_mode=privacy_mode,
            evidence_image_mode=evidence_image_mode,
            summary=summary,
            findings=finding_models,
            evidence=evidence_catalog,
            focus_traversal=focus_dict,
            visual_evidence=visual_dict_list,
            evidence_conflicts=conflicts_list,
            recommendations=recommendations,
            verification_checklist=list(self.DEFAULT_CHECKLIST),
            limitations=list(self.DEFAULT_LIMITATIONS),
        )

        # 8. Calculate SHA-256 Evidence Digest
        digest = calculate_report_digest(report)
        report.evidence_digest = digest

        # 9. Validate Complete Report
        ReportValidator.validate_or_raise(report)

        return report

    @staticmethod
    def _map_signal_to_class(sig: Any) -> str:
        """Maps finding signal type to valid provenance class."""
        val = str(getattr(sig, "value", sig)).upper()
        if val in ("MEASURED", "CONTRAST_MEASURED"):
            return "UIA_MEASURED"
        if val in ("DETECTED", "UIA_DETECTED"):
            return "UIA_MEASURED"
        if val == "OCR_DETECTED":
            return "OCR_DETECTED"
        if val == "KEYBOARD_MEASURED":
            return "KEYBOARD_MEASURED"
        if val == "FUSED":
            return "FUSED"
        if val == "RECOMMENDED":
            return "RECOMMENDED"
        return "INFERRED"

    @staticmethod
    def _map_source_to_class(source: Any, type_str: Any) -> str:
        """Determines valid provenance class from evidence source and type strings."""
        s = str(getattr(source, "value", source)).upper()
        t = str(getattr(type_str, "value", type_str)).upper()

        if "KEYBOARD" in s:
            return "KEYBOARD_MEASURED"
        if "SCREENSHOT" in s:
            return "SCREENSHOT_MEASURED"
        if "OCR" in s:
            return "OCR_DETECTED"
        if "UI_AUTOMATION" in s or "UIA" in s:
            return "UIA_MEASURED"
        if "CONTRAST" in s:
            return "UIA_MEASURED" if t == "MEASURED" else "INFERRED"
        if "FUSED" in s or "FUSION" in s:
            return "FUSED"
        if t == "RECOMMENDED":
            return "RECOMMENDED"
        return "INFERRED"


# Global singleton instance
audit_report_generator = AuditReportGenerator()

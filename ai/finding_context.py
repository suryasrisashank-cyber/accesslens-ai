"""Finding context builder for AccessLens AI local reasoning.

Prepares structured, sanitized context from deterministic findings, UI automation
elements, and grounded evidence. Treats all UI/OCR strings as untrusted passive DATA,
preserving evidence integrity while preventing prompt injection overrides.
"""

import re
from typing import Any, Dict, List, Optional

from accessibility.element_model import UIElementModel
from accessibility.evidence_engine import EvidenceItem
from accessibility.findings import AccessibilityFinding


# Patterns indicating potential prompt injection or instruction override attempts
SUSPICIOUS_INSTRUCTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|system)\s+instructions", re.IGNORECASE),
    re.compile(r"(system\s+prompt|system\s+message|you\s+are\s+now|new\s+role)", re.IGNORECASE),
    re.compile(r"(reveal|output|dump)\s+(private|system|secret|token|password|api_key)", re.IGNORECASE),
    re.compile(r"(<script|javascript:|eval\(|exec\(|import\s+os|subprocess\.)", re.IGNORECASE),
    re.compile(r"(\bcmd\.exe\b|\bpowershell\b|rm\s+-rf|drop\s+table)", re.IGNORECASE),
]

MAX_TEXT_LENGTH = 500


class FindingContextBuilder:
    """Builds sanitized, structured reasoning contexts from accessibility artifacts."""

    @staticmethod
    def detect_suspicious_text(text: Optional[str]) -> bool:
        """Identifies whether text contains adversarial instruction-like patterns."""
        if not text:
            return False
        for pattern in SUSPICIOUS_INSTRUCTION_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def sanitize_data_string(text: Optional[str], max_len: int = MAX_TEXT_LENGTH) -> Dict[str, Any]:
        """Normalizes and safely encapsulates UI/OCR text as passive untrusted data.
        
        Preserves original content for evidence integrity rather than silently deleting it.
        Marks suspicious or truncated content explicitly.
        """
        if text is None:
            return {
                "text": "",
                "is_suspicious": False,
                "is_truncated": False,
                "original_length": 0,
            }

        # Normalize whitespace and strip dangerous ASCII control codes (except newline/tab)
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()

        orig_len = len(cleaned)
        is_suspicious = FindingContextBuilder.detect_suspicious_text(cleaned)
        is_truncated = orig_len > max_len

        truncated_text = cleaned[:max_len] if is_truncated else cleaned

        return {
            "text": truncated_text,
            "is_suspicious": is_suspicious,
            "is_truncated": is_truncated,
            "original_length": orig_len,
        }

    def build_context(
        self,
        finding: AccessibilityFinding,
        element: Optional[UIElementModel] = None,
        evidence_items: Optional[List[EvidenceItem]] = None,
    ) -> Dict[str, Any]:
        """Builds a complete, structured context dictionary for the reasoning engine."""
        # 1. Sanitize Finding metadata
        title_meta = self.sanitize_data_string(finding.title)
        obs_meta = self.sanitize_data_string(finding.observation or finding.title)
        impact_meta = self.sanitize_data_string(finding.impact)
        rec_meta = self.sanitize_data_string(finding.recommendation)

        # 2. Extract and sanitize element properties
        element_data: Dict[str, Any] = {}
        detected_framework: Optional[str] = None
        if element is not None:
            name_meta = self.sanitize_data_string(element.name)
            ocr_meta = self.sanitize_data_string(getattr(element, "ocr_associated_text", ""))
            aid_meta = self.sanitize_data_string(element.automation_id)
            class_meta = self.sanitize_data_string(element.class_name)
            framework_id = getattr(element, "framework_id", "") or ""
            framework_meta = self.sanitize_data_string(framework_id)

            if framework_id and framework_id.lower() in ["wpf", "winui", "winforms", "chrome", "edge", "electron"]:
                detected_framework = framework_id

            element_data = {
                "element_id": element.element_id or element.id,
                "control_type": element.control_type or "Element",
                "name": name_meta["text"],
                "name_untrusted_metadata": name_meta,
                "ocr_associated_text": ocr_meta["text"],
                "ocr_untrusted_metadata": ocr_meta,
                "automation_id": aid_meta["text"],
                "class_name": class_meta["text"],
                "framework_id": framework_meta["text"],
                "bounds": list(element.bounds) if element.bounds else None,
                "is_keyboard_focusable": bool(getattr(element, "focusable", False) or getattr(element, "is_focusable", False)),
                "is_enabled": bool(getattr(element, "enabled", True) if getattr(element, "enabled", None) is not None else getattr(element, "is_enabled", True)),
                "has_keyboard_focus": bool(getattr(element, "focused", False) or getattr(element, "has_keyboard_focus", False)),
            }
        else:
            # Element is absent or unknown
            element_data = {
                "element_id": finding.affected_element_id or "unknown",
                "control_type": getattr(finding, "element_type", "") or "Element",
                "name": getattr(finding, "element_name", "") or "",
                "bounds": getattr(finding, "element_bounds", None),
                "is_keyboard_focusable": False,
                "is_enabled": True,
            }

        # 3. Process Evidence items with evidence ID preservation
        evidence_list = []
        evidence_ids = []
        raw_evidence = evidence_items if evidence_items is not None else finding.evidence

        for idx, ev in enumerate(raw_evidence):
            ev_id = getattr(ev, "evidence_id", None) or getattr(ev, "element_id", None) or f"ev_{idx+1}"
            evidence_ids.append(ev_id)
            ev_sig = getattr(ev, "signal_type", None) or getattr(ev, "type", None)
            sig_str = ev_sig.value if hasattr(ev_sig, "value") else str(ev_sig or "DETECTED")
            ev_src = getattr(ev, "source", None)
            src_str = ev_src.value if hasattr(ev_src, "value") else str(ev_src or finding.source)
            ev_desc = getattr(ev, "description", str(ev))
            desc_meta = self.sanitize_data_string(ev_desc)

            evidence_list.append({
                "evidence_id": ev_id,
                "signal_type": sig_str,
                "source": src_str,
                "description": desc_meta["text"],
                "untrusted_metadata": desc_meta,
                "confidence": getattr(ev, "confidence", finding.confidence),
            })

        # 4. Check for any suspicious content in finding or evidence
        any_suspicious = (
            title_meta["is_suspicious"]
            or obs_meta["is_suspicious"]
            or any(ev["untrusted_metadata"]["is_suspicious"] for ev in evidence_list)
            or (element_data.get("name_untrusted_metadata", {}).get("is_suspicious", False))
            or (element_data.get("ocr_untrusted_metadata", {}).get("is_suspicious", False))
        )

        sev_str = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        cat_str = finding.category.value if hasattr(finding.category, "value") else str(finding.category)

        # 5. Assemble context dictionary
        context = {
            "finding_id": finding.finding_id,
            "title": title_meta["text"],
            "title_untrusted_metadata": title_meta,
            "category": cat_str,
            "severity": sev_str,
            "confidence": round(float(finding.confidence), 3),
            "human_verification_required": bool(finding.human_verification_required),
            "observation": obs_meta["text"],
            "observation_untrusted_metadata": obs_meta,
            "impact": impact_meta["text"],
            "recommendation": rec_meta["text"],
            "source": finding.source,
            "element": element_data,
            "evidence": evidence_list,
            "evidence_ids": evidence_ids,
            "detected_framework": detected_framework,
            "is_untrusted_instruction_detected": any_suspicious,
        }
        return context


# Global context builder instance
finding_context_builder = FindingContextBuilder()

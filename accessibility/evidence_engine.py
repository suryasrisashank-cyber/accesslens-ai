"""Evidence Engine for AccessLens AI.

Enforces rigorous multimodal evidence tracking across:
- MEASURED (mathematically calculated values, bounds, contrast ratios)
- DETECTED (programmatic UIA and OCR properties)
- INFERRED (heuristic and visual layout observations)
- RECOMMENDED (developer remediation advice)

Provides EvidenceItem structures and full evidence chain tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from accessibility.findings import (
    AccessibilityFinding, FindingCategory, FindingModel, SignalType
)
from accessibility.severity import FindingSeverity


class EvidenceSource(str, Enum):
    """Normalized sources for all accessibility observations."""
    UI_AUTOMATION = "UI_AUTOMATION"
    OCR = "OCR"
    SCREENSHOT = "SCREENSHOT"
    VISUAL_ANALYSIS = "VISUAL_ANALYSIS"
    CONTRAST_MEASUREMENT = "CONTRAST_MEASUREMENT"
    KEYBOARD_OBSERVATION = "KEYBOARD_OBSERVATION"


@dataclass
class EvidenceItem:
    """Individual evidence record supporting an accessibility finding."""
    source: str
    type: str  # MEASURED, DETECTED, INFERRED, RECOMMENDED
    description: str
    value: Any = None
    confidence: float = 1.0
    element_id: Optional[str] = None
    location: Optional[List[int]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "type": self.type,
            "description": self.description,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "element_id": self.element_id,
            "location": self.location,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        prefix = f"[{self.type}]" if not self.description.startswith(f"[{self.type}]") else ""
        return f"{prefix} {self.description}".strip()


class EvidenceEngine:
    """Classifies, fuses, and validates multi-signal accessibility evidence."""

    @staticmethod
    def create_item(
        source: Union[EvidenceSource, str],
        evidence_type: Union[SignalType, str],
        description: str,
        value: Any = None,
        confidence: float = 1.0,
        element_id: Optional[str] = None,
        location: Optional[List[int]] = None
    ) -> EvidenceItem:
        """Constructs a normalized, timestamped EvidenceItem."""
        src_val = source.value if isinstance(source, Enum) else str(source)
        type_val = evidence_type.value if isinstance(evidence_type, Enum) else str(evidence_type)
        return EvidenceItem(
            source=src_val,
            type=type_val,
            description=description,
            value=value,
            confidence=round(confidence, 3),
            element_id=element_id,
            location=location
        )

    @staticmethod
    def format_evidence_item(signal_type: Union[SignalType, str], message: str) -> str:
        """Prefixes evidence statements with their exact grounded observation category."""
        st_val = signal_type.value if isinstance(signal_type, Enum) else str(signal_type)
        clean_msg = message.replace(f"[{st_val}]", "").strip()
        return f"[{st_val}] {clean_msg}"

    def build_evidence_chain(self, finding: AccessibilityFinding) -> Dict[str, Any]:
        """Exposes the complete evidence chain for explainable accessibility findings:
        Finding -> Why detected -> Evidence -> Recommended action -> Human verification
        """
        evidence_strings = []
        for ev in finding.evidence:
            if isinstance(ev, EvidenceItem):
                evidence_strings.append(str(ev))
            else:
                evidence_strings.append(str(ev))

        return {
            "finding_title": finding.title,
            "severity": finding.severity.value if isinstance(finding.severity, Enum) else str(finding.severity),
            "confidence": round(finding.confidence, 3),
            "observation": finding.observation or finding.title,
            "why_detected": finding.impact or "Assistive technologies rely on standardized programmatic metadata to enable access.",
            "evidence": evidence_strings,
            "recommended_action": finding.recommendation,
            "human_verification": (
                "Confirm the control's purpose and intended spoken label with visual context."
                if finding.human_verification_required else "Verified by deterministic API check."
            ),
            "source": finding.source,
        }

    def fuse_signals(
        self,
        element: Any,
        rule_findings: List[AccessibilityFinding],
        ocr_confidence: float = 0.9,
    ) -> List[AccessibilityFinding]:
        """Validates and fuses findings with element-level visual and programmatic signals."""
        fused_findings: List[AccessibilityFinding] = []

        for finding in rule_findings:
            calibrated_confidence = finding.confidence

            # If OCR text corroborates a UIA finding (e.g. visible text exists but UIA name is missing)
            if hasattr(element, "ocr_associated_text") and element.ocr_associated_text and not (element.name or "").strip():
                if finding.category == FindingCategory.LABEL:
                    calibrated_confidence = min(0.99, calibrated_confidence + 0.04)
                    corroboration = self.create_item(
                        source=EvidenceSource.OCR,
                        evidence_type=SignalType.DETECTED,
                        description=f"Visual text '{element.ocr_associated_text}' visible in bounds, but omitted from UIA accessible name",
                        value=element.ocr_associated_text,
                        confidence=ocr_confidence,
                        element_id=element.element_id or getattr(element, "id", None),
                        location=element.bounds
                    )
                    # Avoid duplicates
                    if not any(corroboration.description in str(e) for e in finding.evidence):
                        finding.evidence.append(corroboration)

            # Ensure all evidence items adhere to normalized EvidenceItem or formatted string
            normalized_evidence = []
            for ev in finding.evidence:
                if isinstance(ev, EvidenceItem):
                    normalized_evidence.append(ev)
                elif any(str(ev).startswith(f"[{st.value}]") for st in SignalType):
                    normalized_evidence.append(str(ev))
                else:
                    normalized_evidence.append(self.format_evidence_item(finding.signal_type, str(ev)))

            finding.evidence = normalized_evidence
            finding.confidence = round(calibrated_confidence, 2)
            fused_findings.append(finding)

        return fused_findings


# Singleton instance
evidence_engine = EvidenceEngine()

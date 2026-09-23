"""Normalized Accessibility Finding data model for AccessLens AI.

Provides the AccessibilityFinding data class representing evidence-grounded
accessibility barriers, observations, and developer recommendations.
Supports both Phase 3 attributes and backward-compatibility aliases.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from accessibility.severity import FindingSeverity, Severity


class FindingCategory(str, Enum):
    """Categorization of accessibility defects according to WCAG principles."""
    LABEL = "NAME_AND_LABEL"              # WCAG 4.1.2 & 2.5.3: Missing or discordant accessible name
    CONTRAST = "COLOR_CONTRAST"          # WCAG 1.4.3: Visual contrast ratio violations
    KEYBOARD = "KEYBOARD_ACCESSIBILITY"  # WCAG 2.1.1: Keyboard focusability and navigation
    TARGET_SIZE = "TOUCH_TARGET_SIZE"    # WCAG 2.5.8: Interactive click/touch target size
    SEMANTICS = "CONTROL_SEMANTICS"      # WCAG 1.3.1: Control role and state semantics
    STRUCTURE = "VISUAL_STRUCTURE"       # Visual hierarchy and focus order alignment


class SignalType(str, Enum):
    """Mandatory classification distinguishing observed evidence types."""
    MEASURED = "MEASURED"          # Mathematically calculated (e.g. contrast 3.1:1, bounds 18x18px)
    DETECTED = "DETECTED"          # Extracted from Windows UIA API or OCR directly
    INFERRED = "INFERRED"          # Heuristic or visual layout observation
    RECOMMENDED = "RECOMMENDED"    # Actionable guidance for developer remediation


class AccessibilityFinding:
    """Normalized evidence-first accessibility finding."""

    def __init__(
        self,
        finding_id: Optional[str] = None,
        title: str = "",
        category: FindingCategory = FindingCategory.LABEL,
        severity: FindingSeverity = FindingSeverity.MEDIUM,
        confidence: float = 0.8,
        status: str = "open",
        affected_element_id: Optional[str] = None,
        source: str = "Windows UI Automation",
        evidence: Optional[List[Any]] = None,
        observation: str = "",
        impact: str = "",
        recommendation: str = "",
        human_verification_required: bool = True,
        created_at: Optional[str] = None,
        # Backward-compatibility kwargs
        id: Optional[str] = None,
        element_id: Optional[str] = None,
        remediation_code: str = "",
        element_name: str = "",
        element_type: str = "",
        element_bounds: Optional[List[int]] = None,
        signal_type: SignalType = SignalType.DETECTED,
        **kwargs
    ):
        self.finding_id = finding_id or id or "finding_unknown"
        self.title = title
        self.category = category
        self.severity = severity
        self.confidence = confidence
        self.status = status
        self.affected_element_id = affected_element_id or element_id
        self.source = source
        self.evidence = evidence if evidence is not None else []
        self.observation = observation or title
        self.impact = impact
        self.recommendation = recommendation
        self.human_verification_required = human_verification_required
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.remediation_code = remediation_code
        self.element_name = element_name
        self.element_type = element_type
        self.element_bounds = element_bounds
        self.signal_type = signal_type

    @property
    def id(self) -> str:
        return self.finding_id

    @id.setter
    def id(self, val: str):
        self.finding_id = val

    @property
    def element_id(self) -> Optional[str]:
        return self.affected_element_id

    @element_id.setter
    def element_id(self, val: Optional[str]):
        self.affected_element_id = val

    def to_dict(self) -> Dict[str, Any]:
        """Serializes finding to a standard dictionary representation."""
        ev_list = []
        for ev in self.evidence:
            if hasattr(ev, "to_dict"):
                ev_list.append(ev.to_dict())
            else:
                ev_list.append(str(ev))

        return {
            "finding_id": self.finding_id,
            "id": self.finding_id,
            "title": self.title,
            "category": self.category.value if isinstance(self.category, Enum) else str(self.category),
            "severity": self.severity.value if isinstance(self.severity, Enum) else str(self.severity),
            "confidence": round(self.confidence, 3),
            "status": self.status,
            "affected_element_id": self.affected_element_id,
            "element_id": self.affected_element_id,
            "source": self.source,
            "evidence": ev_list,
            "observation": self.observation,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "human_verification_required": self.human_verification_required,
            "created_at": self.created_at,
            "remediation_code": self.remediation_code,
            "element_name": self.element_name,
            "element_type": self.element_type,
            "element_bounds": self.element_bounds,
            "signal_type": self.signal_type.value if isinstance(self.signal_type, Enum) else str(self.signal_type),
        }


# Backward Compatibility Alias
FindingModel = AccessibilityFinding

"""Normalized accessibility element models and unified interface snapshot.

Provides normalized models for Windows UI Automation and multimodal accessibility analysis.
Every field that cannot be obtained remains None to prevent fabricated metadata.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


from accessibility.severity import FindingSeverity, Severity, describe_severity
from accessibility.findings import (
    AccessibilityFinding, FindingCategory, FindingModel, SignalType
)


class UIElementModel:
    """Normalized Windows UI element model.

    Every field that cannot be obtained from the system or target application remains None.
    Supports both Phase 1 normalized element model attributes and backward-compatibility aliases.
    """

    def __init__(
        self,
        element_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        control_type: Optional[str] = None,
        name: Optional[str] = None,
        automation_id: Optional[str] = None,
        class_name: Optional[str] = None,
        bounds: Optional[List[int]] = None,
        enabled: Optional[bool] = None,
        visible: Optional[bool] = None,
        focusable: Optional[bool] = None,
        focused: Optional[bool] = None,
        value: Optional[str] = None,
        text: Optional[str] = None,
        children: Optional[List[Any]] = None,
        patterns: Optional[List[str]] = None,
        # Backward compatibility aliases
        id: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        is_visible: Optional[bool] = None,
        is_focusable: Optional[bool] = None,
        has_keyboard_focus: Optional[bool] = None,
        children_ids: Optional[List[str]] = None,
        supported_patterns: Optional[List[str]] = None,
        ocr_associated_text: Optional[str] = None,
        estimated_contrast_ratio: Optional[float] = None,
        findings: Optional[List[FindingModel]] = None,
        raw_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.element_id: Optional[str] = element_id if element_id is not None else id
        self.parent_id: Optional[str] = parent_id
        self.control_type: Optional[str] = control_type
        self.name: Optional[str] = name
        self.automation_id: Optional[str] = automation_id
        self.class_name: Optional[str] = class_name
        self.bounds: Optional[List[int]] = bounds
        self.enabled: Optional[bool] = enabled if enabled is not None else is_enabled
        self.visible: Optional[bool] = visible if visible is not None else is_visible
        self.focusable: Optional[bool] = focusable if focusable is not None else is_focusable
        self.focused: Optional[bool] = focused if focused is not None else has_keyboard_focus
        self.value: Optional[str] = value
        self.text: Optional[str] = text
        self.children: List[Any] = children if children is not None else []
        self.patterns: List[str] = patterns if patterns is not None else (supported_patterns or [])

        # Additional metadata and analysis fields
        self._children_ids: List[str] = children_ids or []
        self.ocr_associated_text: str = ocr_associated_text or ""
        self.estimated_contrast_ratio: Optional[float] = estimated_contrast_ratio
        self.findings: List[FindingModel] = findings or []
        self.raw_data: Dict[str, Any] = raw_data or {}
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def id(self) -> str:
        return self.element_id or ""

    @id.setter
    def id(self, val: str):
        self.element_id = val

    @property
    def is_enabled(self) -> bool:
        return self.enabled if self.enabled is not None else True

    @is_enabled.setter
    def is_enabled(self, val: bool):
        self.enabled = val

    @property
    def is_visible(self) -> bool:
        return self.visible if self.visible is not None else True

    @is_visible.setter
    def is_visible(self, val: bool):
        self.visible = val

    @property
    def is_focusable(self) -> bool:
        return self.focusable if self.focusable is not None else False

    @is_focusable.setter
    def is_focusable(self, val: bool):
        self.focusable = val

    @property
    def has_keyboard_focus(self) -> bool:
        return self.focused if self.focused is not None else False

    @has_keyboard_focus.setter
    def has_keyboard_focus(self, val: bool):
        self.focused = val

    @property
    def supported_patterns(self) -> List[str]:
        return self.patterns

    @supported_patterns.setter
    def supported_patterns(self, val: List[str]):
        self.patterns = val

    @property
    def children_ids(self) -> List[str]:
        if self._children_ids:
            return self._children_ids
        return [c.element_id for c in self.children if hasattr(c, "element_id") and c.element_id]

    @children_ids.setter
    def children_ids(self, val: List[str]):
        self._children_ids = val

    @property
    def display_label(self) -> str:
        """Returns human-friendly representation for element lists."""
        name_str = f'"{self.name}"' if self.name else "<No Accessible Name>"
        ctype = self.control_type or "UnknownControl"
        return f"[{ctype}] {name_str}"

    @property
    def bounding_box_dict(self) -> dict:
        b = self.bounds or [0, 0, 0, 0]
        x, y, w, h = b[0], b[1], b[2], b[3]
        return {
            "box": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
            "text": self.name or self.control_type or "",
            "confidence": 1.0
        }

    def get_property_display(self, prop_name: str) -> str:
        """Returns human-friendly string or 'Not available' if property is None."""
        val = getattr(self, prop_name, None)
        if val is None:
            return "Not available"
        if isinstance(val, bool):
            return "True" if val else "False"
        if isinstance(val, (list, tuple)):
            if not val:
                return "Not available"
            return str(val)
        s = str(val).strip()
        return s if s else "Not available"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_id": self.element_id,
            "id": self.id,
            "name": self.name,
            "control_type": self.control_type,
            "automation_id": self.automation_id,
            "class_name": self.class_name,
            "bounds": self.bounds,
            "enabled": self.enabled,
            "visible": self.visible,
            "focusable": self.focusable,
            "focused": self.focused,
            "value": self.value,
            "text": self.text,
            "parent_id": self.parent_id,
            "children_count": len(self.children) if self.children else len(self.children_ids),
            "patterns": self.patterns,
            "supported_patterns": self.supported_patterns,
            "ocr_associated_text": self.ocr_associated_text,
            "estimated_contrast_ratio": self.estimated_contrast_ratio,
            "findings_count": len(self.findings),
        }


# Section 1.3 ElementModel alias
ElementModel = UIElementModel


@dataclass
class InterfaceSnapshot:
    """Unified multimodal state capturing UIA tree, OCR, screenshot, and findings."""
    timestamp: str
    application_name: str
    window_title: str
    ui_tree: Optional[Any] = None
    hardware_state: str = ""
    backend: str = ""

    # Future phase fields
    ocr_result: Optional[Any] = None
    visual_observations: List[Any] = field(default_factory=list)
    deterministic_findings: List[Any] = field(default_factory=list)
    keyboard_observations: List[Any] = field(default_factory=list)
    evidence: List[Any] = field(default_factory=list)

    # Backward compatibility fields
    window_handle: int = 0
    elements: List[UIElementModel] = field(default_factory=list)
    ocr_text: str = ""
    screenshot_path: Optional[str] = None
    screen_dimensions: Tuple[int, int] = (1920, 1080)
    findings: List[FindingModel] = field(default_factory=list)
    backend_state: str = "CPU"
    hardware_summary: str = ""
    audit_duration_ms: float = 0.0
    keyboard_order: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Sync ui_tree and elements
        if self.ui_tree is not None and not self.elements:
            if hasattr(self.ui_tree, "elements"):
                self.elements = list(self.ui_tree.elements)
        elif self.elements and self.ui_tree is None:
            from accessibility.ui_tree import UITree
            self.ui_tree = UITree(self.elements)

        # Sync backend representations
        if self.backend and not self.backend_state:
            self.backend_state = self.backend
        elif self.backend_state and not self.backend:
            self.backend = self.backend_state

        # Sync hardware summaries
        if self.hardware_state and not self.hardware_summary:
            self.hardware_summary = self.hardware_state
        elif self.hardware_summary and not self.hardware_state:
            self.hardware_state = self.hardware_summary

        # Sync findings
        if self.deterministic_findings and not self.findings:
            self.findings = list(self.deterministic_findings)
        elif self.findings and not self.deterministic_findings:
            self.deterministic_findings = list(self.findings)

    @property
    def critical_findings_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.CRITICAL)

    @property
    def high_findings_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.HIGH)

    @property
    def medium_findings_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.MEDIUM)

    @property
    def low_findings_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.LOW)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "application_name": self.application_name,
            "window_title": self.window_title,
            "window_handle": self.window_handle,
            "screen_dimensions": list(self.screen_dimensions),
            "elements_count": len(self.elements),
            "elements": [e.to_dict() for e in self.elements],
            "ocr_text_length": len(self.ocr_text),
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "severity_summary": {
                "critical": self.critical_findings_count,
                "high": self.high_findings_count,
                "medium": self.medium_findings_count,
                "low": self.low_findings_count,
            },
            "backend": self.backend,
            "backend_state": self.backend_state,
            "hardware_state": self.hardware_state,
            "hardware_summary": self.hardware_summary,
            "audit_duration_ms": round(self.audit_duration_ms, 2),
            "keyboard_order": self.keyboard_order,
        }

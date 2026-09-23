"""Structured data models for Keyboard Navigation & Focus Traversal in AccessLens AI.

Defines FocusObservation and FocusTraversalResult models capturing step-by-step
keyboard traversal observations, sequence analysis, and detection results.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from accessibility.findings import AccessibilityFinding


@dataclass
class FocusObservation:
    """Individual observation captured during keyboard focus traversal."""
    observation_id: str
    element_id: Optional[str] = None
    element_name: Optional[str] = None
    control_type: Optional[str] = None
    automation_id: Optional[str] = None
    class_name: Optional[str] = None
    bounds: Optional[List[int]] = None
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    traversal_index: int = 0
    direction: str = "forward"  # "forward" (Tab) or "reverse" (Shift+Tab)
    source: str = "Windows UI Automation"
    confidence: float = 0.90
    notes: str = ""
    is_focused: bool = True
    is_enabled: bool = True
    is_visible: bool = True
    hwnd: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes observation to standard dictionary."""
        return {
            "observation_id": self.observation_id,
            "element_id": self.element_id,
            "element_name": self.element_name,
            "control_type": self.control_type,
            "automation_id": self.automation_id,
            "class_name": self.class_name,
            "bounds": list(self.bounds) if self.bounds else None,
            "timestamp": self.timestamp,
            "traversal_index": self.traversal_index,
            "direction": self.direction,
            "source": self.source,
            "confidence": round(self.confidence, 3),
            "notes": self.notes,
            "is_focused": self.is_focused,
            "is_enabled": self.is_enabled,
            "is_visible": self.is_visible,
            "hwnd": self.hwnd,
        }


@dataclass
class FocusTraversalResult:
    """Comprehensive summary of a keyboard focus traversal audit."""
    target_window: str = "Unknown Window"
    target_hwnd: Optional[int] = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    direction: str = "forward"
    observations: List[FocusObservation] = field(default_factory=list)
    unique_elements: int = 0
    repeated_elements: int = 0
    traversal_complete: bool = True
    loop_detected: bool = False
    focus_trap_detected: bool = False
    unreachable_elements: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    findings: List[AccessibilityFinding] = field(default_factory=list)
    human_verification_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes traversal result to dictionary."""
        return {
            "target_window": self.target_window,
            "target_hwnd": self.target_hwnd,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "direction": self.direction,
            "observations": [obs.to_dict() for obs in self.observations],
            "unique_elements": self.unique_elements,
            "repeated_elements": self.repeated_elements,
            "traversal_complete": self.traversal_complete,
            "loop_detected": self.loop_detected,
            "focus_trap_detected": self.focus_trap_detected,
            "unreachable_elements": self.unreachable_elements,
            "warnings": list(self.warnings),
            "findings": [f.to_dict() for f in self.findings],
            "human_verification_required": self.human_verification_required,
        }

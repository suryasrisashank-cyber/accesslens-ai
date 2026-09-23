"""Keyboard accessibility auditing subsystem.

Tracks focus transitions (Tab / Shift+Tab), evaluates focus sequence order,
detects keyboard traps, unreachable interactive elements, and duplicate focus loops.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from accessibility.element_model import (
    FindingCategory, FindingModel, FindingSeverity,
    SignalType, UIElementModel
)
from accessibility.ui_tree import UITree


@dataclass
class FocusStep:
    """Recorded snapshot of an individual keyboard focus landing."""
    step_number: int
    control_name: str
    control_type: str
    automation_id: str
    bounds: List[int]
    is_focusable: bool = True
    time_offset_ms: float = 0.0


@dataclass
class KeyboardAuditReport:
    """Summary of a keyboard accessibility audit run."""
    steps: List[FocusStep] = field(default_factory=list)
    unreachable_elements: List[UIElementModel] = field(default_factory=list)
    findings: List[FindingModel] = field(default_factory=list)
    is_complete: bool = True
    summary_message: str = ""


class KeyboardAuditor:
    """Audits keyboard navigation flow without destructive actions."""

    def __init__(self):
        self._history: List[FocusStep] = []
        self._is_active: bool = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    def start_audit(self):
        self._history.clear()
        self._is_active = True

    def record_focus(
        self,
        name: str,
        control_type: str,
        automation_id: str = "",
        bounds: Optional[List[int]] = None
    ) -> FocusStep:
        """Records an element receiving keyboard focus."""
        step = FocusStep(
            step_number=len(self._history) + 1,
            control_name=name or "<Unnamed>",
            control_type=control_type,
            automation_id=automation_id,
            bounds=bounds or [0, 0, 0, 0]
        )
        self._history.append(step)
        return step

    def stop_audit(self, tree: Optional[UITree] = None) -> KeyboardAuditReport:
        """Finalizes audit and evaluates observed focus sequence against UI elements."""
        self._is_active = False
        findings: List[FindingModel] = []
        unreachable: List[UIElementModel] = []

        # 1. Check for Duplicate Consecutive Focus (Focus Bounce)
        for i in range(1, len(self._history)):
            prev = self._history[i - 1]
            curr = self._history[i]
            if prev.automation_id and prev.automation_id == curr.automation_id:
                findings.append(FindingModel(
                    id=f"kb_dup_focus_{i}",
                    title="Duplicate Focus on Consecutive Tab",
                    category=FindingCategory.KEYBOARD,
                    severity=FindingSeverity.LOW,
                    confidence=0.90,
                    evidence=[
                        f"[DETECTED] Control '{curr.control_name}' received consecutive focus at steps {prev.step_number} and {curr.step_number}",
                        "[INFERRED] Redundant tab stop forces extra keystrokes for keyboard navigators"
                    ],
                    recommendation="Ensure child elements inside composite controls do not create multiple duplicate tab stops.",
                    source="Keyboard Audit Focus Sequence",
                    signal_type=SignalType.DETECTED
                ))

        # 2. Check for Potential Keyboard Trap (Repeated 2-element loop)
        if len(self._history) >= 4:
            last4 = [s.automation_id or s.control_name for s in self._history[-4:]]
            if last4[0] == last4[2] and last4[1] == last4[3] and last4[0] != last4[1]:
                findings.append(FindingModel(
                    id="kb_focus_trap_warning",
                    title="Potential Keyboard Navigation Trap Detected",
                    category=FindingCategory.KEYBOARD,
                    severity=FindingSeverity.CRITICAL,
                    confidence=0.86,
                    evidence=[
                        f"[DETECTED] Navigation alternated between '{last4[0]}' and '{last4[1]}' repeatedly",
                        "[INFERRED] Focus cannot advance past these elements using standard Tab key traversal"
                    ],
                    recommendation="Verify that modal or container controls release keyboard focus when the last child control is tabbed past.",
                    remediation_code="// Ensure container tab continuation:\nKeyboardNavigation.SetTabNavigation(container, KeyboardNavigationMode.Continue);",
                    source="Keyboard Focus Traversal Monitor",
                    signal_type=SignalType.INFERRED
                ))

        # 3. Check for Unreachable Interactive Elements
        if tree is not None:
            interactive = tree.get_interactive_elements()
            visited_ids = {s.automation_id for s in self._history if s.automation_id}
            visited_names = {s.control_name for s in self._history if s.control_name}

            for el in interactive:
                # If neither ID nor Name was visited
                matched_id = el.automation_id in visited_ids if el.automation_id else False
                matched_name = el.name in visited_names if el.name else False

                if not matched_id and not matched_name:
                    unreachable.append(el)

            if unreachable and len(self._history) > 3:
                findings.append(FindingModel(
                    id="kb_unreachable_controls",
                    title="Interactive Elements Not Reached in Focus Traversal",
                    category=FindingCategory.KEYBOARD,
                    severity=FindingSeverity.HIGH,
                    confidence=0.88,
                    evidence=[
                        f"[MEASURED] {len(unreachable)} interactive controls were never reached during the audit sequence",
                        f"[DETECTED] First unreachable control: [{unreachable[0].control_type}] \"{unreachable[0].name}\""
                    ],
                    recommendation="Ensure all interactive buttons, links, and form fields are included in the logical tab traversal order.",
                    source="Keyboard Audit Coverage Analysis",
                    signal_type=SignalType.MEASURED
                ))

        summary = f"Audit complete. Recorded {len(self._history)} focus transitions. Detected {len(findings)} potential focus barriers."

        return KeyboardAuditReport(
            steps=list(self._history),
            unreachable_elements=unreachable,
            findings=findings,
            is_complete=True,
            summary_message=summary
        )

    def simulate_audit_from_tree(self, tree: UITree) -> KeyboardAuditReport:
        """Simulates tab traversal order for deterministic testing and synthetic demo app."""
        self.start_audit()
        interactive = tree.get_interactive_elements()

        # Sort spatially top-to-bottom, left-to-right
        sorted_elements = sorted(interactive, key=lambda e: (e.bounds[1], e.bounds[0]))

        for el in sorted_elements:
            if el.is_focusable:
                self.record_focus(
                    name=el.name,
                    control_type=el.control_type,
                    automation_id=el.automation_id,
                    bounds=el.bounds
                )

        return self.stop_audit(tree)


# Singleton instance
keyboard_auditor = KeyboardAuditor()

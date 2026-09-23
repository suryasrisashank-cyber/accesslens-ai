"""Deterministic Accessibility Rule Engine for AccessLens AI.

Executes evidence-first accessibility evaluations connecting:
Windows UI Automation + OCR + Screenshot analysis + Deterministic rules -> Findings.
Separates confidence from severity, supports modular rule toggling,
and flags human verification requirements for every contextual observation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from PIL import Image

from accessibility.contrast_engine import sample_region_contrast
from accessibility.evidence_engine import EvidenceItem, EvidenceSource, evidence_engine
from accessibility.findings import (
    AccessibilityFinding, FindingCategory, FindingModel, SignalType
)
from accessibility.severity import FindingSeverity
from accessibility.ui_tree import UITree


class BaseRule(ABC):
    """Abstract base class for modular deterministic accessibility rules."""

    def __init__(self, rule_id: str, name: str, enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.enabled = enabled

    @abstractmethod
    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        """Evaluates an individual element and returns any detected findings."""
        pass


class MissingAccessibleNameRule(BaseRule):
    """Rule 1: Detects interactive controls with empty or missing accessible names."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_01_MISSING_NAME",
            name="Missing Accessible Name"
        )
        self.interactive_types = {
            "button", "edit", "checkbox", "radiobutton", "combobox",
            "hyperlink", "menuitem", "tabitem", "slider"
        }

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        ctype = (element.control_type or "").strip().lower()
        if ctype not in self.interactive_types:
            # Check if element has interactive patterns
            patterns = element.patterns or getattr(element, "supported_patterns", [])
            if not any("invoke" in p.lower() or "toggle" in p.lower() for p in patterns):
                return []

        name = (element.name or "").strip()
        if not name:
            eid = element.element_id or getattr(element, "id", "elem")
            return [AccessibilityFinding(
                finding_id=f"missing_name_{eid}",
                title="Missing Accessible Name on Interactive Control",
                category=FindingCategory.LABEL,
                severity=FindingSeverity.HIGH if ctype in ["button", "edit"] else FindingSeverity.MEDIUM,
                confidence=0.95,
                affected_element_id=eid,
                source="Windows UI Automation",
                evidence=[
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=f"Control type '{element.control_type}' is interactive",
                        value=element.control_type,
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description="UIA Name property is empty, null, or whitespace",
                        value=None,
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=f"Focusable: {element.is_focusable}; Enabled: {element.is_enabled}",
                        value={"focusable": element.is_focusable, "enabled": element.is_enabled},
                        element_id=eid
                    )
                ],
                observation=f"Interactive {element.control_type} exposes no accessible name through UI Automation.",
                impact="Assistive technologies (screen readers, braille displays) cannot announce the purpose or action of this control.",
                recommendation="Provide an explicit, descriptive accessible name using AutomationProperties.Name (XAML/WinUI) or AccessibleName (WinForms).",
                remediation_code=f'AutomationProperties.SetName(control, "{ctype.capitalize()} Action");',
                human_verification_required=True,
                element_name="",
                element_type=element.control_type or "Control",
                element_bounds=element.bounds,
                signal_type=SignalType.DETECTED
            )]
        return []


class NameMismatchRule(BaseRule):
    """Rule 2: Compares OCR visible text with UI Automation accessible name."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_02_NAME_MISMATCH",
            name="Visible Label / Accessible Name Mismatch"
        )

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        ocr_text = getattr(element, "ocr_associated_text", "").strip()
        acc_name = (element.name or "").strip()

        # Only evaluate when both OCR text and accessible name exist with sufficient characters
        if not ocr_text or not acc_name or len(ocr_text) < 3 or len(acc_name) < 3:
            return []

        vis = ocr_text.lower()
        acc = acc_name.lower()

        # If visible label is not contained in accessible name or vice-versa
        if vis not in acc and acc not in vis:
            eid = element.element_id or getattr(element, "id", "elem")
            return [AccessibilityFinding(
                finding_id=f"name_mismatch_{eid}",
                title="Visible Label vs Accessible Name Discrepancy",
                category=FindingCategory.LABEL,
                severity=FindingSeverity.MEDIUM,
                confidence=0.86,
                affected_element_id=eid,
                source="OCR + UI Automation Label Mismatch Rule",
                evidence=[
                    evidence_engine.create_item(
                        source=EvidenceSource.OCR,
                        evidence_type=SignalType.DETECTED,
                        description=f"Visible text recognized by on-device OCR: '{ocr_text}'",
                        value=ocr_text,
                        element_id=eid,
                        location=element.bounds
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=f"Programmatic Accessible Name from UIA: '{acc_name}'",
                        value=acc_name,
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.VISUAL_ANALYSIS,
                        evidence_type=SignalType.INFERRED,
                        description="Speech recognition users vocalizing the visible label will fail to activate this control",
                        element_id=eid
                    )
                ],
                observation=f"Control visually shows '{ocr_text}' but exposes accessible name '{acc_name}'.",
                impact="Speech-to-text operators calling out the visible label may fail to activate this control. Potential label-in-name discrepancy — WCAG reference 2.5.3. Human verification required.",
                recommendation=f"Update the programmatic accessible name to incorporate or match the visible label '{ocr_text}'.",
                remediation_code=f'AutomationProperties.SetName(control, "{ocr_text}");',
                human_verification_required=True,
                element_name=acc_name,
                element_type=element.control_type or "Control",
                element_bounds=element.bounds,
                signal_type=SignalType.DETECTED
            )]
        return []


class SemanticMismatchRule(BaseRule):
    """Rule 3: Flags generic or custom controls that visually or programmatically behave as action controls."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_03_UNCLEAR_SEMANTICS",
            name="Unclear Control Semantics"
        )

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        ctype = (element.control_type or "").strip().lower()
        if ctype in ["custom", "pane", "group"]:
            patterns = element.patterns or getattr(element, "supported_patterns", [])
            has_action = any("invoke" in p.lower() or "toggle" in p.lower() for p in patterns)
            if has_action:
                eid = element.element_id or getattr(element, "id", "elem")
                return [AccessibilityFinding(
                    finding_id=f"unclear_semantics_{eid}",
                    title="Unclear Control Semantics",
                    category=FindingCategory.SEMANTICS,
                    severity=FindingSeverity.LOW,
                    confidence=0.72,
                    affected_element_id=eid,
                    source="Windows UI Automation",
                    evidence=[
                        evidence_engine.create_item(
                            source=EvidenceSource.UI_AUTOMATION,
                            evidence_type=SignalType.DETECTED,
                            description=f"UIA reports generic control type '{element.control_type}'",
                            value=element.control_type,
                            element_id=eid
                        ),
                        evidence_engine.create_item(
                            source=EvidenceSource.UI_AUTOMATION,
                            evidence_type=SignalType.DETECTED,
                            description=f"Supported patterns include action pattern: {patterns}",
                            value=patterns,
                            element_id=eid
                        ),
                        evidence_engine.create_item(
                            source=EvidenceSource.VISUAL_ANALYSIS,
                            evidence_type=SignalType.INFERRED,
                            description="Control behaves interactively but exposes generic container semantics",
                            element_id=eid
                        )
                    ],
                    observation=f"Generic control type '{element.control_type}' supports interactive action patterns.",
                    impact="Screen readers may announce a container rather than an interactive action.",
                    recommendation="Expose an explicit control type role such as Button, TabItem, or Hyperlink.",
                    remediation_code="// Expose standard control semantics in custom peer:\nprotected override AutomationControlType GetAutomationControlTypeCore() => AutomationControlType.Button;",
                    human_verification_required=True,
                    element_name=element.name or "",
                    element_type=element.control_type or "Custom",
                    element_bounds=element.bounds,
                    signal_type=SignalType.INFERRED
                )]
        return []


class FocusabilityRule(BaseRule):
    """Rule 4: Checks whether interactive controls are keyboard focusable."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_04_KEYBOARD_FOCUSABILITY",
            name="Keyboard Focusability"
        )
        self.interactive_types = {
            "button", "edit", "checkbox", "radiobutton", "combobox",
            "hyperlink", "menuitem", "tabitem", "slider"
        }

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        ctype = (element.control_type or "").strip().lower()
        if ctype in self.interactive_types:
            if element.is_enabled and element.is_visible and not element.is_focusable:
                eid = element.element_id or getattr(element, "id", "elem")
                return [AccessibilityFinding(
                    finding_id=f"unfocusable_{eid}",
                    title="Potential Keyboard Accessibility Issue (Control Not Focusable)",
                    category=FindingCategory.KEYBOARD,
                    severity=FindingSeverity.HIGH,
                    confidence=0.91,
                    affected_element_id=eid,
                    source="Windows UI Automation",
                    evidence=[
                        evidence_engine.create_item(
                            source=EvidenceSource.UI_AUTOMATION,
                            evidence_type=SignalType.DETECTED,
                            description=f"Interactive control type: {element.control_type}",
                            value=element.control_type,
                            element_id=eid
                        ),
                        evidence_engine.create_item(
                            source=EvidenceSource.UI_AUTOMATION,
                            evidence_type=SignalType.DETECTED,
                            description="IsKeyboardFocusable is False while IsEnabled and Visible are True",
                            value=False,
                            element_id=eid
                        )
                    ],
                    observation=f"Interactive {element.control_type} is visible and enabled but reports IsKeyboardFocusable=False.",
                    impact="Keyboard-only users, switch operators, and screen-reader users may be unable to navigate to or invoke this element.",
                    recommendation="Enable keyboard focusability by setting IsTabStop=True (XAML) or TabStop=True (WinForms).",
                    remediation_code="control.IsTabStop = true;\ncontrol.Focusable = true;",
                    human_verification_required=True,
                    element_name=element.name or "",
                    element_type=element.control_type or "Control",
                    element_bounds=element.bounds,
                    signal_type=SignalType.DETECTED
                )]
        return []


class InteractiveSizeRule(BaseRule):
    """Rule 6: Observes interactive target size dimensions."""

    def __init__(self, min_size: int = 24):
        super().__init__(
            rule_id="RULE_06_TARGET_SIZE",
            name="Interactive Region Size"
        )
        self.min_size = min_size

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        ctype = (element.control_type or "").strip().lower()
        interactive_types = {
            "button", "checkbox", "radiobutton", "combobox",
            "hyperlink", "menuitem", "tabitem"
        }
        if ctype in interactive_types and element.bounds and len(element.bounds) == 4:
            w, h = element.bounds[2], element.bounds[3]
            if 0 < w < self.min_size or 0 < h < self.min_size:
                eid = element.element_id or getattr(element, "id", "elem")
                return [AccessibilityFinding(
                    finding_id=f"target_size_{eid}",
                    title="Undersized Interactive Target (Potentially Small Interactive Target)",
                    category=FindingCategory.TARGET_SIZE,
                    severity=FindingSeverity.MEDIUM if min(w, h) < 18 else FindingSeverity.LOW,
                    confidence=0.94,
                    affected_element_id=eid,
                    source="Geometric Measurement Rule",
                    evidence=[
                        evidence_engine.create_item(
                            source=EvidenceSource.UI_AUTOMATION,
                            evidence_type=SignalType.MEASURED,
                            description=f"Measured target dimensions: {w}x{h} px (Bounds: {element.bounds})",
                            value={"width": w, "height": h, "bounds": element.bounds},
                            element_id=eid,
                            location=element.bounds
                        ),
                        evidence_engine.create_item(
                            source=EvidenceSource.VISUAL_ANALYSIS,
                            evidence_type=SignalType.MEASURED,
                            description=f"Recommended minimum dimension: {self.min_size}x{self.min_size} px",
                            value=self.min_size,
                            element_id=eid
                        )
                    ],
                    observation=f"Interactive target region ({w}x{h} px) is below the recommended {self.min_size}x{self.min_size} px threshold.",
                    impact="Users with motor control challenges or tremors may find it difficult to activate small click/touch areas without accidental misclicks.",
                    recommendation=f"Increase minimum dimension or touch padding to at least {self.min_size}x{self.min_size} pixels.",
                    remediation_code=f"control.MinHeight = {self.min_size};\ncontrol.MinWidth = {self.min_size};\ncontrol.Padding = new Thickness(6);",
                    human_verification_required=True,
                    element_name=element.name or "",
                    element_type=element.control_type or "Control",
                    element_bounds=element.bounds,
                    signal_type=SignalType.MEASURED
                )]
        return []


class LabelRule(BaseRule):
    """Rule 7: Inspects user input controls for missing or unclear accessible labels."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_07_INPUT_LABEL",
            name="Missing / Unclear Label"
        )
        self.input_types = {"edit", "combobox", "slider", "listbox"}

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        ctype = (element.control_type or "").strip().lower()
        if ctype in self.input_types:
            name = (element.name or "").strip()
            ocr_text = getattr(element, "ocr_associated_text", "").strip()

            if not name and not ocr_text:
                eid = element.element_id or getattr(element, "id", "elem")
                return [AccessibilityFinding(
                    finding_id=f"input_label_{eid}",
                    title="Input May Lack a Clear Accessible Label",
                    category=FindingCategory.LABEL,
                    severity=FindingSeverity.MEDIUM,
                    confidence=0.88,
                    affected_element_id=eid,
                    source="Windows UI Automation",
                    evidence=[
                        evidence_engine.create_item(
                            source=EvidenceSource.UI_AUTOMATION,
                            evidence_type=SignalType.DETECTED,
                            description=f"Input control type: {element.control_type}",
                            value=element.control_type,
                            element_id=eid
                        ),
                        evidence_engine.create_item(
                            source=EvidenceSource.UI_AUTOMATION,
                            evidence_type=SignalType.DETECTED,
                            description="No accessible name or correlated nearby label detected",
                            element_id=eid
                        )
                    ],
                    observation=f"Input field ({element.control_type}) does not expose an accessible label or nearby prompt text.",
                    impact="Screen reader users encountering this input field may not know what information is requested.",
                    recommendation="Associate a visible TextBlock with this input using AutomationProperties.LabeledBy or assign AutomationProperties.Name.",
                    remediation_code="AutomationProperties.SetLabeledBy(inputControl, promptTextBlock);",
                    human_verification_required=True,
                    element_name="",
                    element_type=element.control_type or "Input",
                    element_bounds=element.bounds,
                    signal_type=SignalType.DETECTED
                )]
        return []


class ContrastRule(BaseRule):
    """Evaluates rendered visual color contrast against WCAG 1.4.3."""

    def __init__(self, min_contrast: float = 4.5):
        super().__init__(
            rule_id="RULE_08_COLOR_CONTRAST",
            name="Color Contrast Evaluation"
        )
        self.min_contrast = min_contrast

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        if screenshot is None or not element.bounds or len(element.bounds) < 4:
            return []

        w, h = element.bounds[2], element.bounds[3]
        if w < 8 or h < 8:
            return []

        contrast_res = sample_region_contrast(screenshot, element.bounds)
        if contrast_res is None:
            return []

        element.estimated_contrast_ratio = contrast_res.contrast_ratio

        if not contrast_res.passes_aa_normal:
            eid = element.element_id or getattr(element, "id", "elem")
            return [AccessibilityFinding(
                finding_id=f"contrast_{eid}",
                title="Potential Contrast Issue",
                category=FindingCategory.CONTRAST,
                severity=FindingSeverity.HIGH if contrast_res.contrast_ratio < 3.0 else FindingSeverity.MEDIUM,
                confidence=0.84,
                affected_element_id=eid,
                source="Rendered Pixel Contrast Measurement",
                evidence=[
                    evidence_engine.create_item(
                        source=EvidenceSource.CONTRAST_MEASUREMENT,
                        evidence_type=SignalType.MEASURED,
                        description=f"Estimated contrast ratio: {contrast_res.contrast_ratio:.2f}:1 (Required: {self.min_contrast}:1)",
                        value=contrast_res.contrast_ratio,
                        element_id=eid,
                        location=element.bounds
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.CONTRAST_MEASUREMENT,
                        evidence_type=SignalType.MEASURED,
                        description=f"Estimated colors: Foreground {contrast_res.fg_hex}, Background {contrast_res.bg_hex}",
                        value={"fg": contrast_res.fg_hex, "bg": contrast_res.bg_hex},
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.SCREENSHOT,
                        evidence_type=SignalType.INFERRED,
                        description=f"Method: {contrast_res.method}. {contrast_res.limitations}",
                        element_id=eid
                    )
                ],
                observation=f"Rendered element region exhibits estimated contrast ratio of {contrast_res.contrast_ratio:.2f}:1, below the {self.min_contrast}:1 standard.",
                impact="Low contrast text causes difficulty for users with low vision, age-related vision degradation, or under high-glare environments.",
                recommendation=f"Increase visual luminance difference between text ({contrast_res.fg_hex}) and background ({contrast_res.bg_hex}) to at least {self.min_contrast}:1.",
                remediation_code=f"control.Foreground = new SolidColorBrush(Colors.White);\ncontrol.Background = new SolidColorBrush(Color.FromRgb(30, 30, 40));",
                human_verification_required=True,
                element_name=element.name or "",
                element_type=element.control_type or "Control",
                element_bounds=element.bounds,
                signal_type=SignalType.MEASURED
            )]
        return []



class FocusTrapRule(BaseRule):
    """Rule 9: Detects potential keyboard focus traps where focus enters a region and cannot escape."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_09_FOCUS_TRAP",
            name="Potential Keyboard Focus Trap"
        )

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        is_trapped = getattr(element, "is_focus_trapped", False) or getattr(element, "potential_trap", False)
        if is_trapped:
            eid = getattr(element, "element_id", None) or getattr(element, "id", "elem_trap")
            ename = getattr(element, "name", "") or "<Unnamed>"
            return [AccessibilityFinding(
                finding_id=f"kb_trap_{eid}",
                title="Potential Keyboard Focus Trap",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.MEDIUM,
                confidence=0.85,
                affected_element_id=eid,
                source="Keyboard Traversal Monitor",
                evidence=[
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=f"Focus entered element region '{ename}' and failed to advance past sub-cycle",
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.INFERRED,
                        description="Navigation cannot advance past this control using standard Tab traversal",
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.RECOMMENDED,
                        description="Verify whether keyboard focus can intentionally enter and exit this region",
                        element_id=eid
                    )
                ],
                observation=f"Element '{ename}' appears to entrap keyboard focus within a cyclical subset during Tab traversal.",
                impact="Keyboard-only users may become unable to navigate away from this control or container.",
                recommendation="Verify whether keyboard focus can intentionally enter and exit this region. Provide standard Tab continuation or Escape key exit.",
                remediation_code="// Ensure container allows Tab traversal continuation:\nKeyboardNavigation.SetTabNavigation(container, KeyboardNavigationMode.Continue);",
                human_verification_required=True,
                element_name=ename,
                element_type=getattr(element, "control_type", "Control") or "Control",
                element_bounds=getattr(element, "bounds", None),
                signal_type=SignalType.DETECTED
            )]
        return []


class UnreachedInteractiveElementRule(BaseRule):
    """Rule 10: Detects interactive controls in the UI tree that were not observed during keyboard traversal."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_10_UNREACHED_ELEMENT",
            name="Interactive Element Not Observed During Traversal"
        )

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        was_reached = getattr(element, "was_reached_in_traversal", None)
        is_interactive = getattr(element, "is_focusable", False) or getattr(element, "control_type", "") in [
            "Button", "Edit", "CheckBox", "RadioButton", "ComboBox", "Hyperlink"
        ]

        if is_interactive and was_reached is False:
            eid = getattr(element, "element_id", None) or getattr(element, "id", "elem_unreached")
            ename = getattr(element, "name", "") or "<Unnamed>"
            ctype = getattr(element, "control_type", "Control")
            return [AccessibilityFinding(
                finding_id=f"kb_unreached_{eid}",
                title="Interactive Element Not Observed During Traversal",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.LOW,
                confidence=0.80,
                affected_element_id=eid,
                source="Keyboard Traversal Coverage Analysis",
                evidence=[
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.MEASURED,
                        description=f"Control type '{ctype}' is interactive with Focusable={getattr(element, 'is_focusable', True)}",
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description="Element was not observed in the tested traversal sequence",
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.RECOMMENDED,
                        description="Verify whether this control should be included in the primary keyboard tab order",
                        element_id=eid
                    )
                ],
                observation=f"Interactive control '{ename}' ({ctype}) was not observed during this keyboard traversal.",
                impact="Keyboard users navigating by Tab may be unable to reach or activate controls not included in the primary tab order.",
                recommendation="Verify whether this control should be reachable via sequential keyboard Tab navigation or if exclusion is intentional.",
                remediation_code="// Ensure control is included in Tab order:\ncontrol.IsTabStop = true;\ncontrol.TabIndex = tabOrderIndex;",
                human_verification_required=True,
                element_name=ename,
                element_type=ctype,
                element_bounds=getattr(element, "bounds", None),
                signal_type=SignalType.DETECTED
            )]
        return []


class FocusLoopRule(BaseRule):
    """Rule 11: Detects unexpected focus loops where navigation repeatedly cycles through the same elements."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_11_FOCUS_LOOP",
            name="Unexpected Focus Loop"
        )

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        is_loop_member = getattr(element, "is_focus_loop_member", False)
        if is_loop_member:
            eid = getattr(element, "element_id", None) or getattr(element, "id", "elem_loop")
            ename = getattr(element, "name", "") or "<Unnamed>"
            return [AccessibilityFinding(
                finding_id=f"kb_loop_{eid}",
                title="Unexpected Keyboard Focus Loop Observed",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.MEDIUM,
                confidence=0.85,
                affected_element_id=eid,
                source="Keyboard Traversal Monitor",
                evidence=[
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=f"Element '{ename}' participated in a repeated cyclical traversal pattern",
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.INFERRED,
                        description="Navigation repeats previous targets rather than progressing to subsequent interface controls",
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.RECOMMENDED,
                        description="Verify whether focus containment is intentional or prevents progression",
                        element_id=eid
                    )
                ],
                observation=f"Control '{ename}' is part of a repeated keyboard focus loop.",
                impact="Forces redundant keystrokes and can prevent users from reaching content outside the loop.",
                recommendation="Verify whether the circular focus sequence is intentional or if focus should advance to subsequent controls.",
                remediation_code="// Ensure container tab navigation continues:\nKeyboardNavigation.SetTabNavigation(container, KeyboardNavigationMode.Continue);",
                human_verification_required=True,
                element_name=ename,
                element_type=getattr(element, "control_type", "Control"),
                element_bounds=getattr(element, "bounds", None),
                signal_type=SignalType.DETECTED
            )]
        return []


class FocusOrderRule(BaseRule):
    """Rule 12: Detects focus sequence order that differs significantly from spatial layout."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_12_FOCUS_ORDER",
            name="Focus Sequence / Spatial Order Observation"
        )

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        has_discrepancy = getattr(element, "focus_spatial_discrepancy", False)
        if has_discrepancy:
            eid = getattr(element, "element_id", None) or getattr(element, "id", "elem_order")
            ename = getattr(element, "name", "") or "<Unnamed>"
            return [AccessibilityFinding(
                finding_id=f"kb_order_{eid}",
                title="Focus Sequence Differs From Simple Spatial Ordering",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.INFO,
                confidence=0.75,
                affected_element_id=eid,
                source="Spatial vs Tab Order Analyzer",
                evidence=[
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=f"Focus transition to '{ename}' jumps unexpectedly relative to visual top-to-bottom reading order",
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.INFERRED,
                        description="Visual reading layout diverges from logical tab traversal sequence",
                        element_id=eid
                    )
                ],
                observation=f"Focus progression to '{ename}' diverges from natural top-to-bottom spatial order.",
                impact="Visual discrepancy between expected reading order and tab order can disorient keyboard users.",
                recommendation="Confirm whether this custom tab navigation order reflects the intended logical reading sequence.",
                remediation_code="// Align TabIndex with visual reading hierarchy:\ncontrol.TabIndex = logicalOrderIndex;",
                human_verification_required=True,
                element_name=ename,
                element_type=getattr(element, "control_type", "Control"),
                element_bounds=getattr(element, "bounds", None),
                signal_type=SignalType.INFERRED
            )]
        return []


class FocusStateRule(BaseRule):
    """Rule 13: Detects focus state uncertainty where focused element cannot be reliably resolved."""

    def __init__(self):
        super().__init__(
            rule_id="RULE_13_FOCUS_STATE",
            name="Focus State Observation"
        )

    def evaluate(
        self,
        element: Any,
        tree: Optional[UITree] = None,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        is_uncertain = getattr(element, "focus_state_uncertain", False)
        if is_uncertain:
            eid = getattr(element, "element_id", None) or getattr(element, "id", "elem_fstate")
            ename = getattr(element, "name", "") or "<Unnamed>"
            return [AccessibilityFinding(
                finding_id=f"kb_fstate_{eid}",
                title="Focus State Uncertainty on Traversal Transition",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.LOW,
                confidence=0.70,
                affected_element_id=eid,
                source="Focus State Verification",
                evidence=[
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=f"Focus transition occurred but active control state for '{ename}' could not be reliably verified",
                        element_id=eid
                    ),
                    evidence_engine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.RECOMMENDED,
                        description="Test with Windows Narrator and verify visual focus rectangle presence",
                        element_id=eid
                    )
                ],
                observation=f"Active focus state for '{ename}' could not be reliably verified via UI Automation.",
                impact="Assistive technologies may fail to announce control state if focus events are not raised correctly.",
                recommendation="Ensure custom controls correctly raise UI Automation focus events and display visible focus indicators.",
                remediation_code="// Ensure automation peer raises focus change event:\nUIElement.RaiseAutomationEvent(AutomationEvents.AutomationFocusChanged);",
                human_verification_required=True,
                element_name=ename,
                element_type=getattr(element, "control_type", "Control"),
                element_bounds=getattr(element, "bounds", None),
                signal_type=SignalType.DETECTED
            )]
        return []


class AccessibilityRuleEngine:
    """Master deterministic accessibility rule coordinator."""

    def __init__(self):
        self.rules: List[BaseRule] = [
            MissingAccessibleNameRule(),
            NameMismatchRule(),
            SemanticMismatchRule(),
            FocusabilityRule(),
            InteractiveSizeRule(),
            LabelRule(),
            ContrastRule(),
            FocusTrapRule(),
            UnreachedInteractiveElementRule(),
            FocusLoopRule(),
            FocusOrderRule(),
            FocusStateRule(),
        ]
        self.min_target_dimension = 24
        self.min_contrast_aa = 4.5

    def register_rule(self, rule: BaseRule):
        self.rules.append(rule)

    def get_rule(self, rule_id: str) -> Optional[BaseRule]:
        for r in self.rules:
            if r.rule_id == rule_id or r.name.lower() == rule_id.lower():
                return r
        return None

    def enable_rule(self, rule_id: str):
        r = self.get_rule(rule_id)
        if r:
            r.enabled = True

    def disable_rule(self, rule_id: str):
        r = self.get_rule(rule_id)
        if r:
            r.enabled = False

    def evaluate_element(
        self,
        elem: Any,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        """Evaluates enabled rules on a single element."""
        findings: List[AccessibilityFinding] = []
        for r in self.rules:
            if r.enabled:
                findings.extend(r.evaluate(elem, screenshot=screenshot))
        return findings

    def evaluate_tree(
        self,
        tree: UITree,
        screenshot: Optional[Image.Image] = None
    ) -> List[AccessibilityFinding]:
        """Evaluates all elements in a tree and calibrates signals."""
        all_findings: List[AccessibilityFinding] = []

        for elem in tree.elements:
            elem_findings = self.evaluate_element(elem, screenshot)
            # Signal calibration through EvidenceEngine
            calibrated = evidence_engine.fuse_signals(elem, elem_findings)
            elem.findings = calibrated
            all_findings.extend(calibrated)

        return all_findings

    def analyze(self, snapshot: Any) -> List[AccessibilityFinding]:
        """Analyzes an InterfaceSnapshot deterministically."""
        tree = getattr(snapshot, "ui_tree", None)
        if tree is None and hasattr(snapshot, "elements"):
            tree = UITree(snapshot.elements)

        screenshot = None
        sp = getattr(snapshot, "screenshot_path", None)
        if sp:
            try:
                screenshot = Image.open(sp)
            except Exception:
                screenshot = None

        if tree:
            findings = self.evaluate_tree(tree, screenshot)
            snapshot.findings = findings
            snapshot.deterministic_findings = findings
            return findings
        return []


# Singleton instance
rule_engine = AccessibilityRuleEngine()

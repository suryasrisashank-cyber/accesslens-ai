"""Keyboard Navigation & Interactive Focus Traversal Auditor for AccessLens AI (Phase 5).

Discovers focusable interactive controls, executes controlled Tab / Shift+Tab traversal,
records focus transitions, detects focus loops and potential focus traps, identifies
unreached interactive elements, analyzes focus order vs spatial layout, and outputs
grounded, deterministic accessibility findings.
"""

from datetime import datetime, timezone
import json
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from accessibility.element_model import UIElementModel
from accessibility.focus_models import FocusObservation, FocusTraversalResult
from accessibility.focus_path import FocusPath
from accessibility.findings import (
    AccessibilityFinding, FindingCategory, FindingSeverity, SignalType
)
from accessibility.keyboard_driver import (
    KeyboardDriver, MockKeyboardDriver, WindowsKeyboardDriver
)
from accessibility.ui_automation import ui_automation
from accessibility.ui_tree import UITree


class KeyboardAuditor:
    """Coordinates controlled, safety-first keyboard navigation audits."""

    DEFAULT_MAX_STEPS = 100
    DEFAULT_MAX_DURATION_SEC = 30.0
    DEFAULT_STEP_DELAY_MS = 150
    DEFAULT_REPEAT_THRESHOLD = 3

    def __init__(self, driver: Optional[KeyboardDriver] = None):
        self.driver: KeyboardDriver = driver or (
            WindowsKeyboardDriver() if WindowsKeyboardDriver().is_available() else MockKeyboardDriver()
        )
        self._is_cancelled: bool = False
        self._history: List[FocusObservation] = []

    def cancel(self):
        """Signals active audit traversal to stop immediately."""
        self._is_cancelled = True
        if self.driver:
            self.driver.stop()

    def discover_focusable_elements(self, tree: UITree) -> List[UIElementModel]:
        """Discovers candidate focusable interactive elements from the accessibility tree."""
        focusable: List[UIElementModel] = []
        for el in tree.elements:
            if el.is_focusable or el.control_type in [
                "Button", "Edit", "CheckBox", "RadioButton", "ComboBox",
                "Hyperlink", "MenuItem", "TabItem", "Slider"
            ]:
                focusable.append(el)
        return focusable

    def run_traversal(
        self,
        target_hwnd: Optional[int],
        target_window_title: str = "Target Application",
        direction: str = "forward",  # "forward" (Tab) or "reverse" (Shift+Tab)
        max_steps: int = DEFAULT_MAX_STEPS,
        delay_ms: int = DEFAULT_STEP_DELAY_MS,
        max_duration_sec: float = DEFAULT_MAX_DURATION_SEC,
        tree: Optional[UITree] = None,
        on_step_callback: Optional[Callable[[FocusObservation], None]] = None,
    ) -> FocusTraversalResult:
        """Executes a controlled keyboard focus traversal on the target application."""
        self._is_cancelled = False
        self._history.clear()

        started_at = datetime.now(timezone.utc).isoformat()
        start_time = time.time()
        warnings: List[str] = []
        observations: List[FocusObservation] = []

        # 1. Target Window Validation
        if target_hwnd is not None:
            if target_hwnd <= 0 or not self.driver.is_window_valid(target_hwnd):
                return FocusTraversalResult(
                    target_window=target_window_title,
                    target_hwnd=target_hwnd,
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    direction=direction,
                    observations=[],
                    traversal_complete=False,
                    warnings=["Target application is no longer available. Keyboard audit cancelled."],
                    human_verification_required=True,
                )

            # Bring target window to foreground safely
            focused = self.driver.focus_target_window(target_hwnd)
            if not focused:
                warnings.append("Could not confirm foreground focus on target window handle.")

        # 2. Initial Focus Snapshot
        initial_obs = self._capture_focus_snapshot(
            traversal_index=0,
            direction=direction,
            target_hwnd=target_hwnd,
            tree=tree
        )
        if initial_obs:
            observations.append(initial_obs)
            self._history.append(initial_obs)
            if on_step_callback:
                on_step_callback(initial_obs)

        # 3. Controlled Step Loop
        repeated_state_count = 0
        seen_element_keys: List[str] = []
        if initial_obs:
            seen_element_keys.append(self._get_element_key(initial_obs))

        for step in range(1, max_steps + 1):
            if self._is_cancelled:
                warnings.append("Keyboard audit was cancelled by user.")
                break

            if time.time() - start_time > max_duration_sec:
                warnings.append(f"Keyboard audit reached maximum elapsed time limit ({max_duration_sec}s).")
                break

            # Target window loss & focus escape check
            if target_hwnd is not None and target_hwnd > 0:
                if not self.driver.is_window_valid(target_hwnd):
                    warnings.append("Target application window was closed or lost. Keyboard audit aborted.")
                    break

                current_fg = self.driver.get_foreground_window()
                if current_fg is not None and current_fg != target_hwnd:
                    warnings.append("Keyboard audit stopped because focus moved outside the selected target.")
                    break

            # Send single controlled keystroke
            if direction == "reverse":
                success = self.driver.press_shift_tab()
            else:
                success = self.driver.press_tab()

            if not success:
                warnings.append(f"Keyboard driver failed to send keystroke at step {step}.")
                break

            # Wait configurable step interval
            time.sleep(max(delay_ms, 20) / 1000.0)

            # Capture observed focus
            obs = self._capture_focus_snapshot(
                traversal_index=step,
                direction=direction,
                target_hwnd=target_hwnd,
                tree=tree
            )
            if not obs:
                # Focus changed but element could not be reliably identified
                obs = FocusObservation(
                    observation_id=f"focus_step_{step}",
                    element_id=None,
                    element_name="<Unidentified Control>",
                    control_type="Unknown",
                    traversal_index=step,
                    direction=direction,
                    is_focused=False,
                    confidence=0.50,
                    notes="Focus changed but focused element could not be reliably identified."
                )

            observations.append(obs)
            self._history.append(obs)
            if on_step_callback:
                on_step_callback(obs)

            # Cycle & repeated focus evaluation
            current_key = self._get_element_key(obs)
            seen_element_keys.append(current_key)

            # Check consecutive identical focus (bounce)
            if len(seen_element_keys) >= 2 and seen_element_keys[-1] == seen_element_keys[-2]:
                repeated_state_count += 1
                if repeated_state_count >= self.DEFAULT_REPEAT_THRESHOLD:
                    warnings.append(f"Focus remained on '{obs.element_name}' for {repeated_state_count} consecutive steps.")
                    break
            else:
                repeated_state_count = 0

            # Check full cycle repetition threshold
            if self._is_cycle_repeating(seen_element_keys, min_cycle_len=2, max_reps=self.DEFAULT_REPEAT_THRESHOLD):
                warnings.append(f"Detected repeated focus sequence cycling {self.DEFAULT_REPEAT_THRESHOLD} times; terminating traversal.")
                break

        self.driver.stop()
        finished_at = datetime.now(timezone.utc).isoformat()

        # 4. Analyze Observed Traversal Sequence
        analysis = self.analyze_traversal(observations, tree=tree, target_window=target_window_title)

        result = FocusTraversalResult(
            target_window=target_window_title,
            target_hwnd=target_hwnd,
            started_at=started_at,
            finished_at=finished_at,
            direction=direction,
            observations=observations,
            unique_elements=analysis["unique_count"],
            repeated_elements=analysis["repeated_count"],
            traversal_complete=not bool(self._is_cancelled),
            loop_detected=analysis["loop_detected"],
            focus_trap_detected=analysis["focus_trap_detected"],
            unreachable_elements=analysis["unreachable_elements"],
            warnings=warnings,
            findings=analysis["findings"],
            human_verification_required=True,
        )
        return result

    def _capture_focus_snapshot(
        self,
        traversal_index: int,
        direction: str,
        target_hwnd: Optional[int],
        tree: Optional[UITree] = None
    ) -> Optional[FocusObservation]:
        """Captures the currently focused UI element via UI Automation or tree simulation."""
        # Check if driver is MockKeyboardDriver with pre-scripted focus
        if isinstance(self.driver, MockKeyboardDriver):
            # In mock driver, simulate stepping through focusable elements from tree if available
            if tree and tree.elements:
                focusable = [e for e in tree.elements if e.is_focusable or e.control_type in ["Button", "Edit", "CheckBox"]]
                if focusable:
                    idx = traversal_index % len(focusable)
                    el = focusable[idx]
                    return FocusObservation(
                        observation_id=f"focus_step_{traversal_index}",
                        element_id=el.element_id or el.id,
                        element_name=el.name or "<Unnamed>",
                        control_type=el.control_type or "Control",
                        automation_id=el.automation_id or "",
                        class_name=el.class_name or "",
                        bounds=el.bounds,
                        traversal_index=traversal_index,
                        direction=direction,
                        source="Mock UI Automation",
                        confidence=0.95,
                        is_focused=True,
                        is_enabled=el.is_enabled,
                        is_visible=el.is_visible,
                        hwnd=target_hwnd,
                    )

        # Real Windows UI Automation query
        if ui_automation.is_windows():
            ps_script = """
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
try {
    $f = [System.Windows.Automation.AutomationElement]::FocusedElement
    if ($f) {
        $r = $f.Current.BoundingRectangle
        @{
            name = $f.Current.Name
            control_type = $f.Current.ControlType.ProgrammaticName.Replace('ControlType.', '')
            automation_id = $f.Current.AutomationId
            class_name = $f.Current.ClassName
            is_enabled = $f.Current.IsEnabled
            is_focusable = $f.Current.IsKeyboardFocusable
            is_focused = $f.Current.HasKeyboardFocus
            bounds = @([int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height)
        } | ConvertTo-Json -Compress
    }
} catch { }
"""
            raw = ui_automation._run_powershell(ps_script)
            if raw:
                try:
                    data = json.loads(raw)
                    return FocusObservation(
                        observation_id=f"focus_step_{traversal_index}",
                        element_id=f"obs_elem_{traversal_index}",
                        element_name=data.get("name") or "<Unnamed>",
                        control_type=data.get("control_type") or "Control",
                        automation_id=data.get("automation_id") or "",
                        class_name=data.get("class_name") or "",
                        bounds=data.get("bounds"),
                        traversal_index=traversal_index,
                        direction=direction,
                        source="Windows UI Automation",
                        confidence=0.92,
                        is_focused=data.get("is_focused", True),
                        is_enabled=data.get("is_enabled", True),
                        is_visible=True,
                        hwnd=target_hwnd,
                    )
                except Exception:
                    pass

        return None

    def analyze_traversal(
        self,
        observations: List[FocusObservation],
        tree: Optional[UITree] = None,
        target_window: str = "Window",
    ) -> Dict[str, Any]:
        """Analyzes a sequence of focus observations to produce findings and metrics."""
        findings: List[AccessibilityFinding] = []
        unreachable: List[Dict[str, Any]] = []

        if not observations:
            return {
                "unique_count": 0,
                "repeated_count": 0,
                "loop_detected": False,
                "focus_trap_detected": False,
                "unreachable_elements": [],
                "findings": [],
            }

        # 1. Unique vs Repeated Elements
        keys = [self._get_element_key(obs) for obs in observations]
        unique_keys = set(keys)
        unique_count = len(unique_keys)
        repeated_count = len(keys) - unique_count

        # 2. Focus Loop Detection ($A \to B \to C \to A$ or $A \to B \to A$)
        loop_detected, loop_pattern = self.detect_focus_loop(keys)
        if loop_detected:
            loop_str = " -> ".join(loop_pattern)
            findings.append(AccessibilityFinding(
                finding_id=f"kb_loop_{abs(hash(loop_str)) % 10000}",
                title="Unexpected Keyboard Focus Loop Observed",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.MEDIUM,
                confidence=0.85,
                source="Keyboard Focus Traversal Monitor",
                evidence=[
                    f"[DETECTED] Focus sequence repeated cyclical pattern: {loop_str}",
                    "[INFERRED] Navigation cycles through the same controls rather than progressing linearly",
                    "[RECOMMENDED] Verify whether focus containment is intentional (such as in a dialog) or prevents progression."
                ],
                observation=f"Keyboard navigation cycled through repeated sequence: {loop_str}.",
                impact="Users navigating by keyboard may experience redundant keystroke overhead or difficulty reaching subsequent controls.",
                recommendation="Ensure container controls release keyboard focus when the last child control is tabbed past.",
                remediation_code="// Set standard container tab continuation:\nKeyboardNavigation.SetTabNavigation(container, KeyboardNavigationMode.Continue);",
                human_verification_required=True,
                signal_type=SignalType.DETECTED
            ))

        # 3. Focus Trap Detection ($A \to B \to C \to B \to C \to B \to C$)
        trap_detected, trap_pattern = self.detect_focus_trap(keys)
        if trap_detected:
            trap_str = " -> ".join(trap_pattern)
            findings.append(AccessibilityFinding(
                finding_id=f"kb_trap_{abs(hash(trap_str)) % 10000}",
                title="Potential Keyboard Focus Trap Detected",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.MEDIUM,
                confidence=0.85,
                source="Keyboard Focus Traversal Monitor",
                evidence=[
                    f"[DETECTED] Focus entered sub-cycle ({trap_str}) and failed to escape to prior or following targets",
                    "[INFERRED] Focus appears confined to a sub-region without standard Tab progression",
                    "[RECOMMENDED] Verify whether keyboard focus can intentionally enter and exit this region."
                ],
                observation=f"Focus appeared trapped within a subset of controls: {trap_str}.",
                impact="Keyboard-only users may become stuck inside this control region without ability to navigate away.",
                recommendation="Verify whether keyboard focus can intentionally enter and exit this region. Provide standard escape or continuation.",
                remediation_code="// Ensure focus escapes modal on Tab:\nKeyboardNavigation.SetTabNavigation(modalRegion, KeyboardNavigationMode.Cycle);",
                human_verification_required=True,
                signal_type=SignalType.DETECTED
            ))

        # 4. Unreached Interactive Elements
        if tree is not None:
            interactive = self.discover_focusable_elements(tree)
            observed_names = {obs.element_name.strip().lower() for obs in observations if obs.element_name}
            observed_aids = {obs.automation_id.strip() for obs in observations if obs.automation_id}
            observed_eids = {obs.element_id for obs in observations if obs.element_id}

            for el in interactive:
                ename = (el.name or "").strip().lower()
                eaid = (el.automation_id or "").strip()
                eeid = el.element_id or el.id

                # Match against observed sets
                name_matched = bool(ename and ename in observed_names)
                aid_matched = bool(eaid and eaid in observed_aids)
                eid_matched = bool(eeid and eeid in observed_eids)

                if not (name_matched or aid_matched or eid_matched):
                    unreachable.append({
                        "element_id": eeid,
                        "name": el.name or "<Unnamed>",
                        "control_type": el.control_type or "Control",
                        "bounds": el.bounds,
                    })

            if unreachable and len(observations) >= 3:
                first_unreached = unreachable[0]
                findings.append(AccessibilityFinding(
                    finding_id="kb_unreached_elements",
                    title="Interactive Element Not Observed During Traversal",
                    category=FindingCategory.KEYBOARD,
                    severity=FindingSeverity.LOW,
                    confidence=0.80,
                    source="Keyboard Traversal Coverage Analysis",
                    evidence=[
                        f"[MEASURED] {len(unreachable)} interactive elements in the accessibility tree were not observed in the tested traversal sequence",
                        f"[DETECTED] Element '{first_unreached['name']}' ({first_unreached['control_type']}) was not observed during this traversal",
                        "[INFERRED] Element may be excluded from the primary tab order, conditionally visible, or rely on composite/arrow navigation",
                        "[RECOMMENDED] Verify whether this control should be included in the primary keyboard tab sequence."
                    ],
                    observation=f"{len(unreachable)} interactive controls were not observed in the tested traversal sequence.",
                    impact="Keyboard users navigating by Tab might be unable to reach controls not included in the primary tab order.",
                    recommendation="Verify whether these controls should be reachable via sequential keyboard Tab navigation or if exclusion is intentional.",
                    remediation_code="// Ensure element is included in tab sequence:\ncontrol.IsTabStop = true;\ncontrol.TabIndex = nextTabIndex;",
                    human_verification_required=True,
                    signal_type=SignalType.DETECTED
                ))

        # 5. Focus Sequence vs Spatial Ordering Analysis
        spatial_discrepancy, desc = self.analyze_spatial_ordering(observations)
        if spatial_discrepancy:
            findings.append(AccessibilityFinding(
                finding_id="kb_order_discrepancy",
                title="Focus Sequence Differs From Simple Spatial Ordering",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.INFO,
                confidence=0.75,
                source="Spatial vs Tab Order Analyzer",
                evidence=[
                    f"[DETECTED] {desc}",
                    "[INFERRED] Logical tab order diverges from top-to-bottom, left-to-right visual order",
                    "[RECOMMENDED] Verify that the navigation order reflects a logical reading sequence for users."
                ],
                observation="Focus sequence differs from simple top-to-bottom, left-to-right spatial ordering.",
                impact="Discrepancies between visual layout and keyboard focus progression can confuse keyboard users.",
                recommendation="Confirm whether the current tab navigation order reflects the intended logical reading order.",
                remediation_code="// Adjust TabIndex to match logical reading sequence:\ncontrol.TabIndex = logicalIndex;",
                human_verification_required=True,
                signal_type=SignalType.INFERRED
            ))

        # 6. Focus State Verification
        uncertain_obs = [obs for obs in observations if not obs.is_focused or obs.confidence < 0.6]
        if uncertain_obs:
            findings.append(AccessibilityFinding(
                finding_id="kb_focus_state_uncertain",
                title="Focus State Uncertainty on Traversal Transition",
                category=FindingCategory.KEYBOARD,
                severity=FindingSeverity.LOW,
                confidence=0.70,
                source="Focus State Verification",
                evidence=[
                    f"[DETECTED] {len(uncertain_obs)} focus transitions occurred where the active control could not be reliably identified",
                    "[RECOMMENDED] Verify that custom controls implement standard focus visual indicators and UI Automation peers."
                ],
                observation="Focus transition occurred but focused element could not be reliably identified by UI Automation.",
                impact="Assistive technologies may fail to announce control state if focus events are not correctly raised.",
                recommendation="Ensure custom controls raise standard UIA AutomationFocusChanged events.",
                remediation_code="// Raise automation focus event in custom control:\nAutomationProperties.SetAutomationId(this, \"customId\");",
                human_verification_required=True,
                signal_type=SignalType.DETECTED
            ))

        return {
            "unique_count": unique_count,
            "repeated_count": repeated_count,
            "loop_detected": loop_detected,
            "focus_trap_detected": trap_detected,
            "unreachable_elements": unreachable,
            "findings": findings,
        }

    def detect_focus_loop(self, keys: List[str]) -> Tuple[bool, List[str]]:
        """Detects repeated cyclical patterns like A -> B -> C -> A -> B -> C or A -> B -> A -> B."""
        if len(keys) < 4:
            return False, []

        # Check cycle lengths from 2 to 6
        for cycle_len in range(2, min(7, len(keys) // 2 + 1)):
            for start in range(len(keys) - 2 * cycle_len + 1):
                c1 = keys[start : start + cycle_len]
                c2 = keys[start + cycle_len : start + 2 * cycle_len]
                if c1 == c2 and len(set(c1)) > 1:
                    return True, c1

        return False, []

    def detect_focus_trap(self, keys: List[str]) -> Tuple[bool, List[str]]:
        """Detects entrapment where focus enters a sub-cycle and cannot escape (e.g. A -> B -> C -> B -> C -> B -> C)."""
        if len(keys) < 5:
            return False, []

        # Focus entered from some prefix, then repeated the same sub-cycle at the tail at least 2 times
        for cycle_len in range(2, 5):
            if len(keys) >= 1 + 2 * cycle_len:
                tail1 = keys[-cycle_len:]
                tail2 = keys[-2 * cycle_len : -cycle_len]
                prefix = keys[:-2 * cycle_len]
                if tail1 == tail2 and len(set(tail1)) > 1:
                    # If prefix contains elements not in tail, focus entered but cannot escape
                    if any(p not in tail1 for p in prefix):
                        return True, tail1

        return False, []

    def analyze_spatial_ordering(self, observations: List[FocusObservation]) -> Tuple[bool, str]:
        """Checks if focus transitions jump erratically across screen space compared to visual order."""
        valid_bounds_obs = [obs for obs in observations if obs.bounds and len(obs.bounds) == 4 and (obs.bounds[2] > 0 or obs.bounds[3] > 0)]
        if len(valid_bounds_obs) < 3:
            return False, ""

        jumps = 0
        for i in range(1, len(valid_bounds_obs)):
            prev_b = valid_bounds_obs[i - 1].bounds
            curr_b = valid_bounds_obs[i].bounds
            # Significant backward vertical jump (e.g. jump upwards by more than 150px)
            if curr_b[1] < prev_b[1] - 150:
                jumps += 1

        if jumps >= 2:
            return True, f"Detected {jumps} significant backward vertical focus jumps during traversal."
        return False, ""

    def _is_cycle_repeating(self, keys: List[str], min_cycle_len: int = 2, max_reps: int = 3) -> bool:
        """Helper checking if the tail of keys represents a repeated cycle."""
        for c_len in range(min_cycle_len, min(6, len(keys) // max_reps + 1)):
            sub = keys[-c_len:]
            is_match = True
            for rep in range(1, max_reps):
                start = -(rep + 1) * c_len
                end = -rep * c_len
                if keys[start:end] != sub:
                    is_match = False
                    break
            if is_match and len(set(sub)) > 1:
                return True
        return False

    def _get_element_key(self, obs: FocusObservation) -> str:
        """Returns stable element identity key for cycle detection."""
        return obs.automation_id or obs.element_name or obs.element_id or f"elem_{obs.traversal_index}"


# Singleton instance
keyboard_auditor = KeyboardAuditor()

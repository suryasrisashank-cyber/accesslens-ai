"""Asynchronous Keyboard Audit Worker for AccessLens AI (Phase 5).

Executes controlled keyboard traversal in a dedicated QThread off the main UI loop,
emitting live step events, progress updates, cancellation signals, and completion results.
"""

from typing import Optional

from PySide6.QtCore import QThread, Signal

from accessibility.focus_models import FocusObservation, FocusTraversalResult
from accessibility.focus_path import FocusPath
from accessibility.keyboard_auditor import KeyboardAuditor, keyboard_auditor
from accessibility.keyboard_driver import KeyboardDriver
from accessibility.ui_tree import UITree


class KeyboardAuditWorker(QThread):
    """Background worker for non-blocking keyboard navigation audits."""

    started_audit = Signal()
    observation_recorded = Signal(object)  # FocusObservation
    progress = Signal(int, int)            # (current_step, max_steps)
    audit_finished = Signal(object, object)  # (FocusTraversalResult, FocusPath)
    cancelled = Signal(str)                # reason
    error = Signal(str)                    # error message

    def __init__(
        self,
        target_hwnd: Optional[int],
        target_window_title: str = "Target Application",
        direction: str = "forward",
        max_steps: int = 100,
        delay_ms: int = 150,
        tree: Optional[UITree] = None,
        driver: Optional[KeyboardDriver] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.target_hwnd = target_hwnd
        self.target_window_title = target_window_title
        self.direction = direction
        self.max_steps = max_steps
        self.delay_ms = delay_ms
        self.tree = tree
        self.auditor = KeyboardAuditor(driver=driver) if driver else keyboard_auditor

    def cancel(self):
        """Signals worker to abort traversal immediately."""
        self.auditor.cancel()

    def run(self):
        """Executes traversal loop and emits live progress signals."""
        try:
            self.started_audit.emit()

            def on_step(obs: FocusObservation):
                self.observation_recorded.emit(obs)
                self.progress.emit(obs.traversal_index, self.max_steps)

            result = self.auditor.run_traversal(
                target_hwnd=self.target_hwnd,
                target_window_title=self.target_window_title,
                direction=self.direction,
                max_steps=self.max_steps,
                delay_ms=self.delay_ms,
                tree=self.tree,
                on_step_callback=on_step,
            )

            # Build FocusPath
            focus_path = FocusPath.build_from_observations(result.observations)
            focus_path.has_trap = result.focus_trap_detected

            if not result.traversal_complete:
                reason = result.warnings[0] if result.warnings else "Audit cancelled."
                self.cancelled.emit(reason)

            self.audit_finished.emit(result, focus_path)
        except Exception as e:
            self.error.emit(str(e))

"""Asynchronous worker for local AI reasoning and developer remediation.

Executes local reasoning queries on a background QThread to ensure the PySide6 UI
remains responsive, fluid, and non-blocking.
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, Signal

from accessibility.element_model import UIElementModel
from accessibility.evidence_engine import EvidenceItem
from accessibility.findings import AccessibilityFinding
from ai.finding_context import finding_context_builder
from ai.local_model_provider import local_model_provider
from ai.reasoning_models import ReasoningResult


class ReasoningWorker(QThread):
    """Background worker executing local reasoning and developer remediation."""

    finished = Signal(object)  # Emits ReasoningResult
    error = Signal(str)

    def __init__(
        self,
        finding: AccessibilityFinding,
        element: Optional[UIElementModel] = None,
        evidence: Optional[List[EvidenceItem]] = None,
        mode: str = "reasoning",  # "reasoning" or "remediation"
    ):
        super().__init__()
        self.finding = finding
        self.element = element
        self.evidence = evidence
        self.mode = mode

    def run(self):
        try:
            # 1. Build sanitized reasoning context with injection defenses
            context = finding_context_builder.build_context(
                finding=self.finding,
                element=self.element,
                evidence_items=self.evidence,
            )

            # 2. Invoke local model provider
            if self.mode == "remediation":
                result: ReasoningResult = local_model_provider.generate_remediation(context)
            else:
                result = local_model_provider.generate_reasoning(context)

            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(f"Reasoning could not be completed: {str(exc)}")

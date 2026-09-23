"""Background QThread worker for non-blocking multimodal accessibility auditing."""

from typing import Optional, Union
import numpy as np
from PIL import Image

from PySide6.QtCore import QObject, QThread, Signal

from accessibility.audit_coordinator import audit_coordinator
from accessibility.element_model import InterfaceSnapshot
from vision.image_analyzer import ImageAnalysisResult, image_analyzer
from vision.ocr_engine import ocr_engine


class AnalysisWorker(QThread):
    """Executes OCR, UI Automation correlation, and accessibility rules asynchronously."""

    analysis_started = Signal()
    analysis_progress = Signal(str)
    analysis_finished = Signal(object, object)  # Emits (ImageAnalysisResult, InterfaceSnapshot)
    analysis_error = Signal(str)

    def __init__(
        self,
        image_source: Union[str, Image.Image, np.ndarray],
        window_handle: Optional[int] = None,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.image_source = image_source
        self.window_handle = window_handle
        self._is_cancelled = False

    def cancel(self):
        """Cooperatively requests worker cancellation."""
        self._is_cancelled = True

    def run(self):
        try:
            if self._is_cancelled:
                return

            self.analysis_started.emit()
            self.analysis_progress.emit("Extracting on-device ONNX OCR text and visual elements...")

            # Run OCR and base visual understanding (VisionVoice capability preserved)
            ocr_result = ocr_engine.extract_text(self.image_source)
            if self._is_cancelled:
                return

            self.analysis_progress.emit("Synthesizing scene description and accessibility signals...")
            scene_result = image_analyzer.analyze_image(self.image_source, ocr_result=ocr_result)
            if self._is_cancelled:
                return

            # Run full AccessLens deterministic accessibility audit
            self.analysis_progress.emit("Evaluating WCAG rules, contrast, and UI Automation tree...")
            snapshot = audit_coordinator.audit_interface(
                self.image_source,
                window_handle=self.window_handle
            )
            if self._is_cancelled:
                return

            self.analysis_finished.emit(scene_result, snapshot)

        except Exception as e:
            if not self._is_cancelled:
                self.analysis_error.emit(str(e))

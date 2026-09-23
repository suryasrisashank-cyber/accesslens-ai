"""Asynchronous Evidence Fusion Worker for AccessLens AI (Phase 6).

Executes target window screenshot capture, on-device OCR, geometric normalization,
and deterministic UIA-to-visual evidence fusion in a background QThread to ensure
the PySide6 user interface never freezes.
"""

import time
from typing import Any, Dict, List, Optional
from PIL import Image

from PySide6.QtCore import QThread, Signal

from accessibility.element_model import UIElementModel
from accessibility.evidence_fusion import EvidenceFusionResult, evidence_fusion_engine
from accessibility.focus_models import FocusObservation
from accessibility.visual_models import VisualEvidence
from ai.prompt_guard import PromptGuard
from vision.ocr_engine import ocr_engine
from vision.screen_capture import screen_capturer


class EvidenceFusionWorker(QThread):
    """Background worker for multimodal screenshot + UIA evidence fusion."""

    progress = Signal(int, str)  # (percentage, status_text)
    finished = Signal(object, object)  # (EvidenceFusionResult, Optional[Image.Image])
    error = Signal(str)

    def __init__(
        self,
        window_handle: Optional[int],
        window_title: str,
        uia_elements: List[UIElementModel],
        window_bounds: Optional[List[int]] = None,
        keyboard_observations: Optional[List[FocusObservation]] = None,
        existing_screenshot: Optional[Image.Image] = None,
    ):
        super().__init__()
        self.window_handle = window_handle
        self.window_title = window_title
        self.uia_elements = uia_elements
        self.window_bounds = window_bounds
        self.keyboard_observations = keyboard_observations or []
        self.existing_screenshot = existing_screenshot
        self._is_cancelled = False

    def cancel(self):
        """Cooperatively requests worker cancellation."""
        self._is_cancelled = True

    def run(self):
        try:
            if self._is_cancelled:
                return

            self.progress.emit(10, "Capturing target application screenshot...")

            screenshot = self.existing_screenshot
            screenshot_meta = {
                "width": 1280,
                "height": 720,
                "target_hwnd": self.window_handle,
                "window_bounds": self.window_bounds,
                "status": "Available",
            }

            if screenshot is None:
                if self.window_handle and self.window_handle > 0:
                    screenshot, screenshot_meta = screen_capturer.capture_target_window(self.window_handle)
                if screenshot is None:
                    screenshot = screen_capturer.capture_primary_screen()
                    if screenshot:
                        screenshot_meta = {
                            "width": screenshot.width,
                            "height": screenshot.height,
                            "target_hwnd": self.window_handle,
                            "window_bounds": self.window_bounds,
                            "status": "Primary screen fallback.",
                        }

            sw = screenshot.width if screenshot else 1280
            sh = screenshot.height if screenshot else 720

            self.progress.emit(35, "Running on-device OCR on visual canvas...")
            visual_elements: List[VisualEvidence] = []

            if screenshot is not None:
                try:
                    ocr_res = ocr_engine.extract_text(screenshot)
                    if ocr_res and ocr_res.bounding_boxes:
                        for idx, box_item in enumerate(ocr_res.bounding_boxes):
                            raw_text = str(box_item.get("text", "")).strip()
                            is_susp = PromptGuard.is_suspicious_text(raw_text)

                            vis_ev = VisualEvidence.from_ocr_box(
                                evidence_id=f"vis_ocr_{idx}",
                                box_data=box_item,
                                screenshot_ref=f"hwnd_{self.window_handle}_{int(time.time())}",
                                is_suspicious=is_susp,
                            )
                            visual_elements.append(vis_ev)
                except Exception as ocr_err:
                    # Non-fatal OCR error
                    screenshot_meta["ocr_warning"] = str(ocr_err)

            if self._is_cancelled:
                return

            self.progress.emit(70, "Executing deterministic UIA <-> Visual matching...")

            # Run deterministic evidence fusion
            result: EvidenceFusionResult = evidence_fusion_engine.fuse_evidence(
                target_window_title=self.window_title,
                uia_elements=self.uia_elements,
                visual_elements=visual_elements,
                screenshot_size=(sw, sh),
                window_bounds=self.window_bounds,
                keyboard_observations=self.keyboard_observations,
                screenshot_metadata=screenshot_meta,
            )

            if self._is_cancelled:
                return

            self.progress.emit(100, "Evidence fusion complete.")
            self.finished.emit(result, screenshot)

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(f"Evidence fusion failed: {e}")

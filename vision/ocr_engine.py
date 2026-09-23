"""Local OCR engine for VisionVoice AI.

Provides on-device text detection and recognition using ONNX Runtime via RapidOCR,
with graceful fallback if dependencies are missing or uninitialized.
"""

from dataclasses import dataclass, field
import time
from typing import Any, List, Optional, Union
import numpy as np
from PIL import Image

from vision.image_utils import load_image, pil_to_numpy

# Optional RapidOCR ONNX Runtime integration
try:
    from rapidocr_onnxruntime import RapidOCR
    _RAPID_OCR_AVAILABLE = True
except ImportError:
    RapidOCR = None
    _RAPID_OCR_AVAILABLE = False


@dataclass
class OCRResult:
    """Normalized output from optical character recognition."""
    text: str
    confidence: float
    bounding_boxes: List[dict] = field(default_factory=list)
    processing_time_ms: float = 0.0
    backend_used: str = "RapidOCR (ONNX Runtime)"
    line_count: int = 0
    raw_results: Any = None


class OCREngine:
    """On-device OCR pipeline executing via ONNX Runtime."""

    def __init__(self):
        self._engine = None
        self._backend_name = "RapidOCR (ONNX Runtime)"
        self._initialize_engine()

    def _initialize_engine(self):
        """Initializes RapidOCR instance with local ONNX models."""
        if _RAPID_OCR_AVAILABLE:
            try:
                # RapidOCR loads bundled ONNX models (det, cls, rec)
                self._engine = RapidOCR()
                self._backend_name = "RapidOCR (ONNX Runtime CPU)"
            except Exception as e:
                self._engine = None
                self._backend_name = f"Fallback Engine (Init failed: {e})"
        else:
            self._engine = None
            self._backend_name = "Fallback Engine (RapidOCR not installed)"

    @property
    def backend_name(self) -> str:
        return self._backend_name

    def is_available(self) -> bool:
        return self._engine is not None

    def extract_text(self, image_input: Union[str, Image.Image, np.ndarray]) -> OCRResult:
        """Extracts visible text, confidence scores, and bounding boxes from an image.

        Args:
            image_input: File path, PIL Image, or NumPy array.

        Returns:
            OCRResult object with text, confidence, bounding_boxes.
        """
        start_time = time.perf_counter()

        try:
            pil_img = load_image(image_input)
            img_arr = pil_to_numpy(pil_img)
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return OCRResult(
                text=f"[Error loading image: {e}]",
                confidence=0.0,
                bounding_boxes=[],
                processing_time_ms=elapsed_ms,
                backend_used=self._backend_name
            )

        if self._engine is not None:
            try:
                # RapidOCR returns: (results, elapse_list)
                # results: [[[box_coords], text, score], ...]
                results, _ = self._engine(img_arr)
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if not results:
                    return OCRResult(
                        text="",
                        confidence=1.0,
                        bounding_boxes=[],
                        processing_time_ms=elapsed_ms,
                        backend_used=self._backend_name,
                        line_count=0
                    )

                lines: List[str] = []
                confidences: List[float] = []
                boxes: List[dict] = []

                for item in results:
                    # item: [box_points, text, confidence_str_or_float]
                    box_points = item[0]
                    line_text = str(item[1]).strip()
                    score = float(item[2])

                    if line_text:
                        lines.append(line_text)
                        confidences.append(score)
                        boxes.append({
                            "box": box_points,
                            "text": line_text,
                            "confidence": score
                        })

                full_text = "\n".join(lines)
                avg_confidence = float(np.mean(confidences)) if confidences else 0.0

                return OCRResult(
                    text=full_text,
                    confidence=round(avg_confidence, 3),
                    bounding_boxes=boxes,
                    processing_time_ms=round(elapsed_ms, 2),
                    backend_used=self._backend_name,
                    line_count=len(lines),
                    raw_results=results
                )

            except Exception as e:
                # Graceful fallback on unexpected engine exception
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return OCRResult(
                    text=f"[OCR Processing Warning: {e}. Fallback active.]",
                    confidence=0.0,
                    bounding_boxes=[],
                    processing_time_ms=round(elapsed_ms, 2),
                    backend_used=f"{self._backend_name} (Degraded)"
                )
        else:
            # Fallback stub when RapidOCR is completely absent
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return OCRResult(
                text="[OCR Engine Unavailable: RapidOCR ONNX model not loaded. CPU fallback active.]",
                confidence=0.0,
                bounding_boxes=[],
                processing_time_ms=round(elapsed_ms, 2),
                backend_used=self._backend_name,
                line_count=0
            )


# Global singleton instance
ocr_engine = OCREngine()

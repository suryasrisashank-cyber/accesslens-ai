"""Tests for OCR engine interface and text extraction."""

import numpy as np
from PIL import Image, ImageDraw
import pytest

from vision.ocr_engine import OCREngine, OCRResult, ocr_engine


def test_ocr_result_structure():
    res = OCRResult(
        text="Hello VisionVoice",
        confidence=0.98,
        bounding_boxes=[{"box": [10, 10, 50, 30], "text": "Hello VisionVoice"}],
        processing_time_ms=12.5
    )
    assert res.text == "Hello VisionVoice"
    assert res.confidence == 0.98
    assert len(res.bounding_boxes) == 1
    assert res.processing_time_ms > 0


def test_ocr_extract_text_synthetic():
    img = Image.new("RGB", (300, 80), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((15, 25), "QUALCOMM AI 2026", fill=(0, 0, 0))

    result = ocr_engine.extract_text(img)
    assert isinstance(result, OCRResult)
    assert isinstance(result.text, str)
    assert 0.0 <= result.confidence <= 1.0
    assert result.processing_time_ms > 0

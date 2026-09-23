"""Tests for multimodal image analyzer and summarization pipeline."""

from PIL import Image, ImageDraw
import pytest

from vision.image_analyzer import ImageAnalysisResult, ImageAnalyzer, image_analyzer
from vision.ocr_engine import OCRResult


def test_analyzer_interface_structure():
    mock_ocr = OCRResult(
        text="Application deadline: September 30\nApply Now button",
        confidence=0.92,
        bounding_boxes=[]
    )
    img = Image.new("RGB", (400, 200), (255, 255, 255))
    res = image_analyzer.analyze_image(img, ocr_result=mock_ocr)

    assert isinstance(res, ImageAnalysisResult)
    assert res.description != ""
    assert isinstance(res.important_objects, list)
    assert isinstance(res.important_text, str)
    assert 0.0 <= res.confidence <= 1.0
    assert res.word_count > 0
    assert len(res.structured_bullets) > 0


def test_category_detection():
    analyzer = ImageAnalyzer()
    cat, _ = analyzer.detect_category("University Undergraduate Admission portal", 800, 600)
    assert "University" in cat

    cat, _ = analyzer.detect_category("Starters Crispy Calamari Salmon Dinner Menu", 800, 600)
    assert "Menu" in cat

    cat, _ = analyzer.detect_category("Nutrition Facts Serving Size Calories Ingredients", 800, 600)
    assert "Label" in cat


def test_signal_extraction():
    analyzer = ImageAnalyzer()
    sample_text = (
        "Admissions Office 2026\n"
        "Application deadline: September 30, 2026\n"
        "Click Apply Now to register\n"
        "Visit: https://portal.edu"
    )
    bullets, objects = analyzer.extract_important_signals(sample_text)
    assert any("Apply Now" in b for b in bullets)
    assert any("September 30" in b for b in bullets)
    assert any("Apply Now" in o for o in objects)

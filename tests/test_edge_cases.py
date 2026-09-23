"""Tests verifying graceful handling of edge cases and invalid inputs."""

import os
import tempfile
import numpy as np
from PIL import Image
import pytest

from vision.image_analyzer import image_analyzer
from vision.ocr_engine import ocr_engine


def test_empty_blank_image():
    # Completely white image with zero text
    blank = Image.new("RGB", (200, 200), color=(255, 255, 255))
    ocr_res = ocr_engine.extract_text(blank)
    assert ocr_res is not None
    assert ocr_res.text == ""

    analysis = image_analyzer.analyze_image(blank, ocr_result=ocr_res)
    assert analysis is not None
    assert analysis.word_count == 0
    assert "No readable text" in analysis.description or "detected" in analysis.description


def test_black_blank_image():
    # Completely black image
    blank = Image.new("RGB", (200, 200), color=(0, 0, 0))
    ocr_res = ocr_engine.extract_text(blank)
    assert ocr_res is not None
    assert ocr_res.text == ""


def test_nonexistent_image_path():
    fake_path = r"C:\non_existent_folder_xyz\fake_image_123.png"
    ocr_res = ocr_engine.extract_text(fake_path)
    # Must not crash, should return error message in text
    assert ocr_res is not None
    assert "Error" in ocr_res.text


def test_corrupted_image_file():
    # Write garbage bytes to a file with .png extension
    fd, path = tempfile.mkstemp(suffix=".png")
    os.write(fd, b"This is not a real PNG image content.")
    os.close(fd)

    try:
        ocr_res = ocr_engine.extract_text(path)
        assert ocr_res is not None
        assert "Error" in ocr_res.text
    finally:
        if os.path.exists(path):
            os.remove(path)

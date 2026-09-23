"""Tests for screen capture utility."""

import os
from PIL import Image
import pytest

from vision.screen_capture import ScreenCapturer, screen_capturer


def test_screen_capture_primary():
    img = screen_capturer.capture_primary_screen()
    assert img is not None
    assert isinstance(img, Image.Image)
    assert img.width > 0
    assert img.height > 0


def test_screen_capture_temp_file():
    temp_path = screen_capturer.capture_to_temp_file()
    assert os.path.exists(temp_path)
    assert os.path.getsize(temp_path) > 0
    # Clean up
    try:
        os.remove(temp_path)
    except Exception:
        pass

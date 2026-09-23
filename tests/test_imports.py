"""Tests verifying all core modules import cleanly without missing dependencies."""

import pytest


def test_core_imports():
    import app.main
    import app.ui.main_window
    import app.ui.components
    import app.ui.hardware_view
    import app.ui.performance_view
    import app.ui.history_view
    import app.workers.analysis_worker

    import ai.base_backend
    import ai.cpu_backend
    import ai.qualcomm_backend
    import ai.model_registry

    import vision.image_utils
    import vision.ocr_engine
    import vision.image_analyzer
    import vision.screen_capture

    import audio.text_to_speech
    import hardware.hardware_detector
    import hardware.compute_backend
    import hardware.backend_status
    import privacy.privacy_manager
    import storage.database

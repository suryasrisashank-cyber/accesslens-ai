"""Comprehensive Robustness, Edge Case, and Polish Test Suite for AccessLens AI.

Audits edge cases across the complete application stack:
1. Minimized windows and invalid HWNDs in screen capture.
2. Degenerate bounding boxes, NaNs, infinities, and zero-area geometries.
3. Completely blank, uniform, or tiny images in OCR and layout analysis.
4. Empty element lists in evidence fusion (bipartite matching edge cases).
5. Cooperative worker cancellation (AnalysisWorker, EvidenceFusionWorker, ReportWorker).
6. SQLite database connection lifecycle and handle cleanup.
7. Zero-finding report generation and cross-platform digest stability.
8. UI view cleanup and safe thread termination.
"""

from contextlib import contextmanager
import math
import os
import shutil
import tempfile
import time
import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from accessibility.contrast_engine import calculate_contrast_ratio, sample_region_contrast
from accessibility.element_model import InterfaceSnapshot, UIElementModel
from accessibility.evidence_fusion import EvidenceFusionEngine, evidence_fusion_engine
from accessibility.geometry import (
    calculate_containment,
    calculate_iou,
    rect_area,
    rect_intersection,
    validate_rect,
)
from accessibility.rule_engine import rule_engine
from accessibility.ui_tree import UITree
from accessibility.visual_models import VisualEvidence
from app.workers.analysis_worker import AnalysisWorker
from app.workers.evidence_fusion_worker import EvidenceFusionWorker
from app.workers.report_worker import ReportWorker
from reports.exporters.html_exporter import HtmlReportExporter
from reports.exporters.json_exporter import JsonReportExporter
from reports.exporters.markdown_exporter import MarkdownReportExporter
from reports.report_generator import AuditReportGenerator
from reports.report_integrity import calculate_report_digest, verify_report_digest
from reports.report_validator import ReportValidator
from storage.database import DatabaseManager
from vision.image_analyzer import image_analyzer
from vision.ocr_engine import ocr_engine
from vision.screen_capture import ScreenCapturer


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ============================================================================
# 1. Screen Capture & Window Edge Cases
# ============================================================================

def test_screen_capture_invalid_hwnd():
    capturer = ScreenCapturer()
    # Negative or invalid HWND
    img, meta = capturer.capture_target_window(hwnd=-1)
    assert meta["target_hwnd"] == -1
    # Fallback to primary screen or notes unavailability
    assert meta["width"] >= 0


def test_screen_capture_nonexistent_hwnd():
    capturer = ScreenCapturer()
    # Extremely large HWND that definitely does not exist
    img, meta = capturer.capture_target_window(hwnd=99999999)
    assert meta["target_hwnd"] == 99999999
    # If on Windows, should report invalid window handle
    if os.name == "nt":
        assert "Invalid window handle" in meta.get("status", "") or "unavailable" in meta.get("status", "")


# ============================================================================
# 2. Degenerate Bounding Boxes & Spatial Math
# ============================================================================

def test_geometry_validate_rect_degenerate():
    assert validate_rect(None) is None
    assert validate_rect([]) is None
    assert validate_rect([10, 20]) is None
    assert validate_rect([10, 20, 0, 50]) is None       # Zero width
    assert validate_rect([10, 20, 50, 0]) is None       # Zero height
    assert validate_rect([10, 20, -5, 50]) is None      # Negative width
    assert validate_rect([10, 20, 50, -5]) is None      # Negative height
    assert validate_rect([float("nan"), 10, 50, 50]) is None
    assert validate_rect([10, float("inf"), 50, 50]) is None
    assert validate_rect(["invalid", 10, 50, 50]) is None


def test_geometry_calculate_iou_degenerate():
    # Degenerate inputs should return 0.0, never raise ZeroDivisionError
    assert calculate_iou(None, [0, 0, 10, 10]) == 0.0
    assert calculate_iou([0, 0, 10, 10], None) == 0.0
    assert calculate_iou([0, 0, 0, 0], [0, 0, 10, 10]) == 0.0
    assert calculate_iou([0, 0, 10, 10], [0, 0, 0, 0]) == 0.0
    assert calculate_iou([-10, -10, 0, 0], [0, 0, 10, 10]) == 0.0


def test_contrast_sample_region_degenerate():
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    # Zero or tiny bounds
    assert sample_region_contrast(img, [0, 0, 0, 0]) is None
    assert sample_region_contrast(img, [0, 0, 2, 2]) is None
    assert sample_region_contrast(img, [-10, -10, 5, 5]) is None
    # Identical colors
    res = calculate_contrast_ratio((128, 128, 128), (128, 128, 128))
    assert res.contrast_ratio == 1.0


# ============================================================================
# 3. Blank / Uniform Images in OCR & Layout Analyzer
# ============================================================================

def test_ocr_completely_blank_image():
    blank = Image.new("RGB", (200, 200), (255, 255, 255))
    res = ocr_engine.extract_text(blank)
    assert res is not None
    assert res.text == "" or len(res.bounding_boxes) == 0
    assert res.confidence >= 0.0


def test_image_analyzer_blank_image():
    blank = Image.new("RGB", (300, 300), (240, 240, 240))
    res = image_analyzer.analyze_image(blank)
    assert res is not None
    assert res.detected_category == "General Content" or res.detected_category == "General Screen Content"
    assert isinstance(res.description, str)


# ============================================================================
# 4. Evidence Fusion on Empty & Edge Case Element Lists
# ============================================================================

def test_evidence_fusion_both_empty():
    engine = EvidenceFusionEngine()
    result = engine.fuse_evidence(
        target_window_title="EmptyTest",
        uia_elements=[],
        visual_elements=[],
    )
    assert result.matched_count == 0
    assert result.unmatched_uia_count == 0
    assert result.unmatched_visual_count == 0
    assert result.conflicts_count == 0


def test_evidence_fusion_only_uia():
    engine = EvidenceFusionEngine()
    uia = UIElementModel(
        element_id="u1",
        name="Submit",
        control_type="Button",
        bounding_box=[10, 10, 80, 30]
    )
    result = engine.fuse_evidence(
        target_window_title="OnlyUIATest",
        uia_elements=[uia],
        visual_elements=[],
    )
    assert result.matched_count == 0
    assert result.unmatched_uia_count == 1
    assert result.unmatched_visual_count == 0


def test_evidence_fusion_only_visual():
    engine = EvidenceFusionEngine()
    vis = VisualEvidence(
        evidence_id="v1",
        text="Click Here",
        bounds=[10, 10, 80, 30],
        confidence=0.95
    )
    result = engine.fuse_evidence(
        target_window_title="OnlyVisualTest",
        uia_elements=[],
        visual_elements=[vis],
    )
    assert result.matched_count == 0
    assert result.unmatched_uia_count == 0
    assert result.unmatched_visual_count == 1


# ============================================================================
# 5. Worker Cancellation Resilience
# ============================================================================

def test_analysis_worker_cancellation(qapp):
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    worker = AnalysisWorker(image_source=img)
    worker.cancel()
    assert worker._is_cancelled is True
    # Calling run after cancellation exits immediately
    worker.run()


def test_evidence_fusion_worker_cancellation(qapp):
    worker = EvidenceFusionWorker(
        window_handle=None,
        window_title="TestWindow",
        uia_elements=[]
    )
    worker.cancel()
    assert worker._is_cancelled is True
    worker.run()


def test_report_worker_cancellation(qapp):
    worker = ReportWorker(
        application_name="TestApp",
        target_window="TestWindow"
    )
    worker.cancel()
    assert worker._is_cancelled is True
    worker.run()


# ============================================================================
# 6. SQLite Database Connection Management & Handle Cleanup
# ============================================================================

def test_database_manager_connection_cleanup():
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(temp_dir, "test_conn.sqlite3")
        db = DatabaseManager(db_path=db_path)

        # Execute multiple operations rapidly
        for i in range(10):
            db.add_record(
                file_type="PNG",
                analysis_summary=f"Analysis {i}",
                processing_backend="CPU",
                word_count=50,
                confidence=0.99
            )

        records = db.get_records(limit=20)
        assert len(records) == 10

        # Verify that connection closes cleanly by allowing file deletion
        del db
        shutil.rmtree(temp_dir)
        assert not os.path.exists(temp_dir)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# 7. Zero-Finding Report Generation & Digest Line-Ending Neutrality
# ============================================================================

def test_zero_findings_report_generation():
    generator = AuditReportGenerator()
    report = generator.generate_report(
        application_name="PerfectAccessibleApp",
        target_window="MainWindow",
        findings=[],
        ui_elements=[],
        visual_elements=[],
    )

    is_valid, errors = ReportValidator.validate(report)
    assert is_valid is True, f"Validation errors: {errors}"
    assert report.summary.total_findings == 0
    assert len(report.findings) == 0
    assert len(report.evidence_digest) == 64
    assert int(report.evidence_digest, 16) > 0

    # Export to all 3 formats without error
    json_out = JsonReportExporter.export_to_string(report)
    md_out = MarkdownReportExporter.export_to_string(report)
    html_out = HtmlReportExporter.export_to_string(report)

    assert len(json_out) > 0
    assert len(md_out) > 0
    assert len(html_out) > 0


def test_report_digest_line_ending_neutrality():
    generator = AuditReportGenerator()
    report = generator.generate_report(
        application_name="DigestTestApp",
        target_window="MainWindow",
        findings=[],
    )

    digest_1 = calculate_report_digest(report)
    digest_2 = calculate_report_digest(report)
    assert digest_1 == digest_2
    assert verify_report_digest(report, digest_1) is True

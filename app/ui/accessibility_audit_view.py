"""Accessibility Audit view for AccessLens AI (Phase 3).

Implements the complete evidence-first accessibility analysis pipeline:
Select Application -> Inspect Interface -> Capture UIA Tree -> Capture Screenshot ->
On-Device OCR -> Run Deterministic Rules -> Generate Evidence -> Display Findings & Element Highlighting.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
from PIL import Image

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QMessageBox, QProgressBar,
    QPushButton, QRadioButton, QScrollArea, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from ai.reasoning_models import ReasoningResult
from app.workers.reasoning_worker import ReasoningWorker
from accessibility.focus_models import FocusObservation, FocusTraversalResult
from accessibility.focus_path import FocusPath
from app.workers.keyboard_audit_worker import KeyboardAuditWorker

from accessibility.coordinate_mapping import coordinate_mapper
from accessibility.element_model import ElementModel, InterfaceSnapshot, UIElementModel
from accessibility.evidence_engine import EvidenceItem, evidence_engine
from accessibility.evidence_fusion import EvidenceFusionResult, EvidenceMatch, evidence_fusion_engine
from accessibility.findings import AccessibilityFinding, FindingCategory, SignalType
from accessibility.geometry import uia_bounds_to_screenshot_bounds
from accessibility.rule_engine import rule_engine
from accessibility.severity import FindingSeverity, describe_severity
from accessibility.ui_automation import UIAutomationInspectionResult, ui_automation
from accessibility.ui_tree import UITree
from accessibility.visual_models import VisualEvidence
from app.workers.evidence_fusion_worker import EvidenceFusionWorker
from app.ui.components import (
    ACCENT_AMBER, ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN,
    ACCENT_RED, BG_CARD, BG_CARD_BORDER, BG_SURFACE,
    CardWidget, StatusBadge, TEXT_PRIMARY, TEXT_SECONDARY
)
from vision.image_utils import pil_to_qpixmap
from vision.ocr_engine import ocr_engine
from vision.screen_capture import screen_capturer
from reports.report_models import AuditReport
from reports.report_generator import audit_report_generator
from reports.sensitive_data_detector import sensitive_data_detector
from reports.exporters.json_exporter import JsonReportExporter
from reports.exporters.markdown_exporter import MarkdownReportExporter
from reports.exporters.html_exporter import HtmlReportExporter
from app.workers.report_worker import ReportWorker


class WindowSelectionDialog(QDialog):
    """Dialog allowing user to choose an active top-level desktop window to inspect."""

    def __init__(self, windows: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Target Application")
        self.resize(520, 320)
        self.setStyleSheet(f"QDialog {{ background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; }}")
        self._selected_window: Optional[Dict[str, Any]] = None
        self._windows = windows
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Select an active application window to inspect for accessibility barriers:")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        layout.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {BG_CARD};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
        """)

        for w in self._windows:
            title = w.get("title", "Untitled")
            pname = w.get("process_name", "")
            disp = f"{title} [{pname}] (Handle: {w.get('handle')})" if pname else f"{title} (Handle: {w.get('handle')})"
            self.combo.addItem(disp, userData=w)

        layout.addWidget(self.combo)

        note = QLabel("Inspection is read-only. AccessLens never clicks controls, enters text, or alters target states.")
        note.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(note)

        layout.addStretch()

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_accept(self):
        self._selected_window = self.combo.currentData()
        self.accept()

    def get_selected_window(self) -> Optional[Dict[str, Any]]:
        return self._selected_window


class KeyboardAuditConfirmationDialog(QDialog):
    """Explicit safety confirmation dialog for keyboard traversal audits (Phase 5)."""

    def __init__(self, target_title: str = "Selected Application", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Keyboard Navigation Audit")
        self.resize(500, 260)
        self.setStyleSheet(f"QDialog {{ background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; }}")
        self._init_ui(target_title)

    def _init_ui(self, target_title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title_lbl = QLabel("⚠️ Safety Pre-Check: Start Keyboard Audit")
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {ACCENT_AMBER};")
        layout.addWidget(title_lbl)

        msg = (
            "Keyboard auditing will send controlled Tab/Shift+Tab input to the selected "
            f"application ('{target_title}'). Save any unsaved work before continuing."
        )
        body_lbl = QLabel(msg)
        body_lbl.setWordWrap(True)
        body_lbl.setFont(QFont("Segoe UI", 10))
        body_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; line-height: 1.4;")
        layout.addWidget(body_lbl)

        note = QLabel(
            "• Only Tab and Shift+Tab will be sent.\n"
            "• No Enter, Space, or arbitrary keystrokes will be pressed.\n"
            "• The audit stops automatically if focus moves outside the application window."
        )
        note.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(note)

        layout.addStretch()

        btn_box = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: #1E293B;
                color: {TEXT_PRIMARY};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #334155; }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        btn_box.addStretch()

        self.btn_confirm = QPushButton("Start Keyboard Audit")
        self.btn_confirm.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_BLUE};
                color: white;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #1D4ED8; }}
        """)
        self.btn_confirm.clicked.connect(self.accept)
        btn_box.addWidget(self.btn_confirm)

        layout.addLayout(btn_box)


class ReportPreviewDialog(QDialog):
    """Pre-export preview and confirmation dialog (Phase 7)."""

    def __init__(self, metadata: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Accessibility Audit Report Preview")
        self.resize(540, 360)
        self.setStyleSheet(f"QDialog {{ background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; }}")
        self._init_ui(metadata)

    def _init_ui(self, meta: Dict[str, Any]):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title_lbl = QLabel("📋 Audit Report Pre-Export Preview")
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {ACCENT_CYAN};")
        layout.addWidget(title_lbl)

        grid = QFormLayout()
        grid.setSpacing(8)

        def _row(label: str, val: str, color: str = TEXT_PRIMARY):
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
            v_lbl = QLabel(str(val))
            v_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            v_lbl.setStyleSheet(f"color: {color};")
            grid.addRow(lbl, v_lbl)

        _row("Report ID:", meta.get("report_id", "—"), "#A78BFA")
        _row("Target Application:", meta.get("application", "—"))
        _row("Scan Timestamp:", meta.get("scan_time", "—"))
        _row("Findings Count:", str(meta.get("findings_count", "0")), ACCENT_AMBER)
        _row("Severity Distribution:", meta.get("severity_dist", "—"))
        _row("Evidence Items:", str(meta.get("evidence_count", "0")), ACCENT_GREEN)
        _row("Human Review Required:", str(meta.get("human_review_count", "0")), ACCENT_AMBER)
        _row("Privacy Mode:", meta.get("privacy_mode", "Findings Only"), ACCENT_CYAN)
        _row("Hardware Attestation:", meta.get("hardware_status", "AMD CPU Fallback"))

        layout.addLayout(grid)

        if meta.get("sensitive_detected"):
            warn_lbl = QLabel("⚠️ Potential sensitive content detected (emails/credentials). Review privacy mode before export.")
            warn_lbl.setStyleSheet(f"color: {ACCENT_AMBER}; font-size: 11px; font-weight: 600;")
            warn_lbl.setWordWrap(True)
            layout.addWidget(warn_lbl)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(f"background-color: #1E293B; color: {TEXT_PRIMARY}; border: 1px solid {BG_CARD_BORDER}; border-radius: 6px; padding: 6px 16px;")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_box.addStretch()

        btn_gen = QPushButton("Generate & Export")
        btn_gen.setStyleSheet(f"background-color: {ACCENT_GREEN}; color: white; border-radius: 6px; padding: 6px 18px; font-weight: 700;")
        btn_gen.clicked.connect(self.accept)
        btn_box.addWidget(btn_gen)

        layout.addLayout(btn_box)


class AuditExecutionWorker(QThread):
    """Background worker executing the complete deterministic audit pipeline."""

    finished = Signal(object, object, str)  # (InterfaceSnapshot, Optional[Image.Image], status_msg)
    error = Signal(str)

    def __init__(self, window_handle: Optional[int] = None, window_bounds: Optional[List[int]] = None):
        super().__init__()
        self.window_handle = window_handle
        self.window_bounds = window_bounds

    def run(self):
        try:
            # 1. Capture UIA Tree
            result = ui_automation.inspect_window(self.window_handle)
            tree = result.ui_tree

            # 2. Capture Screenshot
            screenshot: Optional[Image.Image] = None
            if self.window_handle:
                screenshot = screen_capturer.capture_window(self.window_handle)
            if screenshot is None:
                screenshot = screen_capturer.capture_primary_screen()

            # 3. On-Device OCR & Correlation
            if screenshot is not None:
                try:
                    ocr_res = ocr_engine.extract_text(screenshot)
                    if ocr_res and ocr_res.bounding_boxes:
                        tree.correlate_with_ocr_boxes(ocr_res.bounding_boxes)
                except Exception:
                    pass

            # 4. Run Deterministic Rules & Evidence Fusion
            findings = rule_engine.evaluate_tree(tree, screenshot=screenshot)

            # 5. Build Unified InterfaceSnapshot
            snapshot = InterfaceSnapshot(
                timestamp=str(int(time.time())),
                application_name=result.app_name,
                window_title=result.window_title,
                window_handle=self.window_handle or 0,
                ui_tree=tree,
                elements=tree.elements,
                findings=findings,
                deterministic_findings=findings,
                backend="CPUExecutionProvider",
                hardware_state="Local Host CPU Fallback"
            )

            status_msg = result.status_message or "Audit Complete."
            self.finished.emit(snapshot, screenshot, status_msg)
        except Exception as e:
            self.error.emit(str(e))


import time


class VisualCanvasWidget(QLabel):
    """Renders interface screenshot with multi-layer visual evidence overlays (Phase 6).

    Supported layers:
    - UIA Bounds (Blue): Direct OS accessibility geometry [UIA_MEASURED]
    - OCR Regions (Magenta): On-device visual OCR text boxes [OCR_DETECTED]
    - Fused Matches (Green): Bipartite matched elements with confidence scores [FUSED]
    - Focus Path (Cyan/Amber): Keyboard focus traversal sequence [KEYBOARD_MEASURED]
    - Finding Highlights (Red): Accessibility barriers grounded on interface
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"background-color: #0B0D13; border: 1px solid {BG_CARD_BORDER}; border-radius: 6px;")
        self.setMinimumSize(260, 200)
        self._original_pixmap: Optional[QPixmap] = None
        self._highlight_box: Optional[List[int]] = None
        self._focus_path_segments: Optional[List[Dict[str, Any]]] = None

        # Layer toggles
        self.show_uia_bounds: bool = True
        self.show_ocr_regions: bool = True
        self.show_matches: bool = True
        self.show_focus_path: bool = True
        self.show_findings: bool = True

        # Layer data
        self._uia_boxes: List[Dict[str, Any]] = []
        self._ocr_boxes: List[Dict[str, Any]] = []
        self._matches: List[Dict[str, Any]] = []
        self._finding_boxes: List[Dict[str, Any]] = []

        self.setText("Visual canvas ready. Screenshot will appear after interface inspection.")

    def set_screenshot(self, pil_image: Optional[Image.Image]):
        if pil_image is not None:
            self._original_pixmap = pil_to_qpixmap(pil_image)
            self._highlight_box = None
            self.redraw()
        else:
            self._original_pixmap = None
            self._highlight_box = None
            self._focus_path_segments = None
            self._uia_boxes.clear()
            self._ocr_boxes.clear()
            self._matches.clear()
            self._finding_boxes.clear()
            self.setText("No screenshot buffer available.")

    def set_layer_visibility(self, uia: bool, ocr: bool, matches: bool, focus_path: bool, findings: bool):
        self.show_uia_bounds = uia
        self.show_ocr_regions = ocr
        self.show_matches = matches
        self.show_focus_path = focus_path
        self.show_findings = findings
        self.redraw()

    def set_evidence_layers(
        self,
        uia_boxes: Optional[List[Dict[str, Any]]] = None,
        ocr_boxes: Optional[List[Dict[str, Any]]] = None,
        matches: Optional[List[Dict[str, Any]]] = None,
        finding_boxes: Optional[List[Dict[str, Any]]] = None,
    ):
        self._uia_boxes = uia_boxes or []
        self._ocr_boxes = ocr_boxes or []
        self._matches = matches or []
        self._finding_boxes = finding_boxes or []
        self.redraw()

    def highlight_box(self, box: Optional[List[int]]):
        self._highlight_box = box
        self.redraw()

    def set_focus_path_segments(self, segments: Optional[List[Dict[str, Any]]]):
        self._focus_path_segments = segments
        self.redraw()

    def redraw(self):
        if not self._original_pixmap:
            return

        canvas = self._original_pixmap.copy()
        painter = QPainter(canvas)

        # 1. Draw UIA Bounds Layer (Thin Blue)
        if self.show_uia_bounds and self._uia_boxes:
            uia_pen = QPen(QColor(59, 130, 246, 170), 1, Qt.PenStyle.SolidLine)
            painter.setPen(uia_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for item in self._uia_boxes:
                b = item.get("bounds")
                if b and len(b) == 4 and b[2] > 0 and b[3] > 0:
                    painter.drawRect(b[0], b[1], b[2], b[3])

        # 2. Draw OCR Regions Layer (Thin Magenta / Orange if suspicious)
        if self.show_ocr_regions and self._ocr_boxes:
            ocr_pen = QPen(QColor(168, 85, 247, 180), 1, Qt.PenStyle.DashLine)
            susp_pen = QPen(QColor(245, 158, 11, 220), 2, Qt.PenStyle.DashDotLine)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for item in self._ocr_boxes:
                b = item.get("bounds")
                if b and len(b) == 4 and b[2] > 0 and b[3] > 0:
                    painter.setPen(susp_pen if item.get("suspicious") else ocr_pen)
                    painter.drawRect(b[0], b[1], b[2], b[3])

        # 3. Draw Fused Matches Layer (Emerald Green with light fill)
        if self.show_matches and self._matches:
            match_pen = QPen(QColor(16, 185, 129, 220), 2)
            match_fill = QColor(16, 185, 129, 25)
            painter.setPen(match_pen)
            for m in self._matches:
                b = m.get("bounds")
                if b and len(b) == 4 and b[2] > 0 and b[3] > 0:
                    painter.fillRect(b[0], b[1], b[2], b[3], match_fill)
                    painter.drawRect(b[0], b[1], b[2], b[3])

        # 4. Draw Focus Path Transitions & Flow Arrows (Cyan / Amber)
        if self.show_focus_path and self._focus_path_segments:
            cyan_pen = QPen(QColor(56, 189, 248), 2)
            amber_pen = QPen(QColor(245, 158, 11), 3)
            for seg in self._focus_path_segments:
                p1 = seg.get("start_point")
                p2 = seg.get("end_point")
                if p1 and p2:
                    is_rep = seg.get("is_repeated", False)
                    painter.setPen(amber_pen if is_rep else cyan_pen)
                    painter.drawLine(p1[0], p1[1], p2[0], p2[1])
                    painter.setBrush(QColor(245, 158, 11, 180) if is_rep else QColor(56, 189, 248, 180))
                    painter.drawEllipse(p2[0] - 6, p2[1] - 6, 12, 12)

        # 5. Draw Finding Highlights Layer (Red outline)
        if self.show_findings and self._finding_boxes:
            finding_pen = QPen(QColor(239, 68, 68, 220), 2)
            finding_fill = QColor(239, 68, 68, 30)
            painter.setPen(finding_pen)
            for fb in self._finding_boxes:
                b = fb.get("bounds")
                if b and len(b) == 4 and b[2] > 0 and b[3] > 0:
                    painter.fillRect(b[0], b[1], b[2], b[3], finding_fill)
                    painter.drawRect(b[0], b[1], b[2], b[3])

        # 6. Selected Element Highlight Box (Prominent Amber outline)
        if self._highlight_box and len(self._highlight_box) == 4:
            x, y, w, h = self._highlight_box
            if w > 0 and h > 0:
                pen = QPen(QColor(245, 158, 11), 3)
                painter.setPen(pen)
                painter.fillRect(x, y, w, h, QColor(245, 158, 11, 50))
                painter.drawRect(x, y, w, h)

        painter.end()

        scaled = canvas.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.redraw()


class AccessibilityAuditView(QWidget):
    """Upgraded Phase 3 Accessibility Audit Workstation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_window: Optional[Dict[str, Any]] = None
        self._current_snapshot: Optional[InterfaceSnapshot] = None
        self._current_screenshot: Optional[Image.Image] = None
        self._current_finding: Optional[AccessibilityFinding] = None
        self._current_reasoning_result: Optional[ReasoningResult] = None
        self._worker: Optional[AuditExecutionWorker] = None
        self._reasoning_worker: Optional[ReasoningWorker] = None
        self._keyboard_worker: Optional[KeyboardAuditWorker] = None
        self._current_traversal_result: Optional[FocusTraversalResult] = None
        self._current_focus_path: Optional[FocusPath] = None
        self._fusion_worker: Optional[EvidenceFusionWorker] = None
        self._current_fusion_result: Optional[EvidenceFusionResult] = None
        self._reasoning_results: Dict[str, ReasoningResult] = {}
        self._report_worker: Optional[ReportWorker] = None
        self._latest_report: Optional[AuditReport] = None
        self._latest_export_paths: Dict[str, str] = {}
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 14)
        main_layout.setSpacing(10)

        # 1. Top Workflow Controls
        control_card = CardWidget()
        ctrl_layout = QVBoxLayout(control_card)
        ctrl_layout.setContentsMargins(12, 10, 12, 10)
        ctrl_layout.setSpacing(8)

        row1 = QHBoxLayout()
        self.btn_select_app = QPushButton("🔍 Select Application")
        self.btn_select_app.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_BLUE};
                color: #FFFFFF;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #1D4ED8; }}
        """)
        self.btn_select_app.clicked.connect(self._on_select_application)
        row1.addWidget(self.btn_select_app)

        self.btn_inspect_current = QPushButton("🎯 Inspect Current Window")
        self.btn_inspect_current.setStyleSheet(f"""
            QPushButton {{
                background-color: #1E293B;
                color: {TEXT_PRIMARY};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #334155; }}
        """)
        self.btn_inspect_current.clicked.connect(self._on_inspect_current)
        row1.addWidget(self.btn_inspect_current)

        self.lbl_target = QLabel("Target: Not selected")
        self.lbl_target.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.lbl_target.setStyleSheet(f"color: {ACCENT_AMBER}; margin-left: 8px;")
        row1.addWidget(self.lbl_target)

        row1.addStretch()

        self.btn_inspect = QPushButton("⚡ Inspect Interface")
        self.btn_inspect.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_GREEN};
                color: #064E3B;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #059669; color: #FFFFFF; }}
        """)
        self.btn_inspect.clicked.connect(self._on_inspect_interface)
        row1.addWidget(self.btn_inspect)

        ctrl_layout.addLayout(row1)

        self.lbl_status = QLabel("Windows UI Automation & Evidence Engine ready.")
        self.lbl_status.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        ctrl_layout.addWidget(self.lbl_status)

        main_layout.addWidget(control_card)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BG_CARD};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{ background-color: {ACCENT_CYAN}; }}
        """)
        main_layout.addWidget(self.progress_bar)

        # 2. Dual Summary Rows: Interface Breakdown & Findings Summary
        summary_card = CardWidget()
        s_layout = QVBoxLayout(summary_card)
        s_layout.setContentsMargins(12, 8, 12, 8)
        s_layout.setSpacing(6)

        # Row A: Element Structure
        row_struct = QHBoxLayout()
        self.val_app = QLabel("Not selected")
        self.val_win = QLabel("Not selected")
        self.val_elements = QLabel("0")
        self.val_focusable = QLabel("0")
        self.val_named = QLabel("0")
        self.val_unnamed = QLabel("0")

        struct_items = [
            ("Application", self.val_app, TEXT_PRIMARY),
            ("Window", self.val_win, TEXT_PRIMARY),
            ("UI Elements", self.val_elements, ACCENT_CYAN),
            ("Focusable", self.val_focusable, ACCENT_GREEN),
            ("Named", self.val_named, "#A78BFA"),
            ("Unnamed", self.val_unnamed, ACCENT_AMBER)
        ]
        for title, val_lbl, color in struct_items:
            box = QHBoxLayout()
            t_lbl = QLabel(f"{title}:")
            t_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            t_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
            val_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            val_lbl.setStyleSheet(f"color: {color};")
            box.addWidget(t_lbl)
            box.addWidget(val_lbl)
            row_struct.addLayout(box)
            row_struct.addSpacing(12)
        row_struct.addStretch()
        s_layout.addLayout(row_struct)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BG_CARD_BORDER};")
        s_layout.addWidget(sep)

        # Row B: Findings Summary
        row_findings = QHBoxLayout()
        f_title = QLabel("FINDINGS SUMMARY:")
        f_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        f_title.setStyleSheet(f"color: {TEXT_SECONDARY};")
        row_findings.addWidget(f_title)

        self.badge_total = StatusBadge("0 TOTAL", bg_color="#1E293B", text_color="#38BDF8")
        self.badge_high = StatusBadge("0 HIGH", bg_color="#78350F", text_color="#FDE68A")
        self.badge_med = StatusBadge("0 MEDIUM", bg_color="#1E3A8A", text_color="#93C5FD")
        self.badge_low = StatusBadge("0 LOW", bg_color="#064E3B", text_color="#A7F3D0")
        self.badge_info = StatusBadge("0 INFO", bg_color="#1E293B", text_color=TEXT_SECONDARY)

        row_findings.addWidget(self.badge_total)
        row_findings.addWidget(self.badge_high)
        row_findings.addWidget(self.badge_med)
        row_findings.addWidget(self.badge_low)
        row_findings.addWidget(self.badge_info)
        row_findings.addStretch()

        self.lbl_visual_map_status = QLabel("")
        self.lbl_visual_map_status.setStyleSheet(f"color: {ACCENT_AMBER}; font-size: 11px;")
        row_findings.addWidget(self.lbl_visual_map_status)

        s_layout.addLayout(row_findings)
        main_layout.addWidget(summary_card)

        # 2b. Keyboard Navigation Audit Card (Phase 5)
        kb_card = CardWidget()
        kb_layout = QVBoxLayout(kb_card)
        kb_layout.setContentsMargins(12, 10, 12, 10)
        kb_layout.setSpacing(8)

        # Header row
        kb_head_row = QHBoxLayout()
        kb_title = QLabel("KEYBOARD NAVIGATION AUDIT")
        kb_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        kb_title.setStyleSheet(f"color: {ACCENT_CYAN};")
        kb_head_row.addWidget(kb_title)

        self.lbl_kb_target = QLabel("Target: [No Application Selected]")
        self.lbl_kb_target.setStyleSheet(f"color: {ACCENT_AMBER}; font-weight: 600; margin-left: 8px;")
        kb_head_row.addWidget(self.lbl_kb_target)

        kb_head_row.addStretch()

        self.lbl_kb_status = QLabel("Keyboard audit idle")
        self.lbl_kb_status.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        kb_head_row.addWidget(self.lbl_kb_status)

        kb_layout.addLayout(kb_head_row)

        # Controls row: Direction, Max Steps, Delay, Buttons
        kb_ctrl_row = QHBoxLayout()
        kb_ctrl_row.setSpacing(10)

        lbl_dir = QLabel("Direction:")
        lbl_dir.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600;")
        kb_ctrl_row.addWidget(lbl_dir)

        self.rb_forward = QRadioButton("Forward Tab")
        self.rb_forward.setChecked(True)
        self.rb_forward.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.rb_reverse = QRadioButton("Reverse Shift+Tab")
        self.rb_reverse.setStyleSheet(f"color: {TEXT_PRIMARY};")
        kb_ctrl_row.addWidget(self.rb_forward)
        kb_ctrl_row.addWidget(self.rb_reverse)

        lbl_steps = QLabel("Max Steps:")
        lbl_steps.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600; margin-left: 6px;")
        kb_ctrl_row.addWidget(lbl_steps)
        self.spin_max_steps = QSpinBox()
        self.spin_max_steps.setRange(5, 500)
        self.spin_max_steps.setValue(100)
        self.spin_max_steps.setStyleSheet(f"background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BG_CARD_BORDER}; border-radius: 4px; padding: 2px 6px;")
        kb_ctrl_row.addWidget(self.spin_max_steps)

        lbl_delay = QLabel("Delay:")
        lbl_delay.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600; margin-left: 6px;")
        kb_ctrl_row.addWidget(lbl_delay)
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(50, 1000)
        self.spin_delay.setValue(150)
        self.spin_delay.setSuffix(" ms")
        self.spin_delay.setStyleSheet(f"background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BG_CARD_BORDER}; border-radius: 4px; padding: 2px 6px;")
        kb_ctrl_row.addWidget(self.spin_delay)

        kb_ctrl_row.addStretch()

        self.btn_start_kb_audit = QPushButton("▶ Start Keyboard Audit")
        self.btn_start_kb_audit.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_BLUE};
                color: white;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #1D4ED8; }}
            QPushButton:disabled {{ background-color: #334155; color: #64748B; }}
        """)
        self.btn_start_kb_audit.clicked.connect(self._on_start_keyboard_audit)
        kb_ctrl_row.addWidget(self.btn_start_kb_audit)

        self.btn_stop_kb_audit = QPushButton("⏹ Stop Audit")
        self.btn_stop_kb_audit.setEnabled(False)
        self.btn_stop_kb_audit.setStyleSheet(f"""
            QPushButton {{
                background-color: #7F1D1D;
                color: #FECACA;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #991B1B; color: white; }}
            QPushButton:disabled {{ background-color: #1E293B; color: #475569; }}
        """)
        self.btn_stop_kb_audit.clicked.connect(self._on_stop_keyboard_audit)
        kb_ctrl_row.addWidget(self.btn_stop_kb_audit)

        kb_layout.addLayout(kb_ctrl_row)

        # Summary Metrics row
        kb_metrics_row = QHBoxLayout()
        self.badge_kb_steps = StatusBadge("0 STEPS", bg_color="#1E293B", text_color="#38BDF8")
        self.badge_kb_unique = StatusBadge("0 UNIQUE", bg_color="#1E293B", text_color="#A7F3D0")
        self.badge_kb_repeated = StatusBadge("0 REPEATED", bg_color="#1E293B", text_color="#FDE68A")
        self.badge_kb_trap = StatusBadge("TRAP: NO", bg_color="#064E3B", text_color="#A7F3D0")
        self.badge_kb_unreached = StatusBadge("0 UNREACHED", bg_color="#1E293B", text_color=TEXT_SECONDARY)
        self.badge_kb_human = StatusBadge("HUMAN REVIEW: REQUIRED", bg_color="#78350F", text_color="#FDE68A")

        kb_metrics_row.addWidget(self.badge_kb_steps)
        kb_metrics_row.addWidget(self.badge_kb_unique)
        kb_metrics_row.addWidget(self.badge_kb_repeated)
        kb_metrics_row.addWidget(self.badge_kb_trap)
        kb_metrics_row.addWidget(self.badge_kb_unreached)
        kb_metrics_row.addWidget(self.badge_kb_human)
        kb_metrics_row.addStretch()
        kb_layout.addLayout(kb_metrics_row)

        main_layout.addWidget(kb_card)

        # 3. Main Splitter: Left (Tree & Visuals), Center (Findings List), Right (Evidence Chain)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # --- Left Panel: Tabbed (Tree, Visual Canvas, Focus Path, Traversal Log) ---
        left_card = CardWidget()
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(8, 8, 8, 8)

        left_tabs = QTabWidget()
        # Subtab 1: UI Tree
        tree_container = QWidget()
        t_lay = QVBoxLayout(tree_container)
        t_lay.setContentsMargins(4, 4, 4, 4)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(3)
        self.tree_widget.setHeaderLabels(["Element / Accessible Name", "Type", "Automation ID"])
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: #12151E;
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QTreeWidget::item:selected {{ background-color: #2563EB; color: white; }}
        """)
        self.tree_widget.currentItemChanged.connect(self._on_tree_element_selected)
        t_lay.addWidget(self.tree_widget)
        left_tabs.addTab(tree_container, "UI Tree")

        # Subtab 2: Visual Canvas & Multimodal Evidence Fusion
        canvas_container = QWidget()
        c_lay = QVBoxLayout(canvas_container)
        c_lay.setContentsMargins(6, 6, 6, 6)
        c_lay.setSpacing(6)

        # Layer toggles & Fusion actions card
        layer_card = CardWidget()
        layer_layout = QVBoxLayout(layer_card)
        layer_layout.setContentsMargins(8, 6, 8, 6)
        layer_layout.setSpacing(6)

        ctrl_row1 = QHBoxLayout()
        ctrl_row1.setSpacing(8)

        lbl_layers = QLabel("VISUAL LAYERS:")
        lbl_layers.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_layers.setStyleSheet(f"color: {ACCENT_CYAN};")
        ctrl_row1.addWidget(lbl_layers)

        self.chk_layer_uia = QCheckBox("UIA (Blue)")
        self.chk_layer_uia.setChecked(True)
        self.chk_layer_uia.setStyleSheet("color: #60A5FA; font-size: 11px;")
        self.chk_layer_uia.toggled.connect(self._on_layer_visibility_changed)
        ctrl_row1.addWidget(self.chk_layer_uia)

        self.chk_layer_ocr = QCheckBox("OCR (Magenta)")
        self.chk_layer_ocr.setChecked(True)
        self.chk_layer_ocr.setStyleSheet("color: #C084FC; font-size: 11px;")
        self.chk_layer_ocr.toggled.connect(self._on_layer_visibility_changed)
        ctrl_row1.addWidget(self.chk_layer_ocr)

        self.chk_layer_matches = QCheckBox("Matches (Green)")
        self.chk_layer_matches.setChecked(True)
        self.chk_layer_matches.setStyleSheet("color: #34D399; font-size: 11px;")
        self.chk_layer_matches.toggled.connect(self._on_layer_visibility_changed)
        ctrl_row1.addWidget(self.chk_layer_matches)

        self.chk_layer_focus = QCheckBox("Focus (Cyan)")
        self.chk_layer_focus.setChecked(True)
        self.chk_layer_focus.setStyleSheet("color: #38BDF8; font-size: 11px;")
        self.chk_layer_focus.toggled.connect(self._on_layer_visibility_changed)
        ctrl_row1.addWidget(self.chk_layer_focus)

        self.chk_layer_findings = QCheckBox("Findings (Red)")
        self.chk_layer_findings.setChecked(True)
        self.chk_layer_findings.setStyleSheet("color: #F87171; font-size: 11px;")
        self.chk_layer_findings.toggled.connect(self._on_layer_visibility_changed)
        ctrl_row1.addWidget(self.chk_layer_findings)

        ctrl_row1.addStretch()

        self.btn_capture_evidence = QPushButton("📷 Fuse Visual Evidence")
        self.btn_capture_evidence.setStyleSheet(f"""
            QPushButton {{
                background-color: #2563EB;
                color: #FFFFFF;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #1D4ED8; }}
        """)
        self.btn_capture_evidence.clicked.connect(self._on_trigger_evidence_fusion)
        ctrl_row1.addWidget(self.btn_capture_evidence)

        layer_layout.addLayout(ctrl_row1)

        # Evidence Summary Badges Row
        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        self.badge_shot_status = StatusBadge("SHOT: UNAVAILABLE", bg_color="#1E293B", text_color=TEXT_SECONDARY)
        self.badge_ev_matched = StatusBadge("0 MATCHED", bg_color="#064E3B", text_color="#A7F3D0")
        self.badge_ev_unmatched = StatusBadge("0 UNMATCHED", bg_color="#1E293B", text_color=ACCENT_CYAN)
        self.badge_ev_conflicts = StatusBadge("0 CONFLICTS", bg_color="#78350F", text_color="#FDE68A")
        self.badge_ev_focus_map = StatusBadge("FOCUS: UNMAPPED", bg_color="#1E293B", text_color=TEXT_SECONDARY)

        badge_row.addWidget(self.badge_shot_status)
        badge_row.addWidget(self.badge_ev_matched)
        badge_row.addWidget(self.badge_ev_unmatched)
        badge_row.addWidget(self.badge_ev_conflicts)
        badge_row.addWidget(self.badge_ev_focus_map)
        badge_row.addStretch()
        layer_layout.addLayout(badge_row)

        c_lay.addWidget(layer_card)

        # Canvas Widget
        self.visual_canvas = VisualCanvasWidget()
        c_lay.addWidget(self.visual_canvas, stretch=1)

        # Bottom Evidence Inspector Panel
        inspector_card = CardWidget()
        insp_lay = QVBoxLayout(inspector_card)
        insp_lay.setContentsMargins(8, 6, 8, 6)
        insp_lay.setSpacing(4)

        insp_header = QLabel("EVIDENCE INSPECTOR (GROUNDED MULTIMODAL CORRELATION)")
        insp_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        insp_header.setStyleSheet(f"color: {ACCENT_AMBER};")
        insp_lay.addWidget(insp_header)

        self.txt_inspector_details = QTextEdit()
        self.txt_inspector_details.setReadOnly(True)
        self.txt_inspector_details.setPlaceholderText("Select an element in the UI Tree or a Finding to inspect fused UIA and visual evidence...")
        self.txt_inspector_details.setMaximumHeight(85)
        self.txt_inspector_details.setStyleSheet(f"""
            QTextEdit {{
                background-color: #12151E;
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 4px;
                color: {TEXT_PRIMARY};
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }}
        """)
        insp_lay.addWidget(self.txt_inspector_details)
        c_lay.addWidget(inspector_card)

        left_tabs.addTab(canvas_container, "Visual Canvas & Highlights")

        # Subtab 3: Focus Path
        focus_path_container = QWidget()
        fp_lay = QVBoxLayout(focus_path_container)
        fp_lay.setContentsMargins(6, 6, 6, 6)
        fp_lay.setSpacing(6)

        fp_header = QLabel("FOCUS PATH TRAVERSAL SEQUENCE")
        fp_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        fp_header.setStyleSheet(f"color: {ACCENT_CYAN};")
        fp_lay.addWidget(fp_header)

        self.txt_focus_path = QTextEdit()
        self.txt_focus_path.setReadOnly(True)
        self.txt_focus_path.setPlaceholderText("Focus sequence graph will appear here after running a Keyboard Navigation Audit.")
        self.txt_focus_path.setStyleSheet(f"""
            QTextEdit {{
                background-color: #12151E;
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }}
        """)
        fp_lay.addWidget(self.txt_focus_path)

        self.lbl_focus_path_mapping = QLabel("Visual focus mapping unavailable; traversal data remains available.")
        self.lbl_focus_path_mapping.setStyleSheet(f"color: {ACCENT_AMBER}; font-size: 11px;")
        fp_lay.addWidget(self.lbl_focus_path_mapping)

        left_tabs.addTab(focus_path_container, "Focus Path")

        # Subtab 4: Live Traversal Steps Log
        trav_container = QWidget()
        tr_lay = QVBoxLayout(trav_container)
        tr_lay.setContentsMargins(6, 6, 6, 6)
        tr_lay.setSpacing(6)

        tr_header = QLabel("LIVE TRAVERSAL LOG")
        tr_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        tr_header.setStyleSheet(f"color: {ACCENT_GREEN};")
        tr_lay.addWidget(tr_header)

        self.table_traversal = QTableWidget(0, 5)
        self.table_traversal.setHorizontalHeaderLabels(["Step", "Element", "Control Type", "Focus", "Time"])
        self.table_traversal.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_traversal.verticalHeader().setVisible(False)
        self.table_traversal.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_traversal.setStyleSheet(f"""
            QTableWidget {{
                background-color: #12151E;
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QTableWidget::item:selected {{ background-color: #1E3A8A; color: white; }}
        """)
        tr_lay.addWidget(self.table_traversal)
        left_tabs.addTab(trav_container, "Live Traversal Log")

        left_layout.addWidget(left_tabs)
        splitter.addWidget(left_card)

        # --- Center Panel: Findings List ---
        center_card = CardWidget()
        center_layout = QVBoxLayout(center_card)
        center_layout.setContentsMargins(10, 10, 10, 10)

        center_head = QLabel("DETECTED BARRIERS & OBSERVATIONS")
        center_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        center_head.setStyleSheet(f"color: {ACCENT_CYAN};")
        center_layout.addWidget(center_head)

        self.findings_table = QTableWidget(0, 4)
        self.findings_table.setHorizontalHeaderLabels(["Severity", "Accessibility Barrier", "Confidence", "Source"])
        self.findings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.findings_table.verticalHeader().setVisible(False)
        self.findings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.findings_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.findings_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #12151E;
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QTableWidget::item:selected {{ background-color: #1E3A8A; color: white; }}
        """)
        self.findings_table.itemSelectionChanged.connect(self._on_finding_table_selection)
        center_layout.addWidget(self.findings_table)
        splitter.addWidget(center_card)

        # --- Right Panel: Finding Detail & Grounded Evidence Chain ---
        right_card = CardWidget()
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(10, 10, 10, 10)

        right_head = QLabel("GROUNDED EVIDENCE CHAIN")
        right_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        right_head.setStyleSheet(f"color: {ACCENT_AMBER};")
        right_layout.addWidget(right_head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        evidence_container = QWidget()
        self.ev_layout = QVBoxLayout(evidence_container)
        self.ev_layout.setSpacing(10)

        # Title & Badges
        self.lbl_finding_title = QLabel("Select a finding to inspect grounded evidence.")
        self.lbl_finding_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_finding_title.setWordWrap(True)
        self.lbl_finding_title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.ev_layout.addWidget(self.lbl_finding_title)

        meta_box = QHBoxLayout()
        self.badge_finding_sev = StatusBadge("INFO", bg_color="#1E293B", text_color=TEXT_SECONDARY)
        self.badge_finding_conf = StatusBadge("Conf: —", bg_color="#1E293B", text_color=ACCENT_CYAN)
        meta_box.addWidget(self.badge_finding_sev)
        meta_box.addWidget(self.badge_finding_conf)
        meta_box.addStretch()
        self.ev_layout.addLayout(meta_box)

        # Observation
        obs_box = QVBoxLayout()
        lbl_obs_h = QLabel("Observation:")
        lbl_obs_h.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_obs_h.setStyleSheet(f"color: {ACCENT_CYAN};")
        self.txt_obs = QTextEdit()
        self.txt_obs.setReadOnly(True)
        self.txt_obs.setMaximumHeight(65)
        obs_box.addWidget(lbl_obs_h)
        obs_box.addWidget(self.txt_obs)
        self.ev_layout.addLayout(obs_box)

        # Evidence Items
        ev_box = QVBoxLayout()
        lbl_ev_h = QLabel("Evidence (Traceable & Grounded):")
        lbl_ev_h.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_ev_h.setStyleSheet(f"color: {ACCENT_AMBER};")
        self.txt_evidence = QTextEdit()
        self.txt_evidence.setReadOnly(True)
        self.txt_evidence.setMinimumHeight(110)
        ev_box.addWidget(lbl_ev_h)
        ev_box.addWidget(self.txt_evidence)
        self.ev_layout.addLayout(ev_box)

        # Why it matters / Impact
        why_box = QVBoxLayout()
        lbl_why_h = QLabel("Why This Matters:")
        lbl_why_h.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_why_h.setStyleSheet(f"color: #F87171;")
        self.txt_impact = QTextEdit()
        self.txt_impact.setReadOnly(True)
        self.txt_impact.setMaximumHeight(70)
        why_box.addWidget(lbl_why_h)
        why_box.addWidget(self.txt_impact)
        self.ev_layout.addLayout(why_box)

        # Recommended Action
        rec_box = QVBoxLayout()
        lbl_rec_h = QLabel("Recommended Action:")
        lbl_rec_h.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_rec_h.setStyleSheet(f"color: {ACCENT_GREEN};")
        self.txt_rec = QTextEdit()
        self.txt_rec.setReadOnly(True)
        self.txt_rec.setMaximumHeight(75)
        rec_box.addWidget(lbl_rec_h)
        rec_box.addWidget(self.txt_rec)
        self.ev_layout.addLayout(rec_box)

        # Human verification requirement notice
        self.lbl_human_verif = QLabel("Requires Human Review: Yes")
        self.lbl_human_verif.setStyleSheet(f"color: {ACCENT_AMBER}; font-size: 11px; font-weight: 600;")
        self.ev_layout.addWidget(self.lbl_human_verif)

        self.lbl_source = QLabel("Source: —")
        self.lbl_source.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self.ev_layout.addWidget(self.lbl_source)

        # --- Phase 4: Local AI Reasoning & Remediation Section ---
        sep_ai = QFrame()
        sep_ai.setFrameShape(QFrame.Shape.HLine)
        sep_ai.setStyleSheet(f"color: {BG_CARD_BORDER}; margin-top: 6px; margin-bottom: 6px;")
        self.ev_layout.addWidget(sep_ai)

        ai_btn_row = QHBoxLayout()
        self.btn_explain_finding = QPushButton("⚡ Explain Finding")
        self.btn_explain_finding.setStyleSheet(f"""
            QPushButton {{
                background-color: #2563EB;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #1D4ED8; }}
            QPushButton:disabled {{ background-color: #1E293B; color: #64748B; }}
        """)
        self.btn_explain_finding.clicked.connect(self._on_explain_finding)
        self.btn_explain_finding.setEnabled(False)
        ai_btn_row.addWidget(self.btn_explain_finding)

        self.btn_recommend_fix = QPushButton("🛠️ Recommend Fix")
        self.btn_recommend_fix.setStyleSheet(f"""
            QPushButton {{
                background-color: #059669;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #047857; }}
            QPushButton:disabled {{ background-color: #1E293B; color: #64748B; }}
        """)
        self.btn_recommend_fix.clicked.connect(self._on_recommend_fix)
        self.btn_recommend_fix.setEnabled(False)
        ai_btn_row.addWidget(self.btn_recommend_fix)

        self.btn_copy_guidance = QPushButton("📋 Copy Guidance")
        self.btn_copy_guidance.setStyleSheet(f"""
            QPushButton {{
                background-color: #334155;
                color: {TEXT_PRIMARY};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #475569; }}
            QPushButton:disabled {{ background-color: #1E293B; color: #64748B; }}
        """)
        self.btn_copy_guidance.clicked.connect(self._on_copy_guidance)
        self.btn_copy_guidance.setEnabled(False)
        ai_btn_row.addWidget(self.btn_copy_guidance)
        ai_btn_row.addStretch()
        self.ev_layout.addLayout(ai_btn_row)

        ai_card = CardWidget()
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setContentsMargins(10, 8, 10, 8)
        ai_layout.setSpacing(6)

        ai_header_row = QHBoxLayout()
        ai_title = QLabel("LOCAL AI REASONING & REMEDIATION")
        ai_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        ai_title.setStyleSheet(f"color: {ACCENT_CYAN};")
        ai_header_row.addWidget(ai_title)
        ai_header_row.addStretch()

        self.badge_local_only = StatusBadge("LOCAL ONLY", bg_color="#064E3B", text_color="#A7F3D0")
        self.badge_cpu_runtime = StatusBadge("CPU RUNTIME", bg_color="#1E293B", text_color="#93C5FD")
        self.badge_human_req = StatusBadge("HUMAN REVIEW REQUIRED", bg_color="#78350F", text_color="#FDE68A")
        ai_header_row.addWidget(self.badge_local_only)
        ai_header_row.addWidget(self.badge_cpu_runtime)
        ai_header_row.addWidget(self.badge_human_req)
        ai_layout.addLayout(ai_header_row)

        self.lbl_ai_status = QLabel("Select a finding and click 'Explain Finding' or 'Recommend Fix'.")
        self.lbl_ai_status.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; font-style: italic;")
        ai_layout.addWidget(self.lbl_ai_status)

        # AI Summary & Why it matters
        lbl_ai_sum = QLabel("Contextual Reasoning:")
        lbl_ai_sum.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_ai_sum.setStyleSheet(f"color: {TEXT_PRIMARY};")
        ai_layout.addWidget(lbl_ai_sum)

        self.txt_ai_summary = QTextEdit()
        self.txt_ai_summary.setReadOnly(True)
        self.txt_ai_summary.setPlaceholderText("Evidence-grounded explanation will appear here...")
        self.txt_ai_summary.setMinimumHeight(70)
        self.txt_ai_summary.setMaximumHeight(105)
        ai_layout.addWidget(self.txt_ai_summary)

        # Confidence Explanation
        lbl_ai_conf = QLabel("Confidence Grounding:")
        lbl_ai_conf.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_ai_conf.setStyleSheet(f"color: {ACCENT_CYAN};")
        ai_layout.addWidget(lbl_ai_conf)

        self.txt_ai_confidence_exp = QTextEdit()
        self.txt_ai_confidence_exp.setReadOnly(True)
        self.txt_ai_confidence_exp.setPlaceholderText("Confidence grounding based on measured/detected signals...")
        self.txt_ai_confidence_exp.setMaximumHeight(50)
        ai_layout.addWidget(self.txt_ai_confidence_exp)

        # Recommended Fix & Developer Guidance
        lbl_ai_rem = QLabel("Recommended Developer Fix & Actions:")
        lbl_ai_rem.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_ai_rem.setStyleSheet(f"color: {ACCENT_GREEN};")
        ai_layout.addWidget(lbl_ai_rem)

        self.txt_ai_remediation = QTextEdit()
        self.txt_ai_remediation.setReadOnly(True)
        self.txt_ai_remediation.setPlaceholderText("Actionable developer remediation and code guidance...")
        self.txt_ai_remediation.setMinimumHeight(95)
        ai_layout.addWidget(self.txt_ai_remediation)

        # Human Verification Checklist
        verif_card = QFrame()
        verif_card.setStyleSheet(f"background-color: #12151E; border: 1px solid {BG_CARD_BORDER}; border-radius: 6px; padding: 6px;")
        verif_layout = QVBoxLayout(verif_card)
        verif_layout.setContentsMargins(6, 6, 6, 6)
        verif_layout.setSpacing(4)

        verif_header = QLabel("HUMAN VERIFICATION CHECKLIST (MANDATORY)")
        verif_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        verif_header.setStyleSheet(f"color: {ACCENT_AMBER};")
        verif_layout.addWidget(verif_header)

        self.chk_step1 = QCheckBox("Reproduce the issue in the target application")
        self.chk_step2 = QCheckBox("Inspect affected element in Accessibility Insights / Inspect.exe")
        self.chk_step3 = QCheckBox("Verify keyboard behavior (Tab navigation & focus ring) where relevant")
        self.chk_step4 = QCheckBox("Test with Windows Narrator (Ctrl+Win+Enter) or screen reader")
        self.chk_step5 = QCheckBox("Apply recommended developer remediation")
        self.chk_step6 = QCheckBox("Re-run AccessLens audit to verify barrier removal")

        self.verification_checkboxes = [
            self.chk_step1, self.chk_step2, self.chk_step3,
            self.chk_step4, self.chk_step5, self.chk_step6
        ]
        for chk in self.verification_checkboxes:
            chk.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px;")
            verif_layout.addWidget(chk)

        ai_layout.addWidget(verif_card)

        # AI Runtime Info Footer
        self.lbl_ai_model_footer = QLabel(
            "AI Runtime: Deterministic Local Reasoning (CPU) | "
            "Model: AccessLens Rule-Based Remediation Engine v1.0 | "
            "Privacy: LOCAL ONLY (Zero Cloud APIs)"
        )
        self.lbl_ai_model_footer.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        ai_layout.addWidget(self.lbl_ai_model_footer)

        self.ev_layout.addWidget(ai_card)

        scroll.setWidget(evidence_container)
        right_layout.addWidget(scroll)
        splitter.addWidget(right_card)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 4)
        main_layout.addWidget(splitter)

        # --- 4. Report & Export Section (Phase 7) ---
        report_card = CardWidget()
        rep_layout = QVBoxLayout(report_card)
        rep_layout.setContentsMargins(12, 10, 12, 10)
        rep_layout.setSpacing(8)

        # Header row: Title & Badges
        rep_head_row = QHBoxLayout()
        rep_title = QLabel("REPORT & EXPORT")
        rep_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        rep_title.setStyleSheet(f"color: {ACCENT_GREEN};")
        rep_head_row.addWidget(rep_title)

        self.badge_rep_findings = StatusBadge("0 FINDINGS", bg_color="#1E293B", text_color="#38BDF8")
        self.badge_rep_evidence = StatusBadge("0 EVIDENCE ITEMS", bg_color="#1E293B", text_color="#A7F3D0")
        self.badge_rep_human = StatusBadge("0 HUMAN REVIEW", bg_color="#1E293B", text_color="#FDE68A")
        self.badge_rep_conflicts = StatusBadge("0 CONFLICTS", bg_color="#1E293B", text_color="#F87171")

        rep_head_row.addWidget(self.badge_rep_findings)
        rep_head_row.addWidget(self.badge_rep_evidence)
        rep_head_row.addWidget(self.badge_rep_human)
        rep_head_row.addWidget(self.badge_rep_conflicts)
        rep_head_row.addStretch()

        self.lbl_report_status = QLabel("Report generator ready")
        self.lbl_report_status.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        rep_head_row.addWidget(self.lbl_report_status)
        rep_layout.addLayout(rep_head_row)

        # Controls & Options row
        rep_ctrl_row = QHBoxLayout()
        rep_ctrl_row.setSpacing(12)

        lbl_priv = QLabel("Privacy Mode:")
        lbl_priv.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600;")
        rep_ctrl_row.addWidget(lbl_priv)

        self.combo_privacy_mode = QComboBox()
        self.combo_privacy_mode.addItems(["Findings Only", "Redacted", "Local Full"])
        self.combo_privacy_mode.setStyleSheet(f"background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BG_CARD_BORDER}; border-radius: 4px; padding: 3px 8px;")
        rep_ctrl_row.addWidget(self.combo_privacy_mode)

        lbl_imgs = QLabel("Evidence Images:")
        lbl_imgs.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600; margin-left: 6px;")
        rep_ctrl_row.addWidget(lbl_imgs)

        self.combo_image_mode = QComboBox()
        self.combo_image_mode.addItems(["Findings Only", "None", "All Evidence"])
        self.combo_image_mode.setStyleSheet(f"background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BG_CARD_BORDER}; border-radius: 4px; padding: 3px 8px;")
        rep_ctrl_row.addWidget(self.combo_image_mode)

        rep_ctrl_row.addStretch()

        # Action Buttons
        self.btn_generate_report = QPushButton("📄 Generate Report")
        self.btn_generate_report.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_GREEN};
                color: white;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #047857; }}
            QPushButton:disabled {{ background-color: #334155; color: #64748B; }}
        """)
        self.btn_generate_report.clicked.connect(self._on_generate_report_clicked)
        rep_ctrl_row.addWidget(self.btn_generate_report)

        self.btn_export_json = QPushButton("Export JSON")
        self.btn_export_json.setEnabled(False)
        self.btn_export_json.setStyleSheet(f"background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BG_CARD_BORDER}; border-radius: 4px; padding: 6px 12px; font-weight: 600;")
        self.btn_export_json.clicked.connect(lambda: self._on_export_format("json"))
        rep_ctrl_row.addWidget(self.btn_export_json)

        self.btn_export_md = QPushButton("Export Markdown")
        self.btn_export_md.setEnabled(False)
        self.btn_export_md.setStyleSheet(f"background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BG_CARD_BORDER}; border-radius: 4px; padding: 6px 12px; font-weight: 600;")
        self.btn_export_md.clicked.connect(lambda: self._on_export_format("md"))
        rep_ctrl_row.addWidget(self.btn_export_md)

        self.btn_export_html = QPushButton("Export HTML")
        self.btn_export_html.setEnabled(False)
        self.btn_export_html.setStyleSheet(f"background-color: {ACCENT_BLUE}; color: white; border-radius: 4px; padding: 6px 14px; font-weight: 700;")
        self.btn_export_html.clicked.connect(lambda: self._on_export_format("html"))
        rep_ctrl_row.addWidget(self.btn_export_html)

        self.btn_open_folder = QPushButton("📁 Open Report Folder")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.setStyleSheet(f"background-color: {BG_CARD}; color: {TEXT_SECONDARY}; border: 1px solid {BG_CARD_BORDER}; border-radius: 4px; padding: 6px 12px; font-weight: 600;")
        self.btn_open_folder.clicked.connect(self._on_open_report_folder)
        rep_ctrl_row.addWidget(self.btn_open_folder)

        rep_layout.addLayout(rep_ctrl_row)
        main_layout.addWidget(report_card)

    def _on_select_application(self):
        windows = ui_automation.list_open_windows()
        if not windows:
            QMessageBox.information(
                self,
                "No Open Windows Detected",
                "No titled top-level desktop windows were detected.\n"
                "Ensure target application is not minimized, or use 'Inspect Current Window'."
            )
            return

        dlg = WindowSelectionDialog(windows, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            win = dlg.get_selected_window()
            if win:
                self._target_window = win
                title = win.get("title", "Untitled")
                pname = win.get("process_name", "")
                disp = f"{title} ({pname})" if pname else title
                self.lbl_target.setText(f"Target: {disp}")
                self.lbl_kb_target.setText(f"Target: {disp}")
                self.lbl_status.setText(f"Selected: {title}. Click 'Inspect Interface' to run evidence-first audit.")

    def _on_inspect_current(self):
        self._target_window = None
        self.lbl_target.setText("Target: Currently Focused Window")
        self.lbl_kb_target.setText("Target: Currently Focused Window")
        self._on_inspect_interface()

    def _on_inspect_interface(self):
        hwnd = self._target_window.get("handle") if self._target_window else None
        bounds = self._target_window.get("bounds") if self._target_window else None

        self.btn_inspect.setEnabled(False)
        self.btn_select_app.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Executing multimodal pipeline (UIA + Screenshot + OCR + Rules + Evidence)...")

        self._worker = AuditExecutionWorker(hwnd, bounds)
        self._worker.finished.connect(self._on_audit_finished)
        self._worker.error.connect(self._on_audit_error)
        self._worker.start()

    def _on_audit_finished(self, snapshot: InterfaceSnapshot, screenshot: Optional[Image.Image], status_msg: str):
        self.btn_inspect.setEnabled(True)
        self.btn_select_app.setEnabled(True)
        self.progress_bar.setVisible(False)

        self._current_snapshot = snapshot
        self._current_screenshot = screenshot

        # Update Structure counts
        self.val_app.setText(snapshot.application_name or "Not available")
        self.val_win.setText(snapshot.window_title or "Not available")

        tree = snapshot.ui_tree
        if tree:
            counts = tree.summary_counts()
            self.val_elements.setText(str(counts["total"]))
            self.val_focusable.setText(str(counts["focusable"]))
            self.val_named.setText(str(counts["named"]))
            self.val_unnamed.setText(str(counts["unnamed"]))

        # Update Findings Badges
        findings = snapshot.findings
        total_f = len(findings)
        high_f = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
        med_f = sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM)
        low_f = sum(1 for f in findings if f.severity == FindingSeverity.LOW)
        info_f = sum(1 for f in findings if f.severity == FindingSeverity.INFO)

        self.badge_total.setText(f"{total_f} TOTAL")
        self.badge_high.setText(f"{high_f} HIGH")
        self.badge_med.setText(f"{med_f} MEDIUM")
        self.badge_low.setText(f"{low_f} LOW")
        self.badge_info.setText(f"{info_f} INFO")

        # Update Report Section Badges
        self.badge_rep_findings.setText(f"{total_f} FINDINGS")
        self.badge_rep_evidence.setText(f"{len(snapshot.elements)} EVIDENCE ITEMS")
        self.badge_rep_human.setText(f"{sum(1 for f in findings if f.human_verification_required)} HUMAN REVIEW")
        self.lbl_report_status.setText("Scan completed. Ready to generate report.")

        # Update Status
        self.lbl_status.setText(status_msg)

        # Update Visual Canvas
        self.visual_canvas.set_screenshot(screenshot)

        # Populate UI Automation Tree
        self._populate_tree(snapshot.elements)

        # Populate Findings Table
        self._populate_findings_table(findings)

        # Trigger Phase 6 Multimodal Evidence Fusion
        self._trigger_evidence_fusion()

    def _on_audit_error(self, err: str):
        self.btn_inspect.setEnabled(True)
        self.btn_select_app.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"Audit pipeline error: {err}")
        QMessageBox.warning(self, "Audit Pipeline Error", f"Failed to complete audit:\n{err}")

    def _on_layer_visibility_changed(self):
        self.visual_canvas.set_layer_visibility(
            uia=self.chk_layer_uia.isChecked(),
            ocr=self.chk_layer_ocr.isChecked(),
            matches=self.chk_layer_matches.isChecked(),
            focus_path=self.chk_layer_focus.isChecked(),
            findings=self.chk_layer_findings.isChecked(),
        )

    def _on_trigger_evidence_fusion(self):
        self._trigger_evidence_fusion()

    def _trigger_evidence_fusion(self):
        if self._fusion_worker and self._fusion_worker.isRunning():
            return
        if not self._current_snapshot or not self._current_snapshot.elements:
            return

        hwnd = self._target_window.get("handle") if self._target_window else None
        title = self._target_window.get("title", "Active Window") if self._target_window else "Active Window"
        bounds = self._target_window.get("bounds") if self._target_window else None
        kb_obs = self._current_traversal_result.observations if self._current_traversal_result else None

        self.btn_capture_evidence.setEnabled(False)
        self.lbl_status.setText("Fusing UIA + Visual + Focus evidence in background...")

        self._fusion_worker = EvidenceFusionWorker(
            window_handle=hwnd,
            window_title=title,
            uia_elements=self._current_snapshot.elements,
            window_bounds=bounds,
            keyboard_observations=kb_obs,
            existing_screenshot=self._current_screenshot,
        )
        self._fusion_worker.finished.connect(self._on_fusion_finished)
        self._fusion_worker.error.connect(self._on_fusion_error)
        self._fusion_worker.start()

    def _on_fusion_finished(self, result: EvidenceFusionResult, screenshot: Optional[Image.Image]):
        self.btn_capture_evidence.setEnabled(True)
        self._current_fusion_result = result
        if screenshot is not None and self._current_screenshot is None:
            self._current_screenshot = screenshot
            self.visual_canvas.set_screenshot(screenshot)

        # Update evidence summary badges
        sw = screenshot.width if screenshot else 0
        sh = screenshot.height if screenshot else 0
        shot_text = f"SHOT: {sw}x{sh}" if sw > 0 else "SHOT: UNAVAILABLE"
        self.badge_shot_status.setText(shot_text)
        self.badge_ev_matched.setText(f"{result.matched_count} MATCHED")
        self.badge_ev_unmatched.setText(f"{result.unmatched_uia_count} UNMATCHED")
        self.badge_ev_conflicts.setText(f"{result.conflicts_count} CONFLICTS")
        self.badge_rep_conflicts.setText(f"{result.conflicts_count} CONFLICTS")
        self.badge_ev_focus_map.setText(f"FOCUS: {result.focus_mapping_status}")

        # Map layer bounding boxes to screenshot coordinate space
        win_bounds = self._target_window.get("bounds") if self._target_window else None
        shot_size = (screenshot.width, screenshot.height) if screenshot else (1280, 720)

        uia_boxes = []
        for el in result.uia_elements:
            if el.bounds:
                mapped = uia_bounds_to_screenshot_bounds(el.bounds, win_bounds, shot_size)
                if mapped:
                    uia_boxes.append({"bounds": mapped, "name": el.name, "type": el.control_type})

        ocr_boxes = []
        for ve in result.visual_elements:
            if ve.bounds:
                ocr_boxes.append({
                    "bounds": ve.bounds,
                    "text": ve.text,
                    "conf": ve.confidence,
                    "suspicious": ve.is_suspicious,
                })

        match_boxes = []
        for m in result.matched_elements:
            b = m.visual_element.bounds or (
                uia_bounds_to_screenshot_bounds(m.uia_element.bounds, win_bounds, shot_size)
                if m.uia_element.bounds else None
            )
            if b:
                match_boxes.append({
                    "bounds": b,
                    "score": m.match_score,
                    "class": m.match_classification,
                    "label": f"{m.uia_element.name or m.visual_element.text} ({int(m.match_score * 100)}%)",
                })

        finding_boxes = []
        if self._current_snapshot and self._current_snapshot.findings:
            for f in self._current_snapshot.findings:
                if f.affected_element_id and self._current_snapshot.ui_tree:
                    fel = self._current_snapshot.ui_tree.search_by_id(f.affected_element_id)
                    if fel and fel.bounds:
                        fb = uia_bounds_to_screenshot_bounds(fel.bounds, win_bounds, shot_size)
                        if fb:
                            finding_boxes.append({
                                "bounds": fb,
                                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                                "title": f.title,
                            })

        self.visual_canvas.set_evidence_layers(
            uia_boxes=uia_boxes,
            ocr_boxes=ocr_boxes,
            matches=match_boxes,
            finding_boxes=finding_boxes,
        )

        self.lbl_status.setText(
            f"Evidence fusion complete: {result.matched_count} matched, "
            f"{result.unmatched_uia_count} unmatched UIA, {result.conflicts_count} conflicts."
        )

    def _on_fusion_error(self, err: str):
        self.btn_capture_evidence.setEnabled(True)
        self.lbl_status.setText(f"Visual evidence fusion error: {err}")

    def _update_evidence_inspector(self, el: Optional[UIElementModel] = None, finding: Optional[AccessibilityFinding] = None):
        """Displays grounded multimodal correlation details in Evidence Inspector."""
        if not self._current_fusion_result:
            if el:
                self.txt_inspector_details.setPlainText(
                    f"[UIA_MEASURED] Element: '{el.name or '<Unnamed>'}' | Type: {el.control_type} | Bounds: {el.bounds}\n"
                    f"[UIA_MEASURED] Evidence fusion not yet executed."
                )
            return

        target_el = el
        if target_el is None and finding and finding.affected_element_id and self._current_snapshot and self._current_snapshot.ui_tree:
            target_el = self._current_snapshot.ui_tree.search_by_id(finding.affected_element_id)

        if not target_el:
            self.txt_inspector_details.setPlainText("No element associated with current selection.")
            return

        # Find match for this element
        m = next(
            (match for match in self._current_fusion_result.matched_elements
             if match.uia_element.element_id == target_el.element_id),
            None
        )

        lines = [
            f"[UIA_MEASURED] Element: '{target_el.name or '<Unnamed>'}' | ControlType: {target_el.control_type} | Bounds: {target_el.bounds}"
        ]

        if m:
            lines.append(
                f"[OCR_DETECTED] Visual Text: '{m.visual_element.text}' | Bounds: {m.visual_element.bounds} | OCR Conf: {m.visual_element.confidence:.2f}"
            )
            lines.append(
                f"[FUSED] Match: {m.match_classification} ({int(m.match_score * 100)}%) | Geo: {m.geometry_score:.2f} | Text: {m.text_score:.2f} | Prox: {m.proximity_score:.2f}"
            )
            if m.discrepancy_detected:
                lines.append(f"[DISCREPANCY] ⚠️ {m.discrepancy_details}")
            if m.visual_element.is_suspicious:
                lines.append("[ADVERSARIAL_INERT] ⚠️ Visual text flagged as suspicious; preserved inertly without execution.")
        else:
            lines.append("[UIA_MEASURED] Visual Correlation: No visual match (Unmatched UIA element).")

        if finding:
            lines.append(f"[FINDING_CORRELATION] Finding: '{finding.title}' | Severity: {finding.severity} | Source: {finding.source}")

        self.txt_inspector_details.setPlainText("\n".join(lines))

    def _populate_tree(self, elements: List[UIElementModel]):
        self.tree_widget.clear()
        elem_items: Dict[str, QTreeWidgetItem] = {}

        for el in elements:
            eid = el.element_id or el.id
            display_name = el.name if el.name else "<No Accessible Name>"
            ctype = el.control_type or "Not available"
            aid = el.automation_id or "Not available"

            item = QTreeWidgetItem([display_name, ctype, aid])
            item.setData(0, Qt.ItemDataRole.UserRole, el)

            if not el.name:
                item.setForeground(0, Qt.GlobalColor.yellow)

            elem_items[eid] = item

            pid = el.parent_id
            if pid and pid in elem_items:
                elem_items[pid].addChild(item)
            else:
                self.tree_widget.addTopLevelItem(item)

        self.tree_widget.expandAll()

    def _populate_findings_table(self, findings: List[AccessibilityFinding]):
        self.findings_table.setRowCount(len(findings))
        for row, f in enumerate(findings):
            # Severity
            sev_str = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            item_sev = QTableWidgetItem(sev_str)
            if sev_str == "HIGH":
                item_sev.setForeground(QColor("#FCA5A5"))
            elif sev_str == "MEDIUM":
                item_sev.setForeground(QColor("#FDE68A"))
            elif sev_str == "LOW":
                item_sev.setForeground(QColor("#A7F3D0"))
            else:
                item_sev.setForeground(QColor(TEXT_SECONDARY))

            item_title = QTableWidgetItem(f.title)
            item_conf = QTableWidgetItem(f"{f.confidence * 100:.0f}%")
            item_src = QTableWidgetItem(f.source)

            for it in [item_sev, item_conf, item_src]:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_title.setData(Qt.ItemDataRole.UserRole, f)

            self.findings_table.setItem(row, 0, item_sev)
            self.findings_table.setItem(row, 1, item_title)
            self.findings_table.setItem(row, 2, item_conf)
            self.findings_table.setItem(row, 3, item_src)

        if findings:
            self.findings_table.selectRow(0)

    def _on_finding_table_selection(self):
        selected_rows = self.findings_table.selectedItems()
        if not selected_rows:
            return
        row = self.findings_table.currentRow()
        title_item = self.findings_table.item(row, 1)
        if not title_item:
            return
        finding: Optional[AccessibilityFinding] = title_item.data(Qt.ItemDataRole.UserRole)
        if not finding:
            return

        self._display_finding_detail(finding)
        self._update_evidence_inspector(finding=finding)

        # Highlight affected element on screenshot if bounds exist
        if finding.affected_element_id and self._current_snapshot and self._current_snapshot.ui_tree:
            el = self._current_snapshot.ui_tree.search_by_id(finding.affected_element_id)
            if el and el.bounds:
                self._highlight_element_bounds(el.bounds)
            else:
                self.visual_canvas.highlight_box(None)
                self.lbl_visual_map_status.setText("Element bounds not available.")
        else:
            self.visual_canvas.highlight_box(None)
            self.lbl_visual_map_status.setText("")

    def _on_tree_element_selected(self, current: Optional[QTreeWidgetItem], previous: Optional[QTreeWidgetItem]):
        if not current:
            return
        el: Optional[UIElementModel] = current.data(0, Qt.ItemDataRole.UserRole)
        if el:
            self._update_evidence_inspector(el=el)
            if el.bounds:
                self._highlight_element_bounds(el.bounds)
            else:
                self.visual_canvas.highlight_box(None)
                self.lbl_visual_map_status.setText("Element bounds not available.")
        else:
            self.visual_canvas.highlight_box(None)

    def _highlight_element_bounds(self, bounds: List[int]):
        if not self._current_screenshot:
            self.lbl_visual_map_status.setText("Screenshot unavailable for visual mapping.")
            return

        shot_size = self._current_screenshot.size
        win_bounds = self._target_window.get("bounds") if self._target_window else None

        mapped_box, msg = coordinate_mapper.map_bounds_to_screenshot(bounds, win_bounds, shot_size)
        if mapped_box is not None:
            self.visual_canvas.highlight_box(mapped_box)
            self.lbl_visual_map_status.setText("")
        else:
            self.visual_canvas.highlight_box(None)
            self.lbl_visual_map_status.setText(msg)

    def _display_finding_detail(self, finding: AccessibilityFinding):
        self._current_finding = finding
        self._current_reasoning_result = None

        self.lbl_finding_title.setText(finding.title)

        sev_str = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        self.badge_finding_sev.setText(sev_str)
        self.badge_finding_conf.setText(f"Confidence: {finding.confidence * 100:.0f}%")

        self.txt_obs.setPlainText(finding.observation or finding.title)

        # Build bulleted evidence list
        evidence_lines = []
        for ev in finding.evidence:
            evidence_lines.append(f"• {str(ev)}")
        self.txt_evidence.setPlainText("\n".join(evidence_lines) if evidence_lines else "No specific evidence recorded.")

        self.txt_impact.setPlainText(finding.impact or "Assistive technologies rely on this metadata to serve users.")
        self.txt_rec.setPlainText(finding.recommendation or "Review and correct the control properties.")

        self.lbl_human_verif.setText(
            "Requires Human Review: YES (Contextual validation required)"
            if finding.human_verification_required else "Requires Human Review: No (Deterministic API result)"
        )
        self.lbl_source.setText(f"Source: {finding.source}")

        # Enable AI action buttons
        self.btn_explain_finding.setEnabled(True)
        self.btn_recommend_fix.setEnabled(True)
        self.btn_copy_guidance.setEnabled(False)

        # Reset AI section state
        self.lbl_ai_status.setText("Click 'Explain Finding' or 'Recommend Fix' to generate evidence-grounded guidance.")
        self.txt_ai_summary.clear()
        self.txt_ai_confidence_exp.clear()
        self.txt_ai_remediation.clear()
        for chk in self.verification_checkboxes:
            chk.setChecked(False)

    def _on_explain_finding(self):
        if not self._current_finding:
            return
        self._run_reasoning_worker(mode="reasoning")

    def _on_recommend_fix(self):
        if not self._current_finding:
            return
        self._run_reasoning_worker(mode="remediation")

    def _run_reasoning_worker(self, mode: str):
        finding = self._current_finding
        if not finding:
            return

        element = None
        if finding.affected_element_id and self._current_snapshot and self._current_snapshot.ui_tree:
            element = self._current_snapshot.ui_tree.search_by_id(finding.affected_element_id)

        self.btn_explain_finding.setEnabled(False)
        self.btn_recommend_fix.setEnabled(False)
        self.lbl_ai_status.setText("Executing local reasoning on CPU (Deterministic Knowledge Engine)...")

        self._reasoning_worker = ReasoningWorker(
            finding=finding,
            element=element,
            evidence=finding.evidence,
            mode=mode,
        )
        self._reasoning_worker.finished.connect(self._on_reasoning_finished)
        self._reasoning_worker.error.connect(self._on_reasoning_error)
        self._reasoning_worker.start()

    def _on_reasoning_finished(self, result: ReasoningResult):
        self.btn_explain_finding.setEnabled(True)
        self.btn_recommend_fix.setEnabled(True)
        self.btn_copy_guidance.setEnabled(True)
        self._current_reasoning_result = result
        self._reasoning_results[result.finding_id] = result

        self.lbl_ai_status.setText(
            f"Reasoning complete via {result.generated_by} ({result.runtime})."
        )
        self.txt_ai_summary.setPlainText(
            f"{result.summary}\n\nWHY THIS MATTERS:\n{result.why_it_matters}"
        )
        self.txt_ai_confidence_exp.setPlainText(result.confidence_explanation)

        dev_steps_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(result.developer_actions))
        full_rem = f"{result.remediation}\n\nDeveloper Action Steps:\n{dev_steps_text}"
        if result.limitations:
            full_rem += f"\n\nContext & Limitations:\n{result.limitations}"
        self.txt_ai_remediation.setPlainText(full_rem)

    def _on_reasoning_error(self, err_msg: str):
        self.btn_explain_finding.setEnabled(True)
        self.btn_recommend_fix.setEnabled(True)
        self.lbl_ai_status.setText(
            "Reasoning could not be completed. The original deterministic finding remains available."
        )
        self.txt_ai_summary.setPlainText(err_msg)

    def _on_copy_guidance(self):
        if not self._current_reasoning_result:
            return
        text = self._current_reasoning_result.to_developer_guidance_text()
        QGuiApplication.clipboard().setText(text)
        self.lbl_ai_status.setText("✓ Developer remediation guidance copied to clipboard.")

    # --- Phase 5: Keyboard Navigation Event Handlers ---

    def _on_start_keyboard_audit(self):
        """Validates target window, prompts explicit confirmation, and launches KeyboardAuditWorker."""
        target_title = "Selected Application"
        target_hwnd = None
        if self._target_window:
            target_title = self._target_window.get("title", "Selected Application")
            target_hwnd = self._target_window.get("handle")

        # Explicit Safety Confirmation Dialog (Mandatory Phase 5 requirement)
        confirm_dlg = KeyboardAuditConfirmationDialog(target_title=target_title, parent=self)
        if confirm_dlg.exec() != QDialog.DialogCode.Accepted:
            self.lbl_kb_status.setText("Keyboard audit cancelled by user.")
            return

        direction = "reverse" if self.rb_reverse.isChecked() else "forward"
        max_steps = self.spin_max_steps.value()
        delay_ms = self.spin_delay.value()
        tree = self._current_snapshot.ui_tree if self._current_snapshot else None

        # Reset traversal table
        self.table_traversal.setRowCount(0)
        self.btn_start_kb_audit.setEnabled(False)
        self.btn_stop_kb_audit.setEnabled(True)
        self.lbl_kb_status.setText(f"Auditing keyboard navigation ({direction.upper()})...")

        self._keyboard_worker = KeyboardAuditWorker(
            target_hwnd=target_hwnd,
            target_window_title=target_title,
            direction=direction,
            max_steps=max_steps,
            delay_ms=delay_ms,
            tree=tree,
            parent=self,
        )
        self._keyboard_worker.started_audit.connect(self._on_keyboard_started)
        self._keyboard_worker.observation_recorded.connect(self._on_keyboard_step)
        self._keyboard_worker.progress.connect(self._on_keyboard_progress)
        self._keyboard_worker.audit_finished.connect(self._on_keyboard_finished)
        self._keyboard_worker.cancelled.connect(self._on_keyboard_cancelled)
        self._keyboard_worker.error.connect(self._on_keyboard_error)
        self._keyboard_worker.start()

    def _on_stop_keyboard_audit(self):
        """Immediately stops the keyboard audit worker."""
        if self._keyboard_worker:
            self.lbl_kb_status.setText("Stopping keyboard audit...")
            self._keyboard_worker.cancel()
        self.btn_stop_kb_audit.setEnabled(False)

    def _on_keyboard_started(self):
        self.lbl_kb_status.setText("Traversing interactive controls via keyboard...")

    def _on_keyboard_step(self, obs: FocusObservation):
        """Appends step record to live traversal table."""
        row = self.table_traversal.rowCount()
        self.table_traversal.insertRow(row)

        step_item = QTableWidgetItem(f"{obs.traversal_index:02d}")
        step_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_traversal.setItem(row, 0, step_item)

        name_item = QTableWidgetItem(obs.element_name or "<Unnamed>")
        self.table_traversal.setItem(row, 1, name_item)

        type_item = QTableWidgetItem(obs.control_type or "Unknown")
        self.table_traversal.setItem(row, 2, type_item)

        focus_item = QTableWidgetItem("✓" if obs.is_focused else "—")
        focus_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        focus_item.setForeground(QColor(167, 243, 208) if obs.is_focused else QColor(253, 230, 138))
        self.table_traversal.setItem(row, 3, focus_item)

        time_str = datetime.fromtimestamp(obs.timestamp, timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        time_item = QTableWidgetItem(time_str)
        self.table_traversal.setItem(row, 4, time_item)

        self.table_traversal.scrollToBottom()

    def _on_keyboard_progress(self, current: int, max_steps: int):
        self.lbl_kb_status.setText(f"Auditing keyboard navigation: step {current}/{max_steps}...")

    def _on_keyboard_finished(self, result: FocusTraversalResult, focus_path: FocusPath):
        self._current_traversal_result = result
        self._current_focus_path = focus_path

        self.btn_start_kb_audit.setEnabled(True)
        self.btn_stop_kb_audit.setEnabled(False)

        # Update metrics badges
        self.badge_kb_steps.setText(f"{len(result.observations)} STEPS")
        self.badge_kb_unique.setText(f"{result.unique_elements} UNIQUE")
        self.badge_kb_repeated.setText(f"{result.repeated_elements} REPEATED")
        self.badge_kb_trap.setText("TRAP: YES" if result.focus_trap_detected else "TRAP: NO")
        self.badge_kb_trap.setStyleSheet(
            f"background-color: {'#7F1D1D' if result.focus_trap_detected else '#064E3B'}; color: {'#FECACA' if result.focus_trap_detected else '#A7F3D0'}; border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
        )
        self.badge_kb_unreached.setText(f"{len(result.unreachable_elements)} UNREACHED")
        self.badge_kb_human.setText("HUMAN REVIEW: REQUIRED")

        status_text = "Keyboard audit complete."
        if result.warnings:
            status_text += f" ({result.warnings[0]})"
        self.lbl_kb_status.setText(status_text)

        # Populate Focus Path text and visual graph
        lines = [
            f"=== FOCUS PATH: {result.direction.upper()} TRAVERSAL ===",
            f"Target: {result.target_window}",
            f"Total Nodes: {len(focus_path.nodes)} | Unique Elements: {result.unique_elements} | Transitions: {len(focus_path.transitions)}",
            f"Loop Detected: {'YES' if focus_path.has_loops else 'NO'} | Potential Trap: {'YES' if focus_path.has_trap else 'NO'}",
            "",
            "TRAVERSAL SEQUENCE:"
        ]
        for node in focus_path.nodes:
            lines.append(f"  {node.index:02d} → [{node.control_type}] \"{node.name}\" (ID: {node.automation_id or 'none'})")

        if focus_path.transitions:
            lines.append("")
            lines.append("TRANSITIONS:")
            for t in focus_path.transitions:
                flag = " [REPEATED]" if t.is_repeated else ""
                lines.append(f"  Step {t.from_index} → Step {t.to_index}: \"{t.from_name}\" -> \"{t.to_name}\" (count={t.count}){flag}")

        self.txt_focus_path.setPlainText("\n".join(lines))

        # Check visual coordinate mapping
        segments = focus_path.get_visual_segments()
        if segments and self._current_screenshot is not None:
            self.visual_canvas.set_focus_path_segments(segments)
            self.lbl_focus_path_mapping.setText(f"✓ Visual focus mapping active ({len(segments)} segments rendered on canvas).")
            self.lbl_focus_path_mapping.setStyleSheet(f"color: {ACCENT_GREEN}; font-size: 11px;")
        else:
            self.visual_canvas.set_focus_path_segments(None)
            self.lbl_focus_path_mapping.setText("Visual focus mapping unavailable; traversal data remains available.")
            self.lbl_focus_path_mapping.setStyleSheet(f"color: {ACCENT_AMBER}; font-size: 11px;")

        # Integrate newly discovered keyboard findings into the findings table
        if result.findings:
            for f in result.findings:
                # Add to snapshot findings if snapshot exists
                if self._current_snapshot:
                    self._current_snapshot.findings.append(f)
                # Add row to findings table
                row = self.findings_table.rowCount()
                self.findings_table.insertRow(row)

                sev_val = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
                sev_item = QTableWidgetItem(sev_val)
                sev_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                color_map = {
                    "CRITICAL": QColor(248, 113, 113),
                    "HIGH": QColor(253, 230, 138),
                    "MEDIUM": QColor(147, 197, 253),
                    "LOW": QColor(167, 243, 208),
                    "INFO": QColor(148, 163, 184),
                }
                sev_item.setForeground(color_map.get(sev_val, QColor(255, 255, 255)))
                self.findings_table.setItem(row, 0, sev_item)

                title_item = QTableWidgetItem(f.title)
                title_item.setData(Qt.ItemDataRole.UserRole, f)
                self.findings_table.setItem(row, 1, title_item)

                conf_item = QTableWidgetItem(f"{f.confidence * 100:.0f}%")
                conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.findings_table.setItem(row, 2, conf_item)

                src_item = QTableWidgetItem(f.source)
                self.findings_table.setItem(row, 3, src_item)

            # Update findings badge counts
            self.badge_total.setText(f"{self.findings_table.rowCount()} TOTAL")

        # Re-trigger evidence fusion with newly recorded keyboard observations
        self._trigger_evidence_fusion()

    def _on_keyboard_cancelled(self, reason: str):
        self.lbl_kb_status.setText(f"Audit cancelled: {reason}")
        self.btn_start_kb_audit.setEnabled(True)
        self.btn_stop_kb_audit.setEnabled(False)

    def _on_keyboard_error(self, err_msg: str):
        self.lbl_kb_status.setText(f"Keyboard audit error: {err_msg}")
        self.btn_start_kb_audit.setEnabled(True)
        self.btn_stop_kb_audit.setEnabled(False)

    # ========================================================================
    # Phase 7: Report Generation, Verification, & Multi-Format Export Handlers
    # ========================================================================

    def _on_generate_report_clicked(self):
        if not self._current_snapshot:
            QMessageBox.information(
                self,
                "No Active Audit Snapshot",
                "Please inspect an application interface first before generating a report."
            )
            return

        # Prepare metadata for pre-export preview
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        rep_id = f"accesslens-report-{now_str}"
        findings = self._current_snapshot.findings
        high_cnt = sum(1 for f in findings if getattr(f.severity, "value", f.severity) in ("CRITICAL", "HIGH", "1", "2"))
        med_cnt = sum(1 for f in findings if getattr(f.severity, "value", f.severity) in ("MEDIUM", "3"))
        low_cnt = sum(1 for f in findings if getattr(f.severity, "value", f.severity) in ("LOW", "INFO", "4", "5"))

        # Check for sensitive data
        has_sensitive = False
        for f in findings:
            if sensitive_data_detector.contains_sensitive_content(f.title) or sensitive_data_detector.contains_sensitive_content(f.observation):
                has_sensitive = True
                break

        preview_meta = {
            "report_id": rep_id,
            "application": self._current_snapshot.application_name or "Target Application",
            "scan_time": self._current_snapshot.timestamp,
            "findings_count": len(findings),
            "severity_dist": f"{high_cnt} High/Crit, {med_cnt} Med, {low_cnt} Low",
            "evidence_count": len(self._current_snapshot.elements),
            "human_review_count": sum(1 for f in findings if f.human_verification_required),
            "privacy_mode": self.combo_privacy_mode.currentText(),
            "hardware_status": "AMD CPU Fallback (Snapdragon Validation Pending)",
            "sensitive_detected": has_sensitive,
        }

        dlg = ReportPreviewDialog(preview_meta, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._start_report_generation(rep_id)

    def _start_report_generation(self, custom_report_id: Optional[str] = None):
        if self._report_worker and self._report_worker.isRunning():
            return
        if not self._current_snapshot:
            return

        priv_map = {
            "Findings Only": "findings_only",
            "Redacted": "redacted",
            "Local Full": "local_full",
        }
        img_map = {
            "Findings Only": "findings_only",
            "None": "none",
            "All Evidence": "all_evidence",
        }

        privacy_mode = priv_map.get(self.combo_privacy_mode.currentText(), "findings_only")
        image_mode = img_map.get(self.combo_image_mode.currentText(), "findings_only")

        self.btn_generate_report.setEnabled(False)
        self.lbl_report_status.setText("Generating report in background...")

        raw_visuals = [m.visual_element for m in self._current_fusion_result.matched_elements] if self._current_fusion_result else None

        self._report_worker = ReportWorker(
            application_name=self._current_snapshot.application_name,
            target_window=self._current_snapshot.window_title,
            findings=self._current_snapshot.findings,
            ui_elements=self._current_snapshot.elements,
            visual_elements=raw_visuals,
            fusion_result=self._current_fusion_result,
            focus_result=self._current_traversal_result,
            reasoning_results=self._reasoning_results,
            privacy_mode=privacy_mode,
            evidence_image_mode=image_mode,
            export_formats=["json", "md", "html"],
            parent=self,
        )
        self._report_worker.progress.connect(self._on_report_progress)
        self._report_worker.finished.connect(self._on_report_finished)
        self._report_worker.error.connect(self._on_report_error)
        self._report_worker.start()

    def _on_report_progress(self, msg: str):
        self.lbl_report_status.setText(msg)

    def _on_report_finished(self, report: AuditReport, export_paths: Dict[str, str]):
        self._latest_report = report
        self._latest_export_paths = export_paths
        self.btn_generate_report.setEnabled(True)
        self.btn_export_json.setEnabled(True)
        self.btn_export_md.setEnabled(True)
        self.btn_export_html.setEnabled(True)
        self.btn_open_folder.setEnabled(True)

        self.lbl_report_status.setText(f"✓ Report '{report.report_id}' generated ({len(export_paths)} formats).")
        QMessageBox.information(
            self,
            "Report Generated Successfully",
            f"Accessibility audit report generated successfully!\n\n"
            f"Report ID: {report.report_id}\n"
            f"SHA-256 Digest: {report.evidence_digest[:16]}...\n\n"
            f"Export Formats: JSON, Markdown, HTML\n"
            f"Destination: reports/generated/{report.report_id}/"
        )

    def _on_report_error(self, err_msg: str):
        self.btn_generate_report.setEnabled(True)
        self.lbl_report_status.setText(f"Report error: {err_msg}")
        QMessageBox.warning(self, "Report Generation Error", f"Failed to generate report:\n{err_msg}")

    def _on_export_format(self, fmt: str):
        if not self._latest_report or fmt not in self._latest_export_paths:
            self._start_report_generation()
            return

        file_path = self._latest_export_paths.get(fmt)
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception:
                QMessageBox.information(self, "Export Location", f"Report file saved at:\n{file_path}")

    def _on_open_report_folder(self):
        dest_dir = None
        if self._latest_export_paths:
            first_path = next(iter(self._latest_export_paths.values()))
            dest_dir = os.path.dirname(first_path)
        if not dest_dir or not os.path.exists(dest_dir):
            dest_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "reports",
                "generated",
            )
        os.makedirs(dest_dir, exist_ok=True)
        try:
            os.startfile(dest_dir)
        except Exception:
            QMessageBox.information(self, "Report Directory", f"Reports are stored at:\n{dest_dir}")

    def cleanup(self):
        """Cancels and safely terminates any active background worker threads."""
        for worker in [self._worker, self._reasoning_worker, self._fusion_worker, self._report_worker]:
            if worker and worker.isRunning():
                try:
                    if hasattr(worker, "cancel"):
                        worker.cancel()
                    worker.terminate()
                    worker.wait(300)
                except Exception:
                    pass
        if self._keyboard_worker and self._keyboard_worker.isRunning():
            try:
                self._keyboard_worker.cancel()
                self._keyboard_worker.wait(300)
            except Exception:
                pass



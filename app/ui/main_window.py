"""Main application window for AccessLens AI.

Provides the unified on-device accessibility inspection and remediation platform:
CAPTURE / SELECT -> EXTRACT (UIA + OCR) -> RULES & EVIDENCE -> REMEDIATION & VOICE
"""

import os
import subprocess
import sys
from typing import Optional
from PIL import Image

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QScrollArea,
    QSplitter, QTabWidget, QTextEdit, QVBoxLayout, QWidget
)

from app.ui.components import (
    ACCENT_AMBER, ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN,
    ACCENT_RED, BG_CARD, BG_CARD_BORDER, BG_PRIMARY, BG_SURFACE,
    AccessibleButton, CardWidget, DARK_STYLESHEET,
    ImagePreviewWidget, StatusBadge, TEXT_PRIMARY, TEXT_SECONDARY
)
from app.ui.accessibility_audit_view import AccessibilityAuditView
from app.ui.element_inspector_view import ElementInspectorView
from app.ui.findings_view import FindingsView
from app.ui.hardware_view import HardwareView
from app.ui.history_view import HistoryView
from app.ui.keyboard_view import KeyboardAuditView
from app.ui.performance_view import PerformanceView
from app.ui.reports_view import ReportsView
from app.workers.analysis_worker import AnalysisWorker

from accessibility.element_model import InterfaceSnapshot
from accessibility.ui_automation import ui_automation
from accessibility.ui_tree import UITree
from ai.model_registry import model_registry
from audio.text_to_speech import tts_engine
from hardware.hardware_detector import hardware_detector
from privacy.privacy_manager import privacy_manager
from storage.database import database_manager
from vision.image_utils import is_supported_image, load_image, pil_to_qpixmap
from vision.screen_capture import screen_capturer


class MainWindow(QMainWindow):
    """AccessLens AI Main Desktop Application Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AccessLens AI — See the interface. Understand the barriers. Fix them locally.")
        self.resize(1220, 840)
        self.setMinimumSize(950, 680)
        self.setStyleSheet(DARK_STYLESHEET)

        self._current_image_path: Optional[str] = None
        self._current_pil_image: Optional[Image.Image] = None
        self._current_scene_result = None
        self._current_snapshot: Optional[InterfaceSnapshot] = None
        self._worker: Optional[AnalysisWorker] = None
        self._demo_app_proc: Optional[subprocess.Popen] = None

        self._setup_menus_and_shortcuts()
        self._init_ui()

    def _setup_menus_and_shortcuts(self):
        open_action = QAction("Open Image", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_image_dialog)
        self.addAction(open_action)

        capture_action = QAction("Capture Screen", self)
        capture_action.setShortcut(QKeySequence("Ctrl+S"))
        capture_action.triggered.connect(self.capture_screen_action)
        self.addAction(capture_action)

        speak_action = QAction("Read Aloud", self)
        speak_action.setShortcut(QKeySequence("Space"))
        speak_action.triggered.connect(self.read_aloud)
        self.addAction(speak_action)

        stop_action = QAction("Stop Speech", self)
        stop_action.setShortcut(QKeySequence("Escape"))
        stop_action.triggered.connect(self.stop_speech)
        self.addAction(stop_action)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 16)
        main_layout.setSpacing(10)

        # 1. Header Banner
        header_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("ACCESSLENS AI")
        title_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; letter-spacing: 1px;")

        tagline_lbl = QLabel("See the interface. Understand the barriers. Fix them locally. — Qualcomm Snapdragon AI Lab 2026")
        tagline_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        tagline_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(tagline_lbl)
        header_bar.addLayout(title_box)

        header_bar.addStretch()

        # Engine Badge
        profile = hardware_detector.inspect()
        if profile.is_snapdragon and profile.is_npu_available:
            self.engine_badge = StatusBadge("SNAPDRAGON NPU", bg_color="#064E3B", text_color=ACCENT_GREEN)
        elif profile.is_snapdragon:
            self.engine_badge = StatusBadge("SNAPDRAGON CPU", bg_color="#78350F", text_color=ACCENT_AMBER)
        else:
            self.engine_badge = StatusBadge("CPU PROCESSING", bg_color="#1E293B", text_color="#38BDF8")
        header_bar.addWidget(self.engine_badge)

        self.privacy_badge = StatusBadge("LOCAL ONLY", bg_color="#1E293B", text_color=ACCENT_GREEN)
        header_bar.addWidget(self.privacy_badge)

        main_layout.addLayout(header_bar)

        # 2. Main Tabs Navigation
        self.tabs = QTabWidget()
        self.dashboard_tab = self._create_dashboard_tab()
        self.accessibility_audit_tab = AccessibilityAuditView()
        self.inspector_tab = ElementInspectorView()
        self.keyboard_tab = KeyboardAuditView()
        self.findings_tab = FindingsView()
        self.reports_tab = ReportsView()
        self.hardware_tab = HardwareView()
        self.performance_tab = PerformanceView()
        self.history_tab = HistoryView()
        self.models_tab = self._create_models_tab()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.accessibility_audit_tab, "Accessibility Audit")
        self.tabs.addTab(self.inspector_tab, "Element Inspector")
        self.tabs.addTab(self.keyboard_tab, "Keyboard Audit")
        self.tabs.addTab(self.findings_tab, "Findings & Evidence")
        self.tabs.addTab(self.reports_tab, "Reports & Redaction")
        self.tabs.addTab(self.hardware_tab, "Hardware Diagnostics")
        self.tabs.addTab(self.performance_tab, "Performance Benchmark")
        self.tabs.addTab(self.history_tab, "History")
        self.tabs.addTab(self.models_tab, "Models & Privacy")

        main_layout.addWidget(self.tabs)

        # 3. Bottom Status Bar
        status_bar = QHBoxLayout()
        self.status_msg_lbl = QLabel("Ready. Capture an interface or select a synthetic test app to begin accessibility audit.")
        self.status_msg_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        status_bar.addWidget(self.status_msg_lbl)

        status_bar.addStretch()

        host_lbl = QLabel(f"Host: {profile.cpu_model} ({profile.architecture}) | AI: {profile.ai_backend_label}")
        host_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        status_bar.addWidget(host_lbl)

        main_layout.addLayout(status_bar)

    def _create_dashboard_tab(self) -> QWidget:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(12, 12, 12, 12)
        tab_layout.setSpacing(10)

        # Action Control Bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        self.btn_capture = AccessibleButton("📸 Capture Interface (Ctrl+S)", primary=True, accent_color=ACCENT_BLUE)
        self.btn_capture.clicked.connect(self.capture_screen_action)
        action_bar.addWidget(self.btn_capture)

        self.btn_open = AccessibleButton("📂 Open Screenshot (Ctrl+O)", primary=False)
        self.btn_open.clicked.connect(self.open_image_dialog)
        action_bar.addWidget(self.btn_open)

        self.btn_demo_app = AccessibleButton("🚀 Launch Synthetic Demo App", primary=False)
        self.btn_demo_app.setStyleSheet(f"""
            QPushButton {{
                background-color: #3730A3;
                color: #C7D2FE;
                border: 1px solid #4F46E5;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #4338CA;
                color: #FFFFFF;
            }}
        """)
        self.btn_demo_app.clicked.connect(self.launch_synthetic_demo_app)
        action_bar.addWidget(self.btn_demo_app)

        # Quick Demo Loader
        demo_box = QHBoxLayout()
        demo_lbl = QLabel("Demo Sample:")
        demo_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600;")
        demo_box.addWidget(demo_lbl)

        self.demo_combo = QComboBox()
        self.demo_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {BG_CARD};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                color: {TEXT_PRIMARY};
                font-weight: 600;
                min-width: 170px;
            }}
        """)
        self.demo_combo.addItems([
            "Select Sample Image...",
            "1. [DEMO / SYNTHETIC TARGET] University Admission Webpage",
            "2. [DEMO / SYNTHETIC TARGET] Restaurant Menu",
            "3. [DEMO / SYNTHETIC TARGET] Product Nutrition Label",
            "4. [DEMO / SYNTHETIC TARGET] Desktop Screenshot"
        ])
        self.demo_combo.currentIndexChanged.connect(self.on_demo_selected)
        demo_box.addWidget(self.demo_combo)
        action_bar.addLayout(demo_box)

        action_bar.addStretch()

        self.chk_boxes = QCheckBox("Show Detected Elements")
        self.chk_boxes.setChecked(True)
        self.chk_boxes.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600;")
        self.chk_boxes.toggled.connect(self.on_toggle_boxes)
        action_bar.addWidget(self.chk_boxes)

        tab_layout.addLayout(action_bar)

        # Progress Bar
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
            QProgressBar::chunk {{
                background-color: {ACCENT_CYAN};
            }}
        """)
        tab_layout.addWidget(self.progress_bar)

        # Severity Summary Metrics Banner
        metrics_card = CardWidget()
        m_layout = QHBoxLayout(metrics_card)
        m_layout.setContentsMargins(12, 6, 12, 6)

        m_title = QLabel("ACCESSIBILITY BARRIER METRICS:")
        m_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        m_title.setStyleSheet(f"color: {TEXT_SECONDARY};")
        m_layout.addWidget(m_title)

        self.badge_crit = StatusBadge("0 CRITICAL", bg_color="#7F1D1D", text_color="#FCA5A5")
        self.badge_high = StatusBadge("0 HIGH", bg_color="#78350F", text_color="#FDE68A")
        self.badge_med = StatusBadge("0 MEDIUM", bg_color="#1E3A8A", text_color="#93C5FD")
        self.badge_low = StatusBadge("0 LOW", bg_color="#064E3B", text_color="#A7F3D0")

        m_layout.addWidget(self.badge_crit)
        m_layout.addWidget(self.badge_high)
        m_layout.addWidget(self.badge_med)
        m_layout.addWidget(self.badge_low)
        m_layout.addStretch()

        self.lbl_audit_time = QLabel("Audit Latency: —")
        self.lbl_audit_time.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        m_layout.addWidget(self.lbl_audit_time)

        tab_layout.addWidget(metrics_card)

        # Main Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # Left: Image Preview
        preview_card = CardWidget()
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(10, 10, 10, 10)

        prev_head = QHBoxLayout()
        prev_title = QLabel("INTERFACE CANVAS & ELEMENT BOUNDS")
        prev_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        prev_title.setStyleSheet(f"color: {TEXT_SECONDARY};")
        prev_head.addWidget(prev_title)
        prev_head.addStretch()
        self.img_info_lbl = QLabel("")
        self.img_info_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        prev_head.addWidget(self.img_info_lbl)
        preview_layout.addLayout(prev_head)

        self.preview_widget = ImagePreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        splitter.addWidget(preview_card)

        # Right: AI Understanding & Voice Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        und_container = QWidget()
        und_layout = QVBoxLayout(und_container)
        und_layout.setSpacing(10)
        und_layout.setContentsMargins(0, 0, 0, 0)

        # Card 1: Interface Scene Understanding
        desc_card = CardWidget()
        desc_layout = QVBoxLayout(desc_card)
        desc_head = QLabel("Interface Scene Understanding")
        desc_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        desc_head.setStyleSheet(f"color: {ACCENT_CYAN};")
        desc_layout.addWidget(desc_head)

        self.txt_description = QTextEdit()
        self.txt_description.setReadOnly(True)
        self.txt_description.setPlaceholderText("Scene description will appear here after analysis...")
        self.txt_description.setMinimumHeight(120)
        desc_layout.addWidget(self.txt_description)
        und_layout.addWidget(desc_card)

        # Card 2: Accessibility Signals
        info_card = CardWidget()
        info_layout = QVBoxLayout(info_card)
        info_head = QLabel("Detected Accessibility Signals & CTAs")
        info_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        info_head.setStyleSheet(f"color: {ACCENT_AMBER};")
        info_layout.addWidget(info_head)

        self.txt_important = QTextEdit()
        self.txt_important.setReadOnly(True)
        self.txt_important.setPlaceholderText("Buttons, form fields, and deadlines...")
        self.txt_important.setMinimumHeight(100)
        info_layout.addWidget(self.txt_important)
        und_layout.addWidget(info_card)

        # Card 3: Detected OCR Text
        ocr_card = CardWidget()
        ocr_layout = QVBoxLayout(ocr_card)
        ocr_head = QLabel("Detected Visible Text (ONNX OCR)")
        ocr_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        ocr_head.setStyleSheet(f"color: {TEXT_PRIMARY};")
        ocr_layout.addWidget(ocr_head)

        self.txt_ocr = QTextEdit()
        self.txt_ocr.setReadOnly(True)
        self.txt_ocr.setPlaceholderText("Extracted text characters...")
        self.txt_ocr.setMinimumHeight(90)
        ocr_layout.addWidget(self.txt_ocr)
        und_layout.addWidget(ocr_card)

        scroll.setWidget(und_container)
        right_layout.addWidget(scroll)

        # Speech Controls Card
        speech_card = CardWidget()
        speech_layout = QVBoxLayout(speech_card)

        sp_btn_box = QHBoxLayout()
        self.btn_speak = AccessibleButton("🔊 READ AUDIT SUMMARY (Space)", primary=True, accent_color=ACCENT_GREEN)
        self.btn_speak.clicked.connect(self.read_aloud)
        sp_btn_box.addWidget(self.btn_speak)

        self.btn_stop = AccessibleButton("⏹ STOP (Esc)", primary=False)
        self.btn_stop.clicked.connect(self.stop_speech)
        sp_btn_box.addWidget(self.btn_stop)
        speech_layout.addLayout(sp_btn_box)

        self.speaking_lbl = QLabel("")
        self.speaking_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speaking_lbl.setStyleSheet(f"color: {ACCENT_GREEN}; font-size: 12px; font-weight: 600;")
        speech_layout.addWidget(self.speaking_lbl)

        right_layout.addWidget(speech_card)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        tab_layout.addWidget(splitter)

        return tab

    def _create_models_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("AI Model Registry & On-Device Privacy Architecture")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Privacy Card
        priv_card = CardWidget()
        p_layout = QVBoxLayout(priv_card)
        p_title = QLabel("ON-DEVICE PRIVACY ASSURANCE")
        p_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        p_title.setStyleSheet(f"color: {ACCENT_GREEN};")
        p_layout.addWidget(p_title)

        p_msg = QLabel(
            f"\"{privacy_manager.privacy_statement}\"\n\n"
            "• Zero Cloud Telemetry: Accessibility evaluation, OCR, and rules run exclusively on-device.\n"
            "• Ephemeral Screenshot Lifecycle: Memory buffers are purged upon session termination.\n"
            "• Metadata-Only Persistence: SQLite logs store timestamps and barrier counts, never raw user pixels."
        )
        p_msg.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; line-height: 1.5;")
        p_layout.addWidget(p_msg)
        layout.addWidget(priv_card)

        # Models List
        models_card = CardWidget()
        m_layout = QVBoxLayout(models_card)
        m_title = QLabel("MODEL REGISTRY & HARDWARE TARGETING")
        m_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        m_title.setStyleSheet(f"color: {ACCENT_CYAN};")
        m_layout.addWidget(m_title)

        for m in model_registry.list_models():
            entry = QLabel(
                f"• {m.name} ({m.format}) — {m.task}\n"
                f"  Runtime: {m.runtime} | License: {m.license} | Target: {m.target}"
            )
            entry.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; margin-bottom: 4px;")
            m_layout.addWidget(entry)

        layout.addWidget(models_card)
        layout.addStretch()
        return tab

    # ================= Actions =================

    def open_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Interface Screenshot for Accessibility Audit",
            "",
            "Supported Images (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*)"
        )
        if file_path:
            self.load_and_audit_image(file_path)

    def capture_screen_action(self):
        self.status_msg_lbl.setText("Capturing active interface screen...")
        try:
            temp_path = screen_capturer.capture_to_temp_file(prefix="accesslens_cap_")
            privacy_manager.register_temp_file(temp_path)
            self.load_and_audit_image(temp_path, is_screen_capture=True)
        except Exception as e:
            QMessageBox.warning(self, "Capture Error", f"Unable to capture interface: {e}")
            self.status_msg_lbl.setText("Screen capture failed.")

    def launch_synthetic_demo_app(self):
        """Launches the synthetic flawed test app for interactive demo audits."""
        demo_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "demo", "accesslens_demo_app.py"
        )
        if os.path.exists(demo_script):
            self._demo_app_proc = subprocess.Popen([sys.executable, demo_script])
            QMessageBox.information(
                self,
                "Synthetic Demo App Launched",
                "The synthetic demonstration target has been launched.\n"
                "Switch to it, then click 'Capture Interface (Ctrl+S)' to audit its known accessibility defects."
            )
        else:
            QMessageBox.warning(self, "File Missing", f"Synthetic demo script not found at {demo_script}")

    def on_demo_selected(self, index: int):
        if index <= 0:
            return
        demo_map = {
            1: "university_admission.png",
            2: "restaurant_menu.png",
            3: "product_label.png",
            4: "desktop_screenshot.png"
        }
        filename = demo_map.get(index)
        if filename:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            path = os.path.join(base_dir, "demo", "samples", filename)
            if os.path.exists(path):
                self.load_and_audit_image(path)

    def on_toggle_boxes(self, checked: bool):
        self.preview_widget.toggle_boxes(checked)

    def load_and_audit_image(self, file_path: str, is_screen_capture: bool = False):
        try:
            pil_img = load_image(file_path)
            self._current_image_path = file_path
            self._current_pil_image = pil_img
            pixmap = pil_to_qpixmap(pil_img)

            self.preview_widget.set_image(pixmap, bounding_boxes=None)
            self.img_info_lbl.setText(f"{pil_img.width}x{pil_img.height} | {os.path.splitext(file_path)[1].upper()}")

            self.txt_description.clear()
            self.txt_important.clear()
            self.txt_ocr.clear()

            self.btn_capture.setEnabled(False)
            self.btn_open.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.status_msg_lbl.setText("Auditing interface across UIA, OCR, and WCAG rules...")

            self._worker = AnalysisWorker(pil_img)
            self._worker.analysis_progress.connect(self.on_analysis_progress)
            self._worker.analysis_finished.connect(
                lambda sres, snap: self.on_audit_finished(sres, snap, file_path, is_screen_capture)
            )
            self._worker.analysis_error.connect(self.on_analysis_error)
            self._worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Error opening interface screenshot: {e}")

    def on_analysis_progress(self, msg: str):
        self.status_msg_lbl.setText(msg)

    def on_audit_finished(self, scene_result, snapshot: InterfaceSnapshot, file_path: str, is_screen_capture: bool):
        self.btn_capture.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._current_scene_result = scene_result
        self._current_snapshot = snapshot

        # 1. Update Dashboard Displays
        self.txt_description.setPlainText(scene_result.description)
        self.txt_important.setPlainText("\n".join(f"• {b}" for b in scene_result.structured_bullets))
        if scene_result.ocr_result:
            self.txt_ocr.setPlainText(scene_result.ocr_result.text)

            # Draw bounding boxes
            pixmap = pil_to_qpixmap(self._current_pil_image)
            boxes = [e.bounding_box_dict for e in snapshot.elements] or scene_result.ocr_result.bounding_boxes
            self.preview_widget.set_image(pixmap, bounding_boxes=boxes)

        # 2. Update Severity Metrics
        self.badge_crit.setText(f"{snapshot.critical_findings_count} CRITICAL")
        self.badge_high.setText(f"{snapshot.high_findings_count} HIGH")
        self.badge_med.setText(f"{snapshot.medium_findings_count} MEDIUM")
        self.badge_low.setText(f"{snapshot.low_findings_count} LOW")
        self.lbl_audit_time.setText(f"Audit Latency: {snapshot.audit_duration_ms:.0f} ms")

        self.status_msg_lbl.setText(
            f"Audit Complete in {snapshot.audit_duration_ms:.0f} ms | Elements: {len(snapshot.elements)} | Barriers: {len(snapshot.findings)}"
        )

        # 3. Propagate to Subsystem Views
        self.inspector_tab.load_elements(snapshot.elements)
        self.keyboard_tab.load_tree(UITree(snapshot.elements))
        self.findings_tab.load_findings(snapshot.findings)
        self.reports_tab.load_snapshot(snapshot)

        # 4. Record to SQLite History
        file_type = "Screenshot" if is_screen_capture else os.path.splitext(file_path)[1].replace(".", "").upper()
        database_manager.add_record(
            file_type=file_type,
            analysis_summary=f"Audit {snapshot.application_name}: {len(snapshot.findings)} barriers ({snapshot.critical_findings_count} critical)",
            processing_backend=snapshot.backend_state,
            word_count=len(snapshot.elements),
            confidence=0.92
        )
        self.history_tab.load_history()

    def on_analysis_error(self, err_msg: str):
        self.btn_capture.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_msg_lbl.setText(f"Audit error: {err_msg}")
        QMessageBox.warning(self, "Audit Notice", f"Audit encountered an issue: {err_msg}")

    # ================= Speech =================

    def read_aloud(self):
        if not self._current_snapshot:
            QMessageBox.information(
                self,
                "No Content",
                "Please capture or open an interface to audit before reading aloud."
            )
            return

        crit = self._current_snapshot.critical_findings_count
        tot = len(self._current_snapshot.findings)
        app = self._current_snapshot.application_name

        script = (
            f"AccessLens AI audit summary for {app}. "
            f"Detected {tot} accessibility barriers, including {crit} critical issues. "
        )
        if self._current_snapshot.findings:
            top_finding = self._current_snapshot.findings[0]
            script += f"Primary finding: {top_finding.title}. Recommendation: {top_finding.recommendation}"

        self.speaking_lbl.setText("🔊 Reading Audit Summary (Playing via Windows SAPI)...")

        def on_done():
            self.speaking_lbl.setText("")

        tts_engine.speak(script, on_finished=on_done)

    def stop_speech(self):
        tts_engine.stop()
        self.speaking_lbl.setText("⏹ Narration Stopped.")
        QTimer.singleShot(1500, lambda: self.speaking_lbl.setText(""))

    def closeEvent(self, event):
        tts_engine.stop()
        privacy_manager.cleanup_all()

        # Safely cancel and wait on main analysis worker
        if self.analysis_worker and self.analysis_worker.isRunning():
            try:
                self.analysis_worker.cancel()
                self.analysis_worker.terminate()
                self.analysis_worker.wait(400)
            except Exception:
                pass

        # Safely clean up tab workers
        if hasattr(self.accessibility_audit_tab, "cleanup"):
            try:
                self.accessibility_audit_tab.cleanup()
            except Exception:
                pass

        if hasattr(self.keyboard_tab, "cleanup"):
            try:
                self.keyboard_tab.cleanup()
            except Exception:
                pass

        if self._demo_app_proc:
            try:
                self._demo_app_proc.terminate()
            except Exception:
                pass
        super().closeEvent(event)


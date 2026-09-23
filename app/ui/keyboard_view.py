"""Keyboard Accessibility Audit view for AccessLens AI.

Audits tab navigation flow, tracks sequential focus steps, detects keyboard traps,
unreachable interactive controls, and redundant focus bouncing.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
    QWidget
)

from accessibility.keyboard_audit import KeyboardAuditReport, keyboard_auditor
from accessibility.ui_tree import UITree
from app.ui.components import (
    ACCENT_AMBER, ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN,
    ACCENT_RED, BG_CARD, BG_CARD_BORDER, CardWidget,
    StatusBadge, TEXT_PRIMARY, TEXT_SECONDARY
)
from audio.text_to_speech import tts_engine


class KeyboardAuditView(QWidget):
    """View managing interactive and simulated keyboard accessibility audits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tree: Optional[UITree] = None
        self._current_report: Optional[KeyboardAuditReport] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Title & Actions
        title_box = QHBoxLayout()
        title_lbl = QLabel("Keyboard & Focus Traversal Audit")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_box.addWidget(title_lbl)
        title_box.addStretch()

        self.btn_run_sim = QPushButton("▶ Run Tab Traversal Audit")
        self.btn_run_sim.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_BLUE};
                color: white;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #1D4ED8;
            }}
        """)
        self.btn_run_sim.clicked.connect(self.run_simulated_audit)
        title_box.addWidget(self.btn_run_sim)

        self.btn_read = QPushButton("🔊 Read Audit Summary")
        self.btn_read.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_GREEN};
                color: white;
                font-weight: 700;
                padding: 8px 14px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #047857;
            }}
        """)
        self.btn_read.clicked.connect(self.read_summary)
        title_box.addWidget(self.btn_read)

        layout.addLayout(title_box)

        # Status Summary Card
        summary_card = CardWidget()
        s_layout = QVBoxLayout(summary_card)
        self.lbl_status = QLabel("Ready. Load an interface or click 'Run Tab Traversal Audit' to evaluate focus sequence.")
        self.lbl_status.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
        s_layout.addWidget(self.lbl_status)
        layout.addWidget(summary_card)

        # Focus Steps Table
        steps_lbl = QLabel("FOCUS SEQUENCING STEPS (TAB TRAVERSAL)")
        steps_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        steps_lbl.setStyleSheet(f"color: {ACCENT_CYAN};")
        layout.addWidget(steps_lbl)

        self.table_steps = QTableWidget(0, 5)
        self.table_steps.setHorizontalHeaderLabels([
            "Step #", "Control Name", "Control Type", "Automation ID", "Bounding Box"
        ])
        self.table_steps.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_steps.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_steps.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_steps.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_steps.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_steps.verticalHeader().setVisible(False)
        layout.addWidget(self.table_steps)

        # Keyboard Barriers Table
        barriers_lbl = QLabel("KEYBOARD FOCUS BARRIERS & TRAPS")
        barriers_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        barriers_lbl.setStyleSheet(f"color: {ACCENT_RED};")
        layout.addWidget(barriers_lbl)

        self.txt_barriers = QTextEdit()
        self.txt_barriers.setReadOnly(True)
        self.txt_barriers.setMinimumHeight(110)
        layout.addWidget(self.txt_barriers)

    def load_tree(self, tree: UITree):
        self._current_tree = tree
        self.run_simulated_audit()

    def run_simulated_audit(self):
        if not self._current_tree:
            self.lbl_status.setText("No UI elements currently loaded to audit. Please run an interface audit first.")
            return

        report = keyboard_auditor.simulate_audit_from_tree(self._current_tree)
        self._current_report = report

        self.lbl_status.setText(report.summary_message)

        # Populate Steps Table
        self.table_steps.setRowCount(len(report.steps))
        for row, s in enumerate(report.steps):
            it_step = QTableWidgetItem(f"#{s.step_number}")
            it_name = QTableWidgetItem(s.control_name)
            it_type = QTableWidgetItem(s.control_type)
            it_id = QTableWidgetItem(s.automation_id or "—")
            it_bounds = QTableWidgetItem(f"{s.bounds[0]},{s.bounds[1]} ({s.bounds[2]}x{s.bounds[3]})")

            it_step.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table_steps.setItem(row, 0, it_step)
            self.table_steps.setItem(row, 1, it_name)
            self.table_steps.setItem(row, 2, it_type)
            self.table_steps.setItem(row, 3, it_id)
            self.table_steps.setItem(row, 4, it_bounds)

        # Populate Barriers
        barrier_lines = []
        if report.unreachable_elements:
            barrier_lines.append(f"• UNREACHABLE CONTROLS ({len(report.unreachable_elements)} elements skipped):")
            for u in report.unreachable_elements[:5]:
                barrier_lines.append(f"    - [{u.control_type}] \"{u.name or '<Unnamed>'}\" at bounds {u.bounds}")

        for f in report.findings:
            barrier_lines.append(f"• [{f.severity.value}] {f.title}: {f.recommendation}")

        if not barrier_lines:
            barrier_lines.append("No keyboard traps, unreachable elements, or tab bounce loops detected.")

        self.txt_barriers.setPlainText("\n".join(barrier_lines))

    def read_summary(self):
        if self._current_report:
            script = f"Keyboard audit summary. {self._current_report.summary_message} "
            if self._current_report.unreachable_elements:
                script += f"Warning: {len(self._current_report.unreachable_elements)} interactive controls could not be reached via tab navigation."
            tts_engine.speak(script)

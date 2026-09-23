"""Detailed Findings and Multi-Signal Evidence view for AccessLens AI.

Presents all detected accessibility barriers with explicit evidence tags:
[MEASURED], [DETECTED], [INFERRED], and [RECOMMENDED], plus developer remediation snippets.
"""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel,
    QPlainTextEdit, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
)

from accessibility.element_model import FindingModel, FindingSeverity
from accessibility.remediation_engine import remediation_engine
from app.ui.components import (
    ACCENT_AMBER, ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN,
    ACCENT_RED, BG_CARD, BG_CARD_BORDER, CardWidget,
    StatusBadge, TEXT_PRIMARY, TEXT_SECONDARY
)
from audio.text_to_speech import tts_engine


class FindingsView(QWidget):
    """Detailed view for browsing, filtering, and narrating accessibility findings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_findings: List[FindingModel] = []
        self._filtered_findings: List[FindingModel] = []
        self._selected_finding: Optional[FindingModel] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Title & Filter
        title_box = QHBoxLayout()
        title_lbl = QLabel("Accessibility Findings & Grounded Evidence")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_box.addWidget(title_lbl)
        title_box.addStretch()

        filter_lbl = QLabel("Severity Filter:")
        filter_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600;")
        title_box.addWidget(filter_lbl)

        self.filter_combo = QComboBox()
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {BG_CARD};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                color: {TEXT_PRIMARY};
                font-weight: 600;
                min-width: 140px;
            }}
        """)
        self.filter_combo.addItems(["All Severities", "Critical Only", "High Only", "Medium Only", "Low / Info"])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        title_box.addWidget(self.filter_combo)

        self.btn_read_finding = QPushButton("🔊 Read Finding Aloud")
        self.btn_read_finding.setStyleSheet(f"""
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
        self.btn_read_finding.clicked.connect(self._read_selected_finding)
        title_box.addWidget(self.btn_read_finding)

        main_layout.addLayout(title_box)

        # Splitter (Top: Findings Table, Bottom: Evidence & Remediation)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(8)

        # Top Pane: Findings Table
        top_card = CardWidget()
        top_layout = QVBoxLayout(top_card)
        self.table_findings = QTableWidget(0, 5)
        self.table_findings.setHorizontalHeaderLabels([
            "Severity", "Finding Title", "Category", "Affected Element", "Confidence"
        ])
        self.table_findings.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_findings.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_findings.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_findings.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_findings.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_findings.verticalHeader().setVisible(False)
        self.table_findings.itemSelectionChanged.connect(self._on_finding_selection_changed)
        top_layout.addWidget(self.table_findings)
        splitter.addWidget(top_card)

        # Bottom Pane: Evidence and Remediation Code
        bottom_card = CardWidget()
        bottom_layout = QHBoxLayout(bottom_card)
        bottom_layout.setSpacing(16)

        # Left Sub-Pane: Grounded Evidence
        ev_box = QVBoxLayout()
        ev_head = QLabel("GROUNDED EVIDENCE (MULTI-SIGNAL ATTESTATION)")
        ev_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        ev_head.setStyleSheet(f"color: {ACCENT_CYAN};")
        ev_box.addWidget(ev_head)

        self.txt_evidence = QTextEdit()
        self.txt_evidence.setReadOnly(True)
        self.txt_evidence.setPlaceholderText("Select a finding above to view observed evidence...")
        ev_box.addWidget(self.txt_evidence)
        bottom_layout.addLayout(ev_box, 1)

        # Right Sub-Pane: Remediation Snippet
        rem_box = QVBoxLayout()
        rem_head = QLabel("REMEDIATION GUIDANCE & CODE SNIPPET")
        rem_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        rem_head.setStyleSheet(f"color: {ACCENT_AMBER};")
        rem_box.addWidget(rem_head)

        self.txt_remediation = QPlainTextEdit()
        self.txt_remediation.setReadOnly(True)
        self.txt_remediation.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #0A0C12;
                color: #A7F3D0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid {BG_CARD_BORDER};
            }}
        """)
        self.txt_remediation.setPlaceholderText("Developer code guidance...")
        rem_box.addWidget(self.txt_remediation)
        bottom_layout.addLayout(rem_box, 1)

        splitter.addWidget(bottom_card)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

    def load_findings(self, findings: List[FindingModel]):
        self._all_findings = findings
        self._apply_filter()

    def _apply_filter(self):
        idx = self.filter_combo.currentIndex()
        if idx == 1:
            self._filtered_findings = [f for f in self._all_findings if f.severity == FindingSeverity.CRITICAL]
        elif idx == 2:
            self._filtered_findings = [f for f in self._all_findings if f.severity == FindingSeverity.HIGH]
        elif idx == 3:
            self._filtered_findings = [f for f in self._all_findings if f.severity == FindingSeverity.MEDIUM]
        elif idx == 4:
            self._filtered_findings = [f for f in self._all_findings if f.severity in [FindingSeverity.LOW, FindingSeverity.INFO]]
        else:
            self._filtered_findings = list(self._all_findings)

        self.table_findings.setRowCount(len(self._filtered_findings))
        for row, f in enumerate(self._filtered_findings):
            it_sev = QTableWidgetItem(f.severity.value)
            it_title = QTableWidgetItem(f.title)
            it_cat = QTableWidgetItem(f.category.value)
            elem_desc = f"[{f.element_type}] {f.element_name}" if f.element_type else "Window-wide"
            it_elem = QTableWidgetItem(elem_desc)
            it_conf = QTableWidgetItem(f"{f.confidence * 100:.0f}%")

            it_sev.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_conf.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if f.severity == FindingSeverity.CRITICAL:
                it_sev.setForeground(Qt.GlobalColor.red)
            elif f.severity == FindingSeverity.HIGH:
                it_sev.setForeground(Qt.GlobalColor.yellow)

            self.table_findings.setItem(row, 0, it_sev)
            self.table_findings.setItem(row, 1, it_title)
            self.table_findings.setItem(row, 2, it_cat)
            self.table_findings.setItem(row, 3, it_elem)
            self.table_findings.setItem(row, 4, it_conf)

        if self._filtered_findings:
            self.table_findings.selectRow(0)

    def _on_finding_selection_changed(self):
        selected_rows = self.table_findings.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        if 0 <= row < len(self._filtered_findings):
            f = self._filtered_findings[row]
            self._selected_finding = f

            # Evidence text
            ev_lines = [f"Finding: {f.title}\nCategory: {f.category.value} | Severity: {f.severity.value}\n"]
            ev_lines.append("Observed Signals:")
            for ev in f.evidence:
                ev_lines.append(f"  • {ev}")
            ev_lines.append(f"\nRecommendation:\n  {f.recommendation}")
            self.txt_evidence.setPlainText("\n".join(ev_lines))

            # Remediation Code
            rem = remediation_engine.explain_finding(f)
            code_text = f"// Remediation for: {f.title}\n"
            code_text += f"// Impact: {rem['impact']}\n\n"
            code_text += f"// Implementation (XAML/WPF/WinUI):\n{rem.get('wpf_xaml', '')}\n\n"
            code_text += f"// Web/HTML Alternative:\n{rem.get('web_html', '')}\n\n"
            code_text += f"// Manual Verification:\n// {rem.get('verification_guidance', '')}"
            self.txt_remediation.setPlainText(code_text)

    def _read_selected_finding(self):
        if self._selected_finding:
            script = remediation_engine.generate_speech_narration(self._selected_finding)
            tts_engine.speak(script)

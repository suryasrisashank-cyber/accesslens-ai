"""Element Inspector view for AccessLens AI.

Provides a developer-focused tree and property inspector for UI Automation elements,
correlating visual bounds, OCR text, accessibility issues, and remediation code.
"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QListWidget, QListWidgetItem,
    QPlainTextEdit, QPushButton, QScrollArea, QSplitter,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
    QWidget
)

from accessibility.element_model import UIElementModel
from accessibility.remediation_engine import remediation_engine
from app.ui.components import (
    ACCENT_AMBER, ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN,
    ACCENT_RED, BG_CARD, BG_CARD_BORDER, BG_SURFACE,
    CardWidget, StatusBadge, TEXT_PRIMARY, TEXT_SECONDARY
)


class ElementInspectorView(QWidget):
    """Interactive property inspector for UI elements and associated accessibility issues."""

    element_selected = Signal(object)  # Emits UIElementModel

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elements: List[UIElementModel] = []
        self._current_element: Optional[UIElementModel] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Title
        title_box = QHBoxLayout()
        title_lbl = QLabel("UI Element & Property Inspector")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_box.addWidget(title_lbl)
        title_box.addStretch()

        self.count_badge = StatusBadge("0 Elements", bg_color="#1E293B", text_color="#38BDF8")
        title_box.addWidget(self.count_badge)
        main_layout.addLayout(title_box)

        # Splitter (Left: Element List, Right: Element Detail Inspector)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # Left Column: Elements List
        left_card = CardWidget()
        left_layout = QVBoxLayout(left_card)
        left_head = QLabel("DETECTED UI ELEMENTS")
        left_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        left_head.setStyleSheet(f"color: {ACCENT_CYAN};")
        left_layout.addWidget(left_head)

        self.element_list = QListWidget()
        self.element_list.setStyleSheet(f"""
            QListWidget {{
                background-color: #12151E;
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {BG_CARD_BORDER};
            }}
            QListWidget::item:selected {{
                background-color: #2563EB;
                color: white;
            }}
        """)
        self.element_list.currentRowChanged.connect(self._on_element_selected)
        left_layout.addWidget(self.element_list)
        splitter.addWidget(left_card)

        # Right Column: Property Detail & Remediation
        right_card = CardWidget()
        right_layout = QVBoxLayout(right_card)
        right_head = QLabel("ACCESSIBILITY PROPERTIES & REMEDIATION")
        right_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        right_head.setStyleSheet(f"color: {ACCENT_AMBER};")
        right_layout.addWidget(right_head)

        # Properties Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        prop_container = QWidget()
        self.prop_layout = QVBoxLayout(prop_container)
        self.prop_layout.setSpacing(10)

        # Form layout for properties
        form_frame = QFrame()
        form_frame.setStyleSheet(f"background-color: #12151E; border-radius: 6px; padding: 10px;")
        self.form_layout = QFormLayout(form_frame)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.lbl_name = QLabel("—")
        self.lbl_role = QLabel("—")
        self.lbl_id = QLabel("—")
        self.lbl_class = QLabel("—")
        self.lbl_bounds = QLabel("—")
        self.lbl_focusable = QLabel("—")
        self.lbl_ocr = QLabel("—")

        for lbl in [self.lbl_name, self.lbl_role, self.lbl_id, self.lbl_class, self.lbl_bounds, self.lbl_focusable, self.lbl_ocr]:
            lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600;")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.form_layout.addRow("Accessible Name:", self.lbl_name)
        self.form_layout.addRow("Control Type:", self.lbl_role)
        self.form_layout.addRow("Automation ID:", self.lbl_id)
        self.form_layout.addRow("Class Name:", self.lbl_class)
        self.form_layout.addRow("Bounding Box:", self.lbl_bounds)
        self.form_layout.addRow("Keyboard Focusable:", self.lbl_focusable)
        self.form_layout.addRow("Correlated OCR Text:", self.lbl_ocr)
        self.prop_layout.addWidget(form_frame)

        # Detected Issues on Element
        issues_head = QLabel("DETECTED BARRIERS & EVIDENCE")
        issues_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        issues_head.setStyleSheet(f"color: {ACCENT_RED}; margin-top: 8px;")
        self.prop_layout.addWidget(issues_head)

        self.txt_issues = QTextEdit()
        self.txt_issues.setReadOnly(True)
        self.txt_issues.setMinimumHeight(120)
        self.prop_layout.addWidget(self.txt_issues)

        # Developer Remediation Code
        code_head = QLabel("DEVELOPER REMEDIATION SNIPPET (XAML / C#)")
        code_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        code_head.setStyleSheet(f"color: {ACCENT_GREEN}; margin-top: 8px;")
        self.prop_layout.addWidget(code_head)

        self.txt_code = QPlainTextEdit()
        self.txt_code.setReadOnly(True)
        self.txt_code.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #0A0C12;
                color: #A7F3D0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid {BG_CARD_BORDER};
            }}
        """)
        self.txt_code.setMinimumHeight(130)
        self.prop_layout.addWidget(self.txt_code)

        scroll.setWidget(prop_container)
        right_layout.addWidget(scroll)
        splitter.addWidget(right_card)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

    def load_elements(self, elements: List[UIElementModel]):
        """Populates element inspector with list of UIElementModel."""
        self._elements = elements
        self.element_list.clear()
        self.count_badge.setText(f"{len(elements)} Elements")

        for el in elements:
            item = QListWidgetItem(el.display_label)
            if el.findings:
                item.setForeground(Qt.GlobalColor.yellow)
            self.element_list.addItem(item)

        if elements:
            self.element_list.setCurrentRow(0)

    def _on_element_selected(self, row: int):
        if 0 <= row < len(self._elements):
            el = self._elements[row]
            self._current_element = el
            self.element_selected.emit(el)

            self.lbl_name.setText(el.name or "<Empty / None>")
            self.lbl_role.setText(el.control_type)
            self.lbl_id.setText(el.automation_id or "<None>")
            self.lbl_class.setText(el.class_name or "<None>")
            self.lbl_bounds.setText(f"{el.bounds[0]}, {el.bounds[1]} (Size: {el.bounds[2]}x{el.bounds[3]} px)")
            self.lbl_focusable.setText("True" if el.is_focusable else "False (Keyboard Barrier)")
            self.lbl_ocr.setText(el.ocr_associated_text or "<No Text Overlap>")

            # Format Issues & Evidence
            if el.findings:
                issue_lines = []
                for f in el.findings:
                    issue_lines.append(f"• [{f.severity.value}] {f.title}")
                    for ev in f.evidence:
                        issue_lines.append(f"    - {ev}")
                    issue_lines.append(f"    Recommendation: {f.recommendation}\n")
                self.txt_issues.setPlainText("\n".join(issue_lines))

                # Remediation code
                rem = remediation_engine.explain_finding(el.findings[0])
                code_snippet = f"// Remediation for: {el.findings[0].title}\n"
                code_snippet += f"// Impact: {rem['impact']}\n\n"
                code_snippet += rem.get("wpf_xaml", "") + "\n\n"
                code_snippet += f"// Verification: {rem.get('verification_guidance', '')}"
                self.txt_code.setPlainText(code_snippet)
            else:
                self.txt_issues.setPlainText("No deterministic accessibility barriers detected on this element.")
                self.txt_code.setPlainText("// Control adheres to standard accessible property guidelines.")

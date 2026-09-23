"""Audit Reports and Sensitive Data Redaction view for AccessLens AI.

Enables export to Markdown, JSON, and self-contained HTML with optional
conservative masking of sensitive credentials, payment cards, emails, and phone numbers.
"""

import os
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QHBoxLayout, QLabel,
    QMessageBox, QPlainTextEdit, QPushButton,
    QVBoxLayout, QWidget
)

from accessibility.element_model import InterfaceSnapshot
from accessibility.report_generator import report_generator
from app.ui.components import (
    ACCENT_AMBER, ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN,
    BG_CARD, BG_CARD_BORDER, CardWidget, StatusBadge,
    TEXT_PRIMARY, TEXT_SECONDARY
)


class ReportsView(QWidget):
    """View for previewing and exporting formal accessibility audit reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshot: Optional[InterfaceSnapshot] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Title & Export Buttons
        title_box = QHBoxLayout()
        title_lbl = QLabel("Audit Reports & Sensitive Data Protection")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_box.addWidget(title_lbl)
        title_box.addStretch()

        self.chk_mask = QCheckBox("Mask Sensitive Data (Credentials / PII)")
        self.chk_mask.setChecked(True)
        self.chk_mask.setStyleSheet(f"color: {ACCENT_GREEN}; font-weight: 600;")
        self.chk_mask.toggled.connect(self._refresh_preview)
        title_box.addWidget(self.chk_mask)

        self.btn_export_md = QPushButton("Export Markdown")
        self.btn_export_md.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BG_CARD_BORDER}; padding: 6px 14px; font-weight: 600;")
        self.btn_export_md.clicked.connect(lambda: self.export_report("md"))
        title_box.addWidget(self.btn_export_md)

        self.btn_export_json = QPushButton("Export JSON")
        self.btn_export_json.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BG_CARD_BORDER}; padding: 6px 14px; font-weight: 600;")
        self.btn_export_json.clicked.connect(lambda: self.export_report("json"))
        title_box.addWidget(self.btn_export_json)

        self.btn_export_html = QPushButton("Export HTML")
        self.btn_export_html.setStyleSheet(f"background-color: {ACCENT_BLUE}; color: white; padding: 6px 16px; font-weight: 700; border-radius: 4px;")
        self.btn_export_html.clicked.connect(lambda: self.export_report("html"))
        title_box.addWidget(self.btn_export_html)

        layout.addLayout(title_box)

        # Redaction Review Banner
        redact_banner = CardWidget()
        rb_layout = QHBoxLayout(redact_banner)
        rb_desc = QLabel(
            "🔒 SENSITIVE DATA PROTECTION ACTIVE:\n"
            "Reports are generated locally. Before external sharing or developer export, potential credentials, tokens,\n"
            "phone numbers, and payment sequences are conservatively redacted."
        )
        rb_desc.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px;")
        rb_layout.addWidget(rb_desc)
        layout.addWidget(redact_banner)

        # Report Preview Text
        self.txt_preview = QPlainTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #12151E;
                color: {TEXT_PRIMARY};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid {BG_CARD_BORDER};
            }}
        """)
        self.txt_preview.setPlaceholderText("Report preview will appear here once an audit is executed...")
        layout.addWidget(self.txt_preview)

    def load_snapshot(self, snapshot: InterfaceSnapshot):
        self._snapshot = snapshot
        self._refresh_preview()

    def _refresh_preview(self):
        if not self._snapshot:
            return
        mask = self.chk_mask.isChecked()
        md_text = report_generator.generate_markdown(self._snapshot, mask=mask)
        self.txt_preview.setPlainText(md_text)

    def export_report(self, format_type: str):
        if not self._snapshot:
            QMessageBox.information(self, "No Audit Data", "Please run an interface audit before exporting reports.")
            return

        mask = self.chk_mask.isChecked()
        if format_type == "md":
            content = report_generator.generate_markdown(self._snapshot, mask=mask)
            def_ext = "Markdown Files (*.md)"
            def_name = f"AccessLens_Audit_{self._snapshot.application_name.replace(' ', '_')}.md"
        elif format_type == "json":
            content = report_generator.generate_json(self._snapshot, mask=mask)
            def_ext = "JSON Files (*.json)"
            def_name = f"AccessLens_Audit_{self._snapshot.application_name.replace(' ', '_')}.json"
        else:
            content = report_generator.generate_html(self._snapshot, mask=mask)
            def_ext = "HTML Files (*.html)"
            def_name = f"AccessLens_Audit_{self._snapshot.application_name.replace(' ', '_')}.html"

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Audit Report", def_name, def_ext)
        if file_path:
            try:
                report_generator.save_report_to_file(content, file_path)
                QMessageBox.information(self, "Export Successful", f"Report saved successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error saving report: {e}")

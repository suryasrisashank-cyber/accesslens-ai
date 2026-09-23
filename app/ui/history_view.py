"""History view for VisionVoice AI.

Displays SQLite-persisted analysis metadata without exposing raw image files.
Includes a Clear History action.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget
)

from app.ui.components import (
    ACCENT_AMBER, ACCENT_BLUE, ACCENT_CYAN, ACCENT_RED,
    BG_CARD, BG_CARD_BORDER, TEXT_PRIMARY, TEXT_SECONDARY
)
from storage.database import database_manager


class HistoryView(QWidget):
    """Analysis history viewer with SQLite backend."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Title
        title_box = QHBoxLayout()
        title_lbl = QLabel("Analysis History")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_box.addWidget(title_lbl)
        title_box.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_CARD};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {ACCENT_CYAN};
            }}
        """)
        refresh_btn.clicked.connect(self.load_history)
        title_box.addWidget(refresh_btn)

        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #7F1D1D;
                color: #FCA5A5;
                border: 1px solid #B91C1C;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #991B1B;
                color: #FFFFFF;
            }}
        """)
        clear_btn.clicked.connect(self.clear_history)
        title_box.addWidget(clear_btn)

        layout.addLayout(title_box)

        # Subtitle
        sub_lbl = QLabel("Lightweight SQLite record log. Raw image pixels are not saved to preserve user privacy.")
        sub_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(sub_lbl)

        # History Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "Source Type", "Analysis Summary", "Processing Backend"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.load_history()

    def load_history(self):
        records = database_manager.get_records(100)
        self.table.setRowCount(len(records))

        for row, r in enumerate(records):
            item_id = QTableWidgetItem(str(r.id))
            item_ts = QTableWidgetItem(r.timestamp)
            item_ft = QTableWidgetItem(r.file_type)
            # Truncate summary if long for table readability
            summary_preview = r.analysis_summary.replace("\n", " ")
            if len(summary_preview) > 90:
                summary_preview = summary_preview[:90] + "..."
            item_sum = QTableWidgetItem(summary_preview)
            item_be = QTableWidgetItem(r.processing_backend)

            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ts.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ft.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_be.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, item_id)
            self.table.setItem(row, 1, item_ts)
            self.table.setItem(row, 2, item_ft)
            self.table.setItem(row, 3, item_sum)
            self.table.setItem(row, 4, item_be)

    def clear_history(self):
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to permanently clear all analysis history records?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            database_manager.clear_history()
            self.load_history()

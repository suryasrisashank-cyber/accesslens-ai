"""Reusable UI components and styles for VisionVoice AI dark accessibility theme."""

from typing import List, Optional
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget
)

from vision.image_utils import draw_bounding_boxes_on_pixmap


# Color Palette (Dark High-Contrast Theme for Accessibility)
BG_PRIMARY = "#0F1117"
BG_SURFACE = "#1A1D27"
BG_CARD = "#212636"
BG_CARD_BORDER = "#2E364B"
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"
ACCENT_CYAN = "#00D2D3"
ACCENT_BLUE = "#2563EB"
ACCENT_GREEN = "#10B981"
ACCENT_AMBER = "#F59E0B"
ACCENT_RED = "#EF4444"


DARK_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
}}

QWidget {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    color: {TEXT_PRIMARY};
}}

QTabBar::tab {{
    background-color: {BG_SURFACE};
    color: {TEXT_SECONDARY};
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    background-color: {BG_CARD};
    color: {ACCENT_CYAN};
    border-bottom: 3px solid {ACCENT_CYAN};
}}

QTabWidget::pane {{
    border: 1px solid {BG_CARD_BORDER};
    background-color: {BG_SURFACE};
    border-radius: 8px;
}}

QTextEdit, QPlainTextEdit {{
    background-color: #12151E;
    border: 1px solid {BG_CARD_BORDER};
    border-radius: 6px;
    color: {TEXT_PRIMARY};
    padding: 8px;
    font-size: 13px;
    line-height: 1.5;
}}

QScrollBar:vertical {{
    background-color: {BG_SURFACE};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: #374151;
    border-radius: 5px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {ACCENT_CYAN};
}}

QTableWidget {{
    background-color: {BG_CARD};
    border: 1px solid {BG_CARD_BORDER};
    gridline-color: {BG_CARD_BORDER};
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}

QHeaderView::section {{
    background-color: {BG_SURFACE};
    color: {TEXT_SECONDARY};
    font-weight: 600;
    padding: 6px;
    border: 1px solid {BG_CARD_BORDER};
}}
"""


class CardWidget(QFrame):
    """Modern elevated card container with dark styling."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 10px;
                padding: 12px;
            }}
        """)


class AccessibleButton(QPushButton):
    """High-contrast button for accessible tactile clicks."""

    def __init__(self, text: str, primary: bool = False, accent_color: str = ACCENT_BLUE, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(44)
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        self.setFont(font)

        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {accent_color};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: #1D4ED8;
                }}
                QPushButton:pressed {{
                    background-color: #1E40AF;
                }}
                QPushButton:disabled {{
                    background-color: #334155;
                    color: #64748B;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_SURFACE};
                    color: {TEXT_PRIMARY};
                    border: 1px solid {BG_CARD_BORDER};
                    border-radius: 8px;
                    padding: 8px 18px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #2D3748;
                    border-color: {ACCENT_CYAN};
                    color: {ACCENT_CYAN};
                }}
                QPushButton:pressed {{
                    background-color: #1A202C;
                }}
                QPushButton:disabled {{
                    background-color: #1E293B;
                    color: #475569;
                    border-color: #334155;
                }}
            """)


class StatusBadge(QLabel):
    """Visual status pill badge."""

    def __init__(self, text: str, bg_color: str = "#1E293B", text_color: str = "#38BDF8", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 700;
                border: 1px solid {text_color}44;
            }}
        """)


class ImagePreviewWidget(QLabel):
    """Displays original or bounding-box-overlaid image preview responsively."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self._raw_pixmap: Optional[QPixmap] = None
        self._annotated_pixmap: Optional[QPixmap] = None
        self._show_boxes: bool = True
        self.setStyleSheet(f"""
            QLabel {{
                background-color: #0B0D13;
                border: 2px dashed {BG_CARD_BORDER};
                border-radius: 8px;
                color: {TEXT_SECONDARY};
                font-size: 14px;
            }}
        """)
        self.setText("No Image Loaded\nClick 'Open Image' or 'Capture Screen'")

    def set_image(self, pixmap: QPixmap, bounding_boxes: Optional[List[dict]] = None):
        """Sets the preview pixmap and generates box overlay."""
        self._raw_pixmap = pixmap
        if bounding_boxes and len(bounding_boxes) > 0:
            self._annotated_pixmap = draw_bounding_boxes_on_pixmap(pixmap, bounding_boxes)
        else:
            self._annotated_pixmap = pixmap

        self._refresh_display()

    def toggle_boxes(self, show: bool):
        self._show_boxes = show
        self._refresh_display()

    def _refresh_display(self):
        target_pixmap = self._annotated_pixmap if self._show_boxes else self._raw_pixmap
        if target_pixmap and not target_pixmap.isNull():
            # Scale smoothly maintaining aspect ratio
            scaled = target_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled)
        else:
            self.setText("No Image Loaded\nClick 'Open Image' or 'Capture Screen'")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_display()

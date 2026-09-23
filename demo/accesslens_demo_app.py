"""Synthetic Demonstration Application for AccessLens AI.

Intentionally provides known accessibility barriers (missing accessible names,
label mismatches, low contrast ratios, undersized click targets, and poor focus order)
alongside correctly implemented controls for offline competition auditing.
"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QPushButton, QVBoxLayout,
    QWidget
)


class AccessLensDemoApp(QMainWindow):
    """Target Windows test application with intentional accessibility defects."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AccessLens Demo App — [DEMO / SYNTHETIC TARGET]")
        self.resize(750, 600)
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Warning & Attestation Banner
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background-color: #FEF3C7;
                border: 2px solid #F59E0B;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        b_layout = QVBoxLayout(banner)
        b_title = QLabel("⚠️ [DEMO / SYNTHETIC TARGET] — Synthetic Accessibility Defects")
        b_title.setStyleSheet("color: #92400E; font-weight: 800; font-size: 13px;")
        b_desc = QLabel("This test window intentionally incorporates common WCAG 2.1 accessibility defects for QA auditing demonstration. It is not a real university or commercial application.")
        b_desc.setStyleSheet("color: #78350F; font-size: 11px;")
        b_layout.addWidget(b_title)
        b_layout.addWidget(b_desc)
        main_layout.addWidget(banner)

        # Form Container
        grid = QGridLayout()
        grid.setVerticalSpacing(16)
        grid.setHorizontalSpacing(20)

        # Defect 1: Missing Accessible Name on Icon Button
        d1_label = QLabel("Defect 1 — Missing Accessible Name:")
        d1_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        grid.addWidget(d1_label, 0, 0)

        self.btn_unnamed = QPushButton("🔍")
        self.btn_unnamed.setToolTip("")
        self.btn_unnamed.setAccessibleName("")  # Intentionally empty accessible name
        self.btn_unnamed.setAccessibleDescription("")
        self.btn_unnamed.setStyleSheet("font-size: 16px; padding: 6px 12px;")
        grid.addWidget(self.btn_unnamed, 0, 1)

        # Defect 2: Visible vs Accessible Name Mismatch
        d2_label = QLabel("Defect 2 — Label in Name Mismatch:")
        d2_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        grid.addWidget(d2_label, 1, 0)

        self.btn_mismatch = QPushButton("Download Application Form")
        self.btn_mismatch.setAccessibleName("Submit Contact Inquiry")  # Intentionally conflicting accessible name
        self.btn_mismatch.setStyleSheet("background-color: #2563EB; color: white; padding: 8px 16px; font-weight: 600;")
        grid.addWidget(self.btn_mismatch, 1, 1)

        # Defect 3: Severe Low Contrast Ratio (< 2.0:1)
        d3_label = QLabel("Defect 3 — Low Contrast Text:")
        d3_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        grid.addWidget(d3_label, 2, 0)

        self.lbl_contrast = QLabel("Secondary terms and policy notice (Low Contrast)")
        # Light gray #A8A8A8 on light gray #EEEEEE yields ~1.8:1 contrast
        self.lbl_contrast.setStyleSheet("""
            background-color: #EEEEEE;
            color: #A8A8A8;
            padding: 8px;
            font-size: 11px;
            border-radius: 4px;
        """)
        grid.addWidget(self.lbl_contrast, 2, 1)

        # Defect 4: Undersized Click Target (< 16x16 px)
        d4_label = QLabel("Defect 4 — Undersized Click Target:")
        d4_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        grid.addWidget(d4_label, 3, 0)

        self.btn_tiny = QPushButton("x")
        self.btn_tiny.setFixedSize(14, 14)  # Intentionally 14x14 pixels
        self.btn_tiny.setStyleSheet("background-color: #DC2626; color: white; font-size: 9px; padding: 0px;")
        grid.addWidget(self.btn_tiny, 3, 1)

        # Defect 5: Unfocusable Interactive Element
        d5_label = QLabel("Defect 5 — Non-Focusable Control:")
        d5_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        grid.addWidget(d5_label, 4, 0)

        self.btn_unfocusable = QPushButton("Interactive Button (Not Tab-Focusable)")
        self.btn_unfocusable.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Skipped during Tab navigation
        self.btn_unfocusable.setStyleSheet("background-color: #475569; color: white; padding: 6px 12px;")
        grid.addWidget(self.btn_unfocusable, 4, 1)

        # Correct Implementation: Fully Accessible Control
        ok_label = QLabel("Compliant Control — Fully Accessible:")
        ok_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        grid.addWidget(ok_label, 5, 0)

        self.btn_good = QPushButton("Save & Continue to Next Step")
        self.btn_good.setAccessibleName("Save & Continue to Next Step")
        self.btn_good.setAccessibleDescription("Saves all form inputs and advances to review screen.")
        self.btn_good.setMinimumHeight(44)  # 44px compliant touch target
        self.btn_good.setStyleSheet("""
            background-color: #059669;
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 700;
            padding: 10px 20px;
            border-radius: 6px;
        """)
        grid.addWidget(self.btn_good, 5, 1)

        main_layout.addLayout(grid)
        main_layout.addStretch()

        status = QLabel("Status: Ready for AccessLens AI Live Inspection")
        status.setStyleSheet("color: #6B7280; font-size: 11px;")
        main_layout.addWidget(status)


def run_demo_app():
    app = QApplication.instance() or QApplication(sys.argv)
    window = AccessLensDemoApp()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_demo_app())

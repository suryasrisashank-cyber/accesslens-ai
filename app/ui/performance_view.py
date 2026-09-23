"""Performance benchmark view for VisionVoice AI.

Runs and displays local latency and memory consumption metrics honestly labeled
as LOCAL CPU BENCHMARK.
"""

import os
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QProgressBar,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from app.ui.components import (
    ACCENT_AMBER, ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN,
    BG_CARD, BG_CARD_BORDER, BG_SURFACE, CardWidget,
    TEXT_PRIMARY, TEXT_SECONDARY
)
from scripts.benchmark import BenchmarkMetric, run_benchmark


class BenchmarkWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def run(self):
        try:
            metrics = run_benchmark()
            self.finished.emit(metrics)
        except Exception as e:
            self.error.emit(str(e))


class PerformanceView(QWidget):
    """Local benchmark display page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Title
        title_box = QHBoxLayout()
        title_lbl = QLabel("Performance & Latency Benchmark")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_box.addWidget(title_lbl)
        title_box.addStretch()

        self.run_btn = QPushButton("▶ Run Local CPU Benchmark")
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_BLUE};
                color: #FFFFFF;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #1D4ED8;
            }}
        """)
        self.run_btn.clicked.connect(self.start_benchmark)
        title_box.addWidget(self.run_btn)
        layout.addLayout(title_box)

        # Notice Card
        notice_card = CardWidget()
        n_layout = QVBoxLayout(notice_card)
        badge_lbl = QLabel("LOCAL CPU BENCHMARK (AMD RYZEN HOST)")
        badge_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        badge_lbl.setStyleSheet(f"color: {ACCENT_AMBER};")
        desc_lbl = QLabel(
            "Measurements below reflect local ONNX Runtime execution on standard x86 CPU fallback.\n"
            "On Qualcomm Snapdragon X Series hardware, these operations can target the Hexagon NPU\n"
            "for enhanced throughput and reduced thermal footprint."
        )
        desc_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        n_layout.addWidget(badge_lbl)
        n_layout.addWidget(desc_lbl)
        layout.addWidget(notice_card)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BG_CARD};
                border: 1px solid {BG_CARD_BORDER};
                border-radius: 4px;
                height: 12px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT_CYAN};
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Table of results
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Visual Sample", "OCR Time (ms)", "Analysis Time (ms)", "Total Latency (ms)", "Process RAM (MB)", "Backend"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def start_benchmark(self):
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.table.setRowCount(0)

        self._worker = BenchmarkWorker()
        self._worker.finished.connect(self.on_benchmark_finished)
        self._worker.error.connect(self.on_benchmark_error)
        self._worker.start()

    def on_benchmark_finished(self, metrics):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        self.table.setRowCount(len(metrics))
        for row, m in enumerate(metrics):
            item_name = QTableWidgetItem(m.sample_name)
            item_ocr = QTableWidgetItem(f"{m.ocr_time_ms:.1f}")
            item_ana = QTableWidgetItem(f"{m.analysis_time_ms:.1f}")
            item_tot = QTableWidgetItem(f"{m.total_time_ms:.1f}")
            item_mem = QTableWidgetItem(f"{m.memory_rss_mb:.1f}")
            item_be = QTableWidgetItem(m.backend_label)

            for it in [item_name, item_ocr, item_ana, item_tot, item_mem, item_be]:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, item_ocr)
            self.table.setItem(row, 2, item_ana)
            self.table.setItem(row, 3, item_tot)
            self.table.setItem(row, 4, item_mem)
            self.table.setItem(row, 5, item_be)

    def on_benchmark_error(self, err_msg):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

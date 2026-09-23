"""Lightweight SQLite database storage for VisionVoice AI analysis history.

Stores minimal metadata (timestamp, file type, summary, backend).
Never stores the original user image bytes by default to preserve strict privacy.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import os
import sqlite3
from typing import List, Optional


@dataclass
class HistoryRecord:
    id: int
    timestamp: str
    file_type: str
    analysis_summary: str
    processing_backend: str
    word_count: int = 0
    confidence: float = 0.0


@dataclass
class ReportHistoryRecord:
    id: int
    report_id: str
    generated_at: str
    application_name: str
    target_window: str
    finding_count: int
    privacy_mode: str
    file_path: str
    digest: str


class DatabaseManager:
    """Manages SQLite history tracking with privacy constraints."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default database location in user's AppData or project folder
            user_data_dir = os.path.join(os.path.expanduser("~"), ".visionvoice")
            os.makedirs(user_data_dir, exist_ok=True)
            self._db_path = os.path.join(user_data_dir, "history.sqlite3")
        else:
            self._db_path = db_path

        self._init_db()

    @property
    def db_path(self) -> str:
        return self._db_path

    @contextmanager
    def _get_connection(self):
        """Yields an active SQLite connection with automatic close on exit."""
        conn = sqlite3.connect(self._db_path, timeout=10.0)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes SQLite schema if not present (strictly backward-compatible)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    analysis_summary TEXT NOT NULL,
                    processing_backend TEXT NOT NULL,
                    word_count INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 0.0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accessibility_report_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL UNIQUE,
                    generated_at TEXT NOT NULL,
                    application_name TEXT NOT NULL,
                    target_window TEXT NOT NULL,
                    finding_count INTEGER DEFAULT 0,
                    privacy_mode TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    digest TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_record(
        self,
        file_type: str,
        analysis_summary: str,
        processing_backend: str,
        word_count: int = 0,
        confidence: float = 0.0,
        timestamp: Optional[str] = None
    ) -> int:
        """Appends a new analysis event record without storing image data."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_history 
                (timestamp, file_type, analysis_summary, processing_backend, word_count, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, file_type, analysis_summary, processing_backend, word_count, confidence))
            conn.commit()
            return cursor.lastrowid

    def get_records(self, limit: int = 100) -> List[HistoryRecord]:
        """Retrieves recent analysis history records ordered newest first."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, file_type, analysis_summary, processing_backend, word_count, confidence
                FROM analysis_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                HistoryRecord(
                    id=row[0],
                    timestamp=row[1],
                    file_type=row[2],
                    analysis_summary=row[3],
                    processing_backend=row[4],
                    word_count=row[5],
                    confidence=row[6]
                )
                for row in rows
            ]

    def add_report_record(
        self,
        report_id: str,
        generated_at: str,
        application_name: str,
        target_window: str,
        finding_count: int,
        privacy_mode: str,
        file_path: str,
        digest: str,
    ) -> int:
        """Appends a new accessibility report export record (metadata only)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO accessibility_report_history
                (report_id, generated_at, application_name, target_window, finding_count, privacy_mode, file_path, digest)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (report_id, generated_at, application_name, target_window, finding_count, privacy_mode, file_path, digest))
            conn.commit()
            return cursor.lastrowid

    def get_report_records(self, limit: int = 100) -> List[ReportHistoryRecord]:
        """Retrieves recent report export metadata records ordered newest first."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, report_id, generated_at, application_name, target_window, finding_count, privacy_mode, file_path, digest
                FROM accessibility_report_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                ReportHistoryRecord(
                    id=row[0],
                    report_id=row[1],
                    generated_at=row[2],
                    application_name=row[3],
                    target_window=row[4],
                    finding_count=row[5],
                    privacy_mode=row[6],
                    file_path=row[7],
                    digest=row[8],
                )
                for row in rows
            ]

    def clear_history(self) -> int:
        """Deletes all history records from SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM analysis_history")
            deleted = cursor.rowcount
            conn.commit()
            return deleted

    def count_records(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM analysis_history")
            return cursor.fetchone()[0]


# Global singleton instance
database_manager = DatabaseManager()

"""Tests for SQLite database history operations."""

import os
import tempfile
import pytest

from storage.database import DatabaseManager


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    yield db
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def test_database_add_and_get(temp_db):
    assert temp_db.count_records() == 0
    rec_id = temp_db.add_record(
        file_type="PNG",
        analysis_summary="University portal detected.",
        processing_backend="CPU Fallback",
        word_count=50,
        confidence=0.94
    )
    assert rec_id == 1
    assert temp_db.count_records() == 1

    records = temp_db.get_records()
    assert len(records) == 1
    assert records[0].file_type == "PNG"
    assert "University" in records[0].analysis_summary
    assert records[0].processing_backend == "CPU Fallback"
    assert records[0].word_count == 50
    assert records[0].confidence == 0.94


def test_database_clear_history(temp_db):
    temp_db.add_record("JPG", "Summary 1", "CPU")
    temp_db.add_record("PNG", "Summary 2", "CPU")
    assert temp_db.count_records() == 2

    deleted = temp_db.clear_history()
    assert deleted == 2
    assert temp_db.count_records() == 0

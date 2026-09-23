"""Tests for privacy manager and local cleanup."""

import os
import tempfile
import pytest

from privacy.privacy_manager import PrivacyManager, privacy_manager


def test_privacy_statement():
    assert "stays on this device" in privacy_manager.privacy_statement
    assert privacy_manager.is_local_processing_guaranteed is True


def test_privacy_temp_file_cleanup():
    pm = PrivacyManager()
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    assert os.path.exists(path)

    pm.register_temp_file(path)
    assert path in pm._tracked_temp_files

    pm.cleanup_file(path)
    assert not os.path.exists(path)
    assert path not in pm._tracked_temp_files


def test_privacy_cleanup_all():
    pm = PrivacyManager()
    fd1, path1 = tempfile.mkstemp()
    os.close(fd1)
    fd2, path2 = tempfile.mkstemp()
    os.close(fd2)

    pm.register_temp_file(path1)
    pm.register_temp_file(path2)
    assert len(pm._tracked_temp_files) == 2

    pm.cleanup_all()
    assert len(pm._tracked_temp_files) == 0
    assert not os.path.exists(path1)
    assert not os.path.exists(path2)

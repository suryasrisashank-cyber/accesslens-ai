"""Tests verifying honest hardware detection and backend status typing."""

import pytest
from hardware.backend_status import BackendState, HardwareProfile
from hardware.hardware_detector import HardwareDetector, hardware_detector


def test_hardware_detector_inspect():
    profile = hardware_detector.inspect()
    assert isinstance(profile, HardwareProfile)
    assert profile.os_name != ""
    assert profile.architecture in ["AMD64", "x86_64", "ARM64", "aarch64"]
    assert profile.ram_gb >= 0.0
    assert isinstance(profile.backend_state, BackendState)
    assert profile.status_label != ""
    assert profile.npu_status_label != ""


def test_hardware_detector_honesty_on_amd():
    detector = HardwareDetector()
    # If on x86/AMD, ensure is_snapdragon is strictly False
    profile = detector.inspect()
    if "amd" in profile.cpu_model.lower() or "intel" in profile.cpu_model.lower():
        assert profile.is_snapdragon is False
        assert profile.is_npu_available is False
        assert profile.backend_state == BackendState.CPU
        assert "Not Available" in profile.npu_status_label or "CPU" in profile.status_label


def test_snapdragon_detection_logic():
    detector = HardwareDetector()
    # Synthetic verification of Snapdragon string matching
    assert detector.is_snapdragon_device("Snapdragon(R) X Elite", "ARM64") is True
    assert detector.is_snapdragon_device("Qualcomm Snapdragon X Plus", "aarch64") is True
    assert detector.is_snapdragon_device("AMD Ryzen 3 2200U", "AMD64") is False
    assert detector.is_snapdragon_device("Intel Core i7-13700H", "x86_64") is False

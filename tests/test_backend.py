"""Tests for compute backend manager, CPU backend, and Qualcomm backend."""

import pytest
from ai.cpu_backend import CPUBackend
from ai.qualcomm_backend import QualcommBackend
from hardware.backend_status import BackendState
from hardware.compute_backend import ComputeBackendManager


def test_cpu_backend():
    backend = CPUBackend()
    assert backend.name == "CPU Execution Provider"
    assert "CPUExecutionProvider" in backend.execution_providers
    assert backend.is_available() is True
    info = backend.get_status_info()
    assert "backend" in info
    assert "status" in info


def test_qualcomm_backend():
    backend = QualcommBackend()
    assert "Qualcomm" in backend.name
    # On AMD/Intel laptop, is_available should be False
    info = backend.get_status_info()
    assert "target_hardware" in info
    providers = backend.get_provider_configuration()
    assert "CPUExecutionProvider" in providers or any("CPUExecutionProvider" in str(p) for p in providers)


def test_compute_backend_manager():
    manager = ComputeBackendManager()
    assert manager.profile is not None
    assert manager.current_state in [
        BackendState.CPU,
        BackendState.SNAPDRAGON_CPU,
        BackendState.SNAPDRAGON_NPU_AVAILABLE,
        BackendState.SNAPDRAGON_NPU_VERIFIED,
        BackendState.UNKNOWN
    ]
    providers = manager.get_preferred_providers()
    assert len(providers) > 0
    assert "CPUExecutionProvider" in providers

"""Tests verifying hardware honesty, capability detection, and runtime selector fallback.

Verifies:
1. Host platform is AMD64 / x64, NOT Qualcomm Snapdragon.
2. Qualcomm Hexagon NPU is NOT available on current host.
3. QNNExecutionProvider fallback to CPU is explicit and documented.
4. RuntimeSelector never fabricates Snapdragon execution or benchmarks.
5. Model registry properly separates verified local models from pending Snapdragon models.
6. Deterministic match scores are strictly bounded in [0.0, 1.0].
"""

import pytest
from ai.model_registry import model_registry
from ai.runtime_selector import RuntimeSelector, runtime_selector
from hardware.backend_status import BackendState
from hardware.capability_matrix import (
    CapabilityMatrix,
    CapabilityState,
    HardwareCapabilities,
    capability_matrix,
)
from hardware.compute_backend import ComputeBackendManager
from hardware.hardware_detector import hardware_detector


def test_host_is_not_snapdragon_on_amd():
    """Confirms current host is genuinely an AMD64 development machine."""
    profile = hardware_detector.inspect()
    caps = capability_matrix.detect()

    assert profile.cpu_model != ""
    assert profile.architecture in ["AMD64", "x86_64"]
    assert profile.is_snapdragon is False
    assert caps.qualcomm_detected is False
    assert caps.npu_available is False
    assert caps.qnn_available is False
    assert caps.verification_status == CapabilityState.NOT_DETECTED


def test_runtime_selector_qnn_explicit_fallback():
    """Requesting Qualcomm QNN on non-Snapdragon host must fall back to CPU with explanation."""
    sel = RuntimeSelector()
    res = sel.select_backend("qualcomm_qnn")

    assert res.requested_backend == "qualcomm_qnn"
    assert res.selected_backend == "cpu"
    assert res.hardware_verified is False
    assert res.fallback_reason is not None
    assert len(res.fallback_reason) > 0
    assert "Snapdragon" in res.fallback_reason or "Non-Snapdragon" in res.fallback_reason
    assert res.execution_providers == ["CPUExecutionProvider"]
    assert sel.is_snapdragon_active() is False
    assert sel.is_npu_active() is False


def test_runtime_selector_cpu_and_auto():
    """Auto and CPU modes select verified CPU execution on current host."""
    sel = RuntimeSelector()

    cpu_res = sel.select_backend("cpu")
    assert cpu_res.selected_backend == "cpu"
    assert cpu_res.hardware_verified is True
    assert cpu_res.fallback_reason is None

    auto_res = sel.select_backend("auto")
    assert auto_res.selected_backend == "cpu"
    assert auto_res.execution_providers == ["CPUExecutionProvider"]


def test_compute_backend_manager_honesty():
    """ComputeBackendManager must report genuine CPU state unless verified."""
    mgr = ComputeBackendManager()
    assert mgr.current_state == BackendState.CPU
    assert "Verified & Active" not in mgr.display_status
    assert "Not Available" in mgr.npu_status or "CPU" in mgr.display_status


def test_capability_states_enum():
    """Verifies all required CapabilityState lifecycle phases."""
    states = [
        CapabilityState.NOT_DETECTED,
        CapabilityState.DETECTED_NOT_AVAILABLE,
        CapabilityState.AVAILABLE_NOT_INITIALIZED,
        CapabilityState.AVAILABLE,
        CapabilityState.VERIFIED_RUNTIME,
    ]
    for s in states:
        assert isinstance(s.value, str)


def test_model_registry_metadata_and_verification_status():
    """Verifies all models declare complete metadata and honest verification."""
    models = model_registry.list_models()
    assert len(models) >= 5

    for m in models:
        assert m.name != ""
        assert m.model_name != ""
        assert m.model_version != ""
        assert m.source != ""
        assert m.license != ""
        assert m.task != ""
        assert m.runtime != ""
        assert m.precision != ""
        assert m.target_hardware != ""
        assert m.execution_provider != ""

        if m.cpu_supported:
            assert "verified_on_current_host" in m.verification_status
            assert "Verified" in m.verification_status
        else:
            assert "pending_genuine_snapdragon_validation" in m.verification_status


def test_synthetic_snapdragon_detection_matrix():
    """Verifies matrix evaluates mock Snapdragon hardware states correctly."""
    class MockDetector:
        def inspect(self, force_refresh=False):
            from hardware.backend_status import HardwareProfile
            return HardwareProfile(
                os_name="Windows 11",
                os_version="10.0.26100",
                architecture="ARM64",
                cpu_model="Snapdragon(R) X Elite - X1E80100",
                ram_gb=32.0,
                gpu_info="Qualcomm Adreno GPU",
                is_snapdragon=True,
                is_npu_available=False,
                npu_name="Qualcomm Hexagon NPU",
                backend_state=BackendState.SNAPDRAGON_CPU,
                status_label="Snapdragon Device Detected",
                npu_status_label="NPU: Not Verified",
                ai_backend_label="Snapdragon CPU",
                raw_details={},
            )

    # When Snapdragon is present but QNN EP is not in ORT
    mock_matrix = CapabilityMatrix()
    # Temporarily patch hardware_detector reference
    import hardware.capability_matrix as cm
    orig_det = cm.hardware_detector
    cm.hardware_detector = MockDetector()
    try:
        mock_matrix.reset()
        caps = mock_matrix.detect()
        assert caps.qualcomm_detected is True
        assert caps.verification_status == CapabilityState.DETECTED_NOT_AVAILABLE
    finally:
        cm.hardware_detector = orig_det


def test_deterministic_score_bounds():
    """Verifies any deterministic fusion score stays strictly in [0.0, 1.0]."""
    from accessibility.geometry import calculate_iou
    from accessibility.evidence_fusion import EvidenceFusionEngine

    engine = EvidenceFusionEngine()

    # Test extreme variations of geometry, text, type, proximity, and focus
    test_cases = [
        (1.0, 1.0, 1.0, 1.0, True),
        (0.0, 0.0, 0.0, 0.0, False),
        (0.5, 0.8, 0.2, 0.4, True),
        (1.0, 0.0, 0.0, 0.0, False),
        (0.0, 1.0, 1.0, 1.0, True),
    ]

    for g, t, c, p, has_focus in test_cases:
        score = engine.calculate_deterministic_score(
            geometry_score=g,
            text_score=t,
            control_type_score=c,
            proximity_score=p,
            has_focus_evidence=has_focus
        )
        assert 0.0 <= score <= 1.0, f"Score {score} out of bounds"

"""Qualcomm Snapdragon QNN Backend for VisionVoice AI.

Architected for Qualcomm Hexagon NPU via ONNX Runtime QNN Execution Provider (QNNExecutionProvider).
Performs capability detection without crashing on non-Snapdragon systems.
"""

from typing import Any, Dict, List, Optional
from ai.base_backend import BaseAIBackend
from hardware.hardware_detector import hardware_detector

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class QualcommBackend(BaseAIBackend):
    """Optional Qualcomm QNN Execution Provider backend."""

    def __init__(self):
        self._qnn_options: Dict[str, Any] = {
            "backend_type": "htp",  # Hexagon Tensor Processor
            "htp_performance_mode": "burst",
            "enable_htp_fp16_precision": "1",
        }

    @property
    def name(self) -> str:
        return "Qualcomm QNN (Snapdragon NPU)"

    @property
    def execution_providers(self) -> List[str]:
        """Preferred execution hierarchy for Snapdragon devices."""
        providers = []
        if self.is_available():
            providers.append("QNNExecutionProvider")
        providers.append("CPUExecutionProvider")
        return providers

    def is_available(self) -> bool:
        """Verifies true hardware and software support for QNN."""
        if ort is None:
            return False

        profile = hardware_detector.inspect()
        if not profile.is_snapdragon:
            return False

        try:
            available = ort.get_available_providers()
            return "QNNExecutionProvider" in available
        except Exception:
            return False

    def get_provider_configuration(self) -> List[Any]:
        """Generates ONNX Runtime provider spec for session creation."""
        if self.is_available():
            return [("QNNExecutionProvider", self._qnn_options), "CPUExecutionProvider"]
        return ["CPUExecutionProvider"]

    def get_status_info(self) -> Dict[str, Any]:
        profile = hardware_detector.inspect()
        is_avail = self.is_available()

        if is_avail:
            status_desc = "Available (Ready for NPU Acceleration)"
            notes = "Target: Qualcomm Hexagon NPU (HTP) on Snapdragon X Series"
        elif profile.is_snapdragon:
            status_desc = "Snapdragon CPU (QNN Provider not registered in ORT)"
            notes = "Snapdragon device detected, but onnxruntime-qnn package is required for NPU."
        else:
            status_desc = "Not Available (Non-Snapdragon Hardware Detected)"
            notes = "Application is running on AMD/Intel architecture. Using CPU fallback."

        return {
            "backend": self.name,
            "status": status_desc,
            "available": is_avail,
            "is_snapdragon_device": profile.is_snapdragon,
            "qnn_provider_registered": "QNNExecutionProvider" in (ort.get_available_providers() if ort else []),
            "target_hardware": "Qualcomm Snapdragon X Elite / X Plus (Hexagon NPU)",
            "notes": notes,
        }

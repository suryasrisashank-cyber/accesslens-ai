"""Hardware capability matrix for AccessLens AI.

Defines explicit multi-state hardware capability assessment for CPU, GPU,
Snapdragon PC platforms, and Qualcomm Hexagon NPU execution providers.
Strictly prevents simulated or fabricated hardware claims.
"""

from dataclasses import dataclass, field
from enum import Enum
import platform
import sys
from typing import Any, Dict, List, Optional

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from hardware.hardware_detector import hardware_detector


class CapabilityState(str, Enum):
    """Explicit multi-state lifecycle for hardware and execution capabilities."""
    NOT_DETECTED = "NOT_DETECTED"
    DETECTED_NOT_AVAILABLE = "DETECTED_NOT_AVAILABLE"
    AVAILABLE_NOT_INITIALIZED = "AVAILABLE_NOT_INITIALIZED"
    AVAILABLE = "AVAILABLE"
    VERIFIED_RUNTIME = "VERIFIED_RUNTIME"


@dataclass
class HardwareCapabilities:
    """Comprehensive, honest capability model for the host platform."""
    cpu_available: bool = True
    gpu_available: bool = False
    npu_available: bool = False
    qualcomm_detected: bool = False
    qnn_available: bool = False
    qnn_runtime_available: bool = False
    supported_execution_providers: List[str] = field(default_factory=list)
    architecture: str = ""
    processor_name: str = ""
    device_name: str = ""
    verification_status: CapabilityState = CapabilityState.NOT_DETECTED
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_available": self.cpu_available,
            "gpu_available": self.gpu_available,
            "npu_available": self.npu_available,
            "qualcomm_detected": self.qualcomm_detected,
            "qnn_available": self.qnn_available,
            "qnn_runtime_available": self.qnn_runtime_available,
            "supported_execution_providers": list(self.supported_execution_providers),
            "architecture": self.architecture,
            "processor_name": self.processor_name,
            "device_name": self.device_name,
            "verification_status": self.verification_status.value,
            "details": self.details,
        }


class CapabilityMatrix:
    """Evaluates and inspects hardware capabilities safely without throwing."""

    def __init__(self):
        self._cached: Optional[HardwareCapabilities] = None

    def detect(self, force_refresh: bool = False) -> HardwareCapabilities:
        """Inspects physical hardware and ONNX Runtime providers safely."""
        if self._cached is not None and not force_refresh:
            return self._cached

        profile = hardware_detector.inspect(force_refresh=force_refresh)

        # 1. Query ONNX Runtime providers safely
        ort_providers: List[str] = []
        qnn_in_ort = False
        if ort is not None:
            try:
                ort_providers = ort.get_available_providers()
                qnn_in_ort = "QNNExecutionProvider" in ort_providers
            except Exception:
                ort_providers = []
                qnn_in_ort = False

        # 2. Query GPU availability
        has_gpu = bool(profile.gpu_info and "standard" not in profile.gpu_info.lower())

        # 3. Determine Qualcomm / Snapdragon detection
        is_snapdragon = profile.is_snapdragon
        arch = profile.architecture
        cpu_name = profile.cpu_model

        # 4. Determine state
        supported_eps = ["CPUExecutionProvider"]

        if is_snapdragon:
            if qnn_in_ort:
                # Genuine Snapdragon hardware with QNN EP registered
                status = CapabilityState.AVAILABLE_NOT_INITIALIZED
                npu_avail = True
                qnn_avail = True
                supported_eps.insert(0, "QNNExecutionProvider")
            else:
                # Snapdragon CPU detected, but QNN execution provider is missing
                status = CapabilityState.DETECTED_NOT_AVAILABLE
                npu_avail = False
                qnn_avail = False
        else:
            # Non-Qualcomm hardware (AMD/Intel x64 development machines)
            status = CapabilityState.NOT_DETECTED
            npu_avail = False
            qnn_avail = False

        details = {
            "os_name": profile.os_name,
            "os_version": profile.os_version,
            "ram_gb": profile.ram_gb,
            "gpu_info": profile.gpu_info,
            "ort_providers": ort_providers,
            "host_is_development_machine": not is_snapdragon,
            "qnn_reason": (
                "Verified on genuine Snapdragon"
                if is_snapdragon and qnn_in_ort
                else "Snapdragon hardware not present on current development host"
            ),
        }

        caps = HardwareCapabilities(
            cpu_available=True,
            gpu_available=has_gpu,
            npu_available=npu_avail,
            qualcomm_detected=is_snapdragon,
            qnn_available=qnn_avail,
            qnn_runtime_available=qnn_avail,
            supported_execution_providers=supported_eps,
            architecture=arch,
            processor_name=cpu_name,
            device_name=platform.node() or "Local Host",
            verification_status=status,
            details=details,
        )

        self._cached = caps
        return caps

    def reset(self) -> None:
        """Clears cached capabilities."""
        self._cached = None


# Singleton instance
capability_matrix = CapabilityMatrix()

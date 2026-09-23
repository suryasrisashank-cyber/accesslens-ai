"""AI runtime provider selector for AccessLens AI.

Evaluates requested execution backend against physical hardware capabilities.
Strictly routes to local CPU fallback when Snapdragon hardware or QNN runtime
is not present, logging explicit fallback rationale.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional

from hardware.capability_matrix import (
    CapabilityMatrix,
    CapabilityState,
    HardwareCapabilities,
    capability_matrix,
)

logger = logging.getLogger(__name__)


@dataclass
class RuntimeSelectionResult:
    """Structured result of backend evaluation and fallback determination."""
    requested_backend: str
    selected_backend: str
    fallback_reason: Optional[str]
    hardware_verified: bool
    execution_providers: List[str] = field(default_factory=list)
    provider_options: Optional[Dict[str, Any]] = None
    capabilities: Optional[HardwareCapabilities] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requested_backend": self.requested_backend,
            "selected_backend": self.selected_backend,
            "fallback_reason": self.fallback_reason,
            "hardware_verified": self.hardware_verified,
            "execution_providers": list(self.execution_providers),
            "provider_options": self.provider_options,
        }


class RuntimeSelector:
    """Selects execution backend with rigorous fallback and zero simulated claims."""

    def __init__(self, matrix: Optional[CapabilityMatrix] = None):
        self._matrix = matrix or capability_matrix
        self._active_selection: Optional[RuntimeSelectionResult] = None

    def select_backend(self, requested: str = "auto") -> RuntimeSelectionResult:
        """Evaluates requested backend against physical capabilities.

        Supported requested modes:
          - 'auto': Selects Qualcomm QNN if genuinely verified, otherwise CPU.
          - 'qualcomm_qnn' / 'qnn' / 'snapdragon': Requests Snapdragon NPU.
          - 'cpu': Requests standard CPU execution provider.
        """
        caps = self._matrix.detect()
        req_norm = requested.strip().lower()

        if req_norm in ("qualcomm_qnn", "qnn", "snapdragon"):
            # Check if genuine Snapdragon hardware AND QNN runtime are active
            can_use_qnn = (
                caps.qualcomm_detected
                and caps.qnn_available
                and caps.verification_status in (
                    CapabilityState.AVAILABLE,
                    CapabilityState.VERIFIED_RUNTIME,
                )
            )

            if can_use_qnn:
                res = RuntimeSelectionResult(
                    requested_backend=requested,
                    selected_backend="qualcomm_qnn",
                    fallback_reason=None,
                    hardware_verified=True,
                    execution_providers=["QNNExecutionProvider", "CPUExecutionProvider"],
                    provider_options={
                        "backend_type": "htp",
                        "htp_performance_mode": "burst",
                        "enable_htp_fp16_precision": "1",
                    },
                    capabilities=caps,
                )
            else:
                reason = "Snapdragon/QNN runtime unavailable on current host"
                if not caps.qualcomm_detected:
                    reason = "Non-Snapdragon host detected (AMD/Intel development machine)"
                elif not caps.qnn_available:
                    reason = "Snapdragon detected, but QNNExecutionProvider is not registered"

                logger.info(
                    "Requested '%s' but falling back to 'cpu': %s", requested, reason
                )
                res = RuntimeSelectionResult(
                    requested_backend=requested,
                    selected_backend="cpu",
                    fallback_reason=reason,
                    hardware_verified=False,
                    execution_providers=["CPUExecutionProvider"],
                    provider_options=None,
                    capabilities=caps,
                )
        elif req_norm == "cpu":
            res = RuntimeSelectionResult(
                requested_backend=requested,
                selected_backend="cpu",
                fallback_reason=None,
                hardware_verified=True,
                execution_providers=["CPUExecutionProvider"],
                provider_options=None,
                capabilities=caps,
            )
        else:  # 'auto'
            if (
                caps.qualcomm_detected
                and caps.qnn_available
                and caps.verification_status in (
                    CapabilityState.AVAILABLE,
                    CapabilityState.VERIFIED_RUNTIME,
                )
            ):
                res = RuntimeSelectionResult(
                    requested_backend=requested,
                    selected_backend="qualcomm_qnn",
                    fallback_reason=None,
                    hardware_verified=True,
                    execution_providers=["QNNExecutionProvider", "CPUExecutionProvider"],
                    provider_options={
                        "backend_type": "htp",
                        "htp_performance_mode": "burst",
                        "enable_htp_fp16_precision": "1",
                    },
                    capabilities=caps,
                )
            else:
                res = RuntimeSelectionResult(
                    requested_backend=requested,
                    selected_backend="cpu",
                    fallback_reason=(
                        "Auto-selected CPU: Snapdragon NPU not detected or unverified"
                        if not caps.qualcomm_detected
                        else None
                    ),
                    hardware_verified=True,  # CPU is genuine and verified on current host
                    execution_providers=["CPUExecutionProvider"],
                    provider_options=None,
                    capabilities=caps,
                )

        self._active_selection = res
        return res

    @property
    def current_selection(self) -> RuntimeSelectionResult:
        if self._active_selection is None:
            self._active_selection = self.select_backend("auto")
        return self._active_selection

    def is_snapdragon_active(self) -> bool:
        """Returns True ONLY if selected backend is genuine, verified Snapdragon."""
        sel = self.current_selection
        return sel.selected_backend == "qualcomm_qnn" and sel.hardware_verified

    def is_npu_active(self) -> bool:
        """Returns True ONLY if Qualcomm Hexagon NPU is actively executing."""
        return self.is_snapdragon_active()

    def get_active_summary(self) -> Dict[str, Any]:
        sel = self.current_selection
        return {
            "selected_backend": sel.selected_backend,
            "hardware_verified": sel.hardware_verified,
            "fallback_active": sel.fallback_reason is not None,
            "fallback_reason": sel.fallback_reason,
            "execution_providers": sel.execution_providers,
            "architecture": sel.capabilities.architecture if sel.capabilities else "",
            "processor": sel.capabilities.processor_name if sel.capabilities else "",
        }


# Singleton instance
runtime_selector = RuntimeSelector()

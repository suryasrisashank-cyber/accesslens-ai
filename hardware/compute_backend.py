"""Compute backend manager for VisionVoice AI.

Selects appropriate execution provider:
1. QNN / Snapdragon NPU when genuinely available and verified
2. Snapdragon CPU
3. Standard CPU Fallback
"""

from typing import List, Optional
from hardware.backend_status import BackendState, HardwareProfile
from hardware.hardware_detector import hardware_detector


class ComputeBackendManager:
    """Manages AI runtime provider selection and verification state."""

    def __init__(self):
        self._profile: HardwareProfile = hardware_detector.inspect()
        self._npu_verified: bool = False
        self._verification_evidence: Optional[str] = None

    @property
    def profile(self) -> HardwareProfile:
        return self._profile

    @property
    def current_state(self) -> BackendState:
        if self._npu_verified:
            return BackendState.SNAPDRAGON_NPU_VERIFIED
        return self._profile.backend_state

    @property
    def display_status(self) -> str:
        if self._npu_verified:
            return "Snapdragon NPU: Verified & Active"
        return self._profile.status_label

    @property
    def npu_status(self) -> str:
        if self._npu_verified:
            return "NPU: VERIFIED"
        return self._profile.npu_status_label

    def get_preferred_providers(self) -> List[str]:
        """Returns the prioritized ONNX Runtime execution provider list.

        Priority order:
        1. QNNExecutionProvider (when Snapdragon NPU is genuinely present)
        2. CPUExecutionProvider
        """
        providers = []
        if self._profile.is_npu_available:
            providers.append("QNNExecutionProvider")
        providers.append("CPUExecutionProvider")
        return providers

    def record_npu_verification(self, evidence: str) -> None:
        """Records genuine runtime evidence of NPU execution.

        Never called unless actual QNN provider execution succeeded without error.
        """
        self._npu_verified = True
        self._verification_evidence = evidence

    def reset_verification(self) -> None:
        self._npu_verified = False
        self._verification_evidence = None


# Singleton instance
backend_manager = ComputeBackendManager()

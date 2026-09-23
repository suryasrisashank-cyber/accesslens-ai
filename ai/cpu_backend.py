"""CPU execution backend for VisionVoice AI.

Provides standard reliable on-device execution on x86_64, AMD Ryzen,
Intel, and ARM CPUs using ONNX Runtime CPUExecutionProvider.
"""

from typing import Any, Dict, List
from ai.base_backend import BaseAIBackend

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class CPUBackend(BaseAIBackend):
    """Local CPU execution provider."""

    @property
    def name(self) -> str:
        return "CPU Execution Provider"

    @property
    def execution_providers(self) -> List[str]:
        return ["CPUExecutionProvider"]

    def is_available(self) -> bool:
        """CPU fallback is always available when ONNX Runtime is installed."""
        return ort is not None

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "backend": self.name,
            "status": "Active (Local CPU Fallback)",
            "available": self.is_available(),
            "ort_version": ort.__version__ if ort else "Not Installed",
            "device": "System CPU",
            "notes": "Reliable baseline execution across any Windows computer."
        }

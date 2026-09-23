"""Backend status and hardware states for VisionVoice AI.

Provides honest enum types and status dataclasses to prevent false claims of
NPU execution or artificial hardware acceleration.
"""

from dataclasses import dataclass
from enum import Enum


class BackendState(str, Enum):
    """Execution backend state categories."""
    CPU = "CPU"
    SNAPDRAGON_CPU = "SNAPDRAGON_CPU"
    SNAPDRAGON_NPU_AVAILABLE = "SNAPDRAGON_NPU_AVAILABLE"
    SNAPDRAGON_NPU_VERIFIED = "SNAPDRAGON_NPU_VERIFIED"
    UNKNOWN = "UNKNOWN"


@dataclass
class HardwareProfile:
    """Comprehensive hardware inspection snapshot."""
    os_name: str
    os_version: str
    architecture: str
    cpu_model: str
    ram_gb: float
    gpu_info: str
    is_snapdragon: bool
    is_npu_available: bool
    npu_name: str
    backend_state: BackendState
    status_label: str
    npu_status_label: str
    ai_backend_label: str
    raw_details: dict

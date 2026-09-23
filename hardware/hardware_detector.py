"""Hardware detector for VisionVoice AI.

Inspects system hardware (CPU, RAM, OS, GPU, architecture) and evaluates
Snapdragon and Qualcomm Hexagon NPU presence honestly without fabrication.
"""

import os
import platform
import subprocess
import sys
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from hardware.backend_status import BackendState, HardwareProfile


class HardwareDetector:
    """Inspects underlying physical hardware and reports execution readiness."""

    def __init__(self):
        self._cached_profile: Optional[HardwareProfile] = None

    def get_cpu_info(self) -> str:
        """Retrieves user-friendly CPU model string on Windows."""
        # 1. Try Windows Registry for clean friendly name
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
                )
                processor_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                winreg.CloseKey(key)
                if processor_name and processor_name.strip():
                    return processor_name.strip()
            except Exception:
                pass

        # 2. Try platform.processor() or platform.machine()
        proc = platform.processor()
        if proc and proc.strip():
            return proc.strip()

        return platform.machine() or "Unknown CPU"

    def get_gpu_info(self) -> str:
        """Inspects available display adapter/GPU on Windows."""
        if sys.platform == "win32":
            try:
                cmd = "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if res.returncode == 0 and res.stdout.strip():
                    gpus = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
                    return ", ".join(gpus)
            except Exception:
                pass
        return "Standard Display Adapter"

    def is_snapdragon_device(self, cpu_info: str, arch: str) -> bool:
        """Determines if current platform is a Qualcomm Snapdragon PC."""
        cpu_lower = cpu_info.lower()
        snapdragon_indicators = [
            "snapdragon", "qualcomm", "sc8380", "sc8280", "x1e", "x1p", "kryo", "oryon"
        ]
        is_arm = "arm" in arch.lower() or "aarch64" in arch.lower()
        has_snap_name = any(ind in cpu_lower for ind in snapdragon_indicators)
        return is_arm and has_snap_name

    def check_qnn_available(self) -> tuple[bool, str]:
        """Checks if Qualcomm Neural Processing Engine (QNN) is genuinely available."""
        if ort is None:
            return False, "ONNX Runtime not installed"

        try:
            available_providers = ort.get_available_providers()
            if "QNNExecutionProvider" in available_providers:
                return True, "QNNExecutionProvider is registered in ONNX Runtime"
            return False, "QNNExecutionProvider not registered in ONNX Runtime"
        except Exception as e:
            return False, f"Provider detection failed: {e}"

    def inspect(self, force_refresh: bool = False) -> HardwareProfile:
        """Performs full hardware diagnosis and returns HardwareProfile."""
        if self._cached_profile is not None and not force_refresh:
            return self._cached_profile

        os_name = f"{platform.system()} {platform.release()}"
        os_version = platform.version()
        arch = platform.machine()
        cpu_model = self.get_cpu_info()
        gpu_info = self.get_gpu_info()

        ram_gb = 0.0
        if psutil is not None:
            ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)

        is_snapdragon = self.is_snapdragon_device(cpu_model, arch)
        qnn_available, qnn_reason = self.check_qnn_available()

        # Strictly determine honest backend states
        if is_snapdragon:
            if qnn_available:
                backend_state = BackendState.SNAPDRAGON_NPU_AVAILABLE
                status_label = "Snapdragon Device Detected"
                npu_status_label = "Snapdragon NPU: Available (Pending Verification)"
                ai_backend_label = "QNN Execution Provider (Snapdragon NPU)"
                npu_name = "Qualcomm Hexagon NPU"
            else:
                backend_state = BackendState.SNAPDRAGON_CPU
                status_label = "Snapdragon Device Detected"
                npu_status_label = "NPU: Not Verified"
                ai_backend_label = "Snapdragon CPU Fallback"
                npu_name = "Qualcomm Hexagon (Unregistered Provider)"
        else:
            backend_state = BackendState.CPU
            status_label = "CPU Processing"
            npu_status_label = "Snapdragon NPU: Not Available"
            ai_backend_label = "CPU fallback"
            npu_name = "None (Non-Qualcomm Hardware)"

        raw_details = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "ort_providers": ort.get_available_providers() if ort else [],
            "qnn_reason": qnn_reason,
        }

        profile = HardwareProfile(
            os_name=os_name,
            os_version=os_version,
            architecture=arch,
            cpu_model=cpu_model,
            ram_gb=ram_gb,
            gpu_info=gpu_info,
            is_snapdragon=is_snapdragon,
            is_npu_available=qnn_available and is_snapdragon,
            npu_name=npu_name,
            backend_state=backend_state,
            status_label=status_label,
            npu_status_label=npu_status_label,
            ai_backend_label=ai_backend_label,
            raw_details=raw_details
        )
        self._cached_profile = profile
        return profile


# Singleton instance
hardware_detector = HardwareDetector()

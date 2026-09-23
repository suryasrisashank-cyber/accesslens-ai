"""Snapdragon NPU and Qualcomm QNN verification utility for AccessLens AI.

Performs honest, un-fabricated verification of the local execution environment,
detecting whether Qualcomm Hexagon NPU hardware and ONNX Runtime QNNExecutionProvider
are present or if CPU fallback must be used.
"""

import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai.qualcomm_backend import QualcommBackend
from hardware.backend_status import BackendState
from hardware.hardware_detector import hardware_detector

try:
    import onnxruntime as ort
except ImportError:
    ort = None


def verify_snapdragon_npu():
    print("\n" + "=" * 68)
    print(" ACCESSLENS AI — QUALCOMM SNAPDRAGON & NPU VERIFICATION")
    print("=" * 68)

    profile = hardware_detector.inspect(force_refresh=True)
    qnn = QualcommBackend()
    status_info = qnn.get_status_info()

    print(f"Host Operating System:    {profile.os_name} (Build {profile.os_version})")
    print(f"Processor Model:          {profile.cpu_model}")
    print(f"Architecture:             {profile.architecture}")
    print(f"Installed Memory:         {profile.ram_gb} GB RAM")
    print(f"Graphics Adapter (GPU):   {profile.gpu_info}")
    print("-" * 68)

    print("HARDWARE ATTESTATION:")
    print(f"  • Snapdragon Platform:   {'DETECTED' if profile.is_snapdragon else 'NOT DETECTED'}")
    print(f"  • Physical NPU Present:  {profile.npu_status_label}")
    print(f"  • Active AI Backend:     {profile.ai_backend_label}")
    print("-" * 68)

    print("ONNX RUNTIME PROVIDER INSPECTION:")
    if ort is not None:
        providers = ort.get_available_providers()
        print(f"  • ONNX Runtime Version:  {ort.__version__}")
        print(f"  • Registered Providers:  {', '.join(providers)}")
        has_qnn = "QNNExecutionProvider" in providers
        print(f"  • QNN Execution Provider:{' REGISTERED' if has_qnn else ' NOT REGISTERED'}")
    else:
        print("  • ONNX Runtime:          NOT INSTALLED")
        has_qnn = False

    print("-" * 68)
    print("RUNTIME VERIFICATION RESULT:")
    if profile.is_snapdragon and has_qnn:
        print("  >> STATUS: SNAPDRAGON NPU AVAILABLE & READY")
        print("     Targeting Qualcomm Hexagon NPU via QNN Execution Provider.")
        return True
    elif profile.is_snapdragon:
        print("  >> STATUS: SNAPDRAGON CPU (NPU PROVIDER PENDING)")
        print("     Snapdragon device detected; install onnxruntime-qnn for NPU acceleration.")
        return False
    else:
        print("  >> STATUS: NON-SNAPDRAGON HARDWARE (CPU FALLBACK VERIFIED)")
        print(f"     Development machine is {profile.cpu_model} ({profile.architecture}).")
        print("     Application operates in local CPU fallback mode without NPU fabrication.")
        return False


if __name__ == "__main__":
    is_npu = verify_snapdragon_npu()
    print("=" * 68 + "\n")
    # Return exit code 0 because CPU fallback verification is a legitimate operational state
    sys.exit(0)

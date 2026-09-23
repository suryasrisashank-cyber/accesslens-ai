# AccessLens AI — Qualcomm Snapdragon & NPU Validation Guide

**Project:** AccessLens AI  
**Author:** AccessLens Hardware & AI Systems Engineering  
**Integrity Rule:** No simulated or fabricated NPU results. Only report verified execution.

---

## 1. Current Development Environment Baseline

All development, debugging, and initial benchmark measurements were executed on:
- **Host Processor:** AMD Ryzen 3 2200U with Radeon Vega Mobile Gfx
- **Architecture:** AMD64 (x86_64)
- **Host OS:** Microsoft Windows 10 Home (Build 10.0.19045)
- **Physical Memory:** 7.64 GB RAM
- **Active Backend:** ONNX Runtime `CPUExecutionProvider` (Local CPU Fallback)
- **NPU Status:** Not Available (Non-Qualcomm Hardware)

### Actual Baseline Measurements (Local CPU Fallback)
Measured via `python scripts/benchmark.py` (single-pass sequential pipeline execution):
- **Average On-Device OCR Latency (RapidOCR):** 4,516.77 ms
- **Average Scene & Layout Understanding Latency:** 4.83 ms
- **Average Audit, Rules & Evidence Fusion Latency:** 24.83 ms
- **Average Multi-Format Report Generation Latency:** 16.00 ms
- **Average Total Sequential Pipeline Latency:** 4,562.45 ms
- **Average Host Process Memory (RSS):** 111.23 MB

---

## 2. Target Platform: Snapdragon Deployment Target

The target deployment hardware for AccessLens AI comprises modern Windows 11 Copilot+ PCs powered by Qualcomm Snapdragon X Series platforms:
- **Processor:** Qualcomm Snapdragon X Series target (Snapdragon X Elite, Snapdragon X Plus).
- **Architecture:** ARM64 / ARM64EC target environment.
- **Snapdragon Detection:** To be verified on genuine Snapdragon hardware.
- **NPU:** Expected Qualcomm Hexagon NPU target.
- **QNN:** Target deployment backend (`QNNExecutionProvider`).
- **NPU Performance:** Not measured on current AMD development machine.
- **Hardware Validation:** Pending genuine Snapdragon hardware validation.
- **45 TOPS Hardware Rating:** Platform hardware specification rating only; do not present as a measured AccessLens result.

---

## 3. QNN Integration Architecture

AccessLens AI abstracts Qualcomm execution through `ai/qualcomm_backend.py` using ONNX Runtime's official `QNNExecutionProvider`:

```python
# Provider configuration in ai/qualcomm_backend.py
qnn_options = {
    "backend_type": "htp",               # Qualcomm Hexagon Tensor Processor
    "htp_performance_mode": "burst",      # Maximizes NPU clock frequency during audit
    "enable_htp_fp16_precision": "1",    # FP16 acceleration mode
}

session = ort.InferenceSession(
    "model.onnx",
    providers=[("QNNExecutionProvider", qnn_options), "CPUExecutionProvider"]
)
```

### Execution Priority Hierarchy
1. `QNNExecutionProvider`: Offloads OCR text detection, recognition, and layout segmentation to the Qualcomm Hexagon NPU.
2. `CPUExecutionProvider`: Falls back to the host CPU (Qualcomm Oryon or x86 host) if the NPU is busy or a specific tensor op is un-quantized.

---

## 4. Procedure for Real Snapdragon Hardware Verification

When migrating AccessLens AI to a Snapdragon X Series PC (or testing via Qualcomm Device Cloud):

### Step 1: Install Qualcomm NPU Drivers & Runtime
Ensure the Qualcomm Hexagon NPU driver package and ARM64 ONNX Runtime with QNN are installed:
```powershell
pip install onnxruntime-qnn --extra-index-url https://aihub.qualcomm.com/wheels/
```

### Step 2: Run Verification Utility
Execute the dedicated hardware verifier:
```powershell
python scripts/verify_snapdragon_npu.py
```
**Expected Output on Snapdragon X Series Device:**
```
Host Processor:           Qualcomm Snapdragon X Series (ARM64)
Snapdragon Platform:      DETECTED (Verified on genuine Snapdragon hardware)
Physical NPU Present:     Qualcomm Hexagon NPU (Hardware spec: up to 45 TOPS; not a measured AccessLens result)
QNN Execution Provider:   Target deployment backend (REGISTERED)
RUNTIME VERIFICATION:    STATUS: SNAPDRAGON NPU AVAILABLE & READY
```

### Step 3: Run Full Accessibility Benchmark on NPU
```powershell
python scripts/benchmark.py
```
Record genuine NPU latency and offload ratios once deployed. The results will automatically be labeled as `SNAPDRAGON NPU RESULT`.

---

## 5. Limitations

1. **Host Architecture Independence**: Current benchmarks reflect CPU execution on an AMD Ryzen development machine. NPU performance has not been measured on the current AMD host and hardware validation is pending genuine Snapdragon hardware validation.
2. **45 TOPS Hardware Rating**: The 45 TOPS figure represents the manufacturer hardware specification rating for the Snapdragon X Series Hexagon NPU; it is not a measured AccessLens result. INT8 model quantization through Qualcomm AI Hub / QNN SDK is recommended to achieve peak hardware potential.

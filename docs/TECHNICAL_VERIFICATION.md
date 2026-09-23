# AccessLens AI — Technical Verification Report
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**Project:** AccessLens AI  
**Tagline:** *"See. Understand. Listen."*  
**Host Platform:** Windows 10 (AMD64 / x64 Host)  
**Verification Date:** September 2026

---

## 1. Machine & Environment Information

| Property | Value | Notes |
|---|---|---|
| **Host Processor** | AMD Ryzen 3 2200U with Radeon Vega Mobile Gfx | Dual-core, 4-thread mobile x86_64 processor |
| **Instruction Architecture** | AMD64 / x86_64 | 64-bit Windows execution environment |
| **System Memory** | 7.64 GB RAM | Low-profile development machine |
| **Operating System** | Windows 10 (Build 10.0.19045) | Native Windows Desktop APIs (COM UIA, SAPI) |
| **Python Version** | Python 3.14.6 | Standard 64-bit CPython runtime |
| **Active Inference Backend** | `CPUExecutionProvider` | Local ONNX Runtime CPU execution provider |
| **Snapdragon Hardware** | **NOT DETECTED** | Physical Snapdragon SoC is not present |
| **Qualcomm Hexagon NPU** | **NOT AVAILABLE ON CURRENT DEVELOPMENT HOST** | No physical NPU silicon accessible |

---

## 2. Dependency Information

Key verified Python packages from the environment:
- `PySide6`: 6.11.2 (Qt GUI Framework)
- `rapidocr-onnxruntime`: 1.2.3 (Local text detection and recognition)
- `onnxruntime`: 1.30.0 (ONNX Runtime engine)
- `numpy`: 2.5.1 (Array operations and coordinate calculations)
- `pillow`: 12.3.0 (Image analysis and crop buffer handling)
- `psutil`: 7.2.2 (Process memory telemetry)
- `pytest`: 9.1.1 (Automated test runner)

---

## 3. Test Suite Verification Results

- **Command:** `python -m pytest tests/ -q`
- **Result:** **211/211 automated tests passed in the verified test run (0 failures).**
- **Duration:** ~18–24 seconds across 17 test modules.
- **Coverage Areas:** Windows UI Automation tree extraction, RapidOCR bounding, deterministic WCAG 2.1 AA rules, active keyboard focus traversal, bipartite evidence fusion, local reasoning, sensitive-data redaction, report generation, thread safety, and hardware honesty.

---

## 4. Project Validation Results

- **Command:** `python scripts/validate_project.py`
- **Output:**
  - `[PASS] Project structure`
  - `[PASS] Python imports`
  - `[PASS] Hardware detection & Capability Matrix`
  - `[PASS] AI backend & Local Reasoning`
  - `[PASS] Keyboard Navigation & Focus Traversal`
  - `[PASS] Multimodal Evidence Fusion`
  - `[PASS] Accessibility Reports & Multimodal Export`
  - `[PASS] OCR module`
  - `[PASS] Image analyzer`
  - `[PASS] TTS`
  - `[PASS] Privacy`
  - `[PASS] Tests`
- **Status:** **FINAL STATUS: READY**

---

## 5. Verified AMD CPU Baseline Benchmark

- **Command:** `python scripts/benchmark.py`
- **Benchmark Type:** `REAL LOCAL AMD CPU BASELINE`
- **Measurement Method:** Single-pass sequential additive wall-clock execution across 4 standardized sample interfaces.

| Metric | Result |
|---|---:|
| CPU | AMD Ryzen 3 2200U |
| Architecture | AMD64/x64 |
| Backend | CPUExecutionProvider |
| OCR | 4760.83 ms |
| Scene/Layout | 15.19 ms |
| Audit/Rules/Evidence Fusion | 29.10 ms |
| Report Generation | 180.08 ms |
| Total Sequential Pipeline | 4985.20 ms |
| Process Memory | 115.42 MB |

*These measurements were obtained on the AMD Ryzen 3 2200U development system using CPUExecutionProvider. They are not Snapdragon performance measurements.*

---

## 6. Technical Limitations & Boundary Disclosures

1. **Host Silicon:** All benchmarks reflect the AMD Ryzen 3 2200U processor. Snapdragon NPU execution has not been measured on the current host.
2. **QNN Validation:** Architecture targeting `QNNExecutionProvider` on the Qualcomm Hexagon NPU is implemented in `ai/qualcomm_backend.py`, but genuine physical hardware validation remains pending.
3. **Automated QA Assistance:** AccessLens AI findings are QA assistance results requiring human verification; they do not constitute formal legal accessibility compliance certificates.
4. **Local Heuristic Redaction:** Sensitive data masking is pattern-based and should be reviewed prior to external sharing.

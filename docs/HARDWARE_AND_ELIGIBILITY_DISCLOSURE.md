# AccessLens AI — Hardware & Eligibility Disclosure
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**Project:** AccessLens AI  
**Tagline:** *"See the interface. Understand the barriers. Fix them locally."*  
**Date of Attestation:** September 2026

---

## 1. Development Host Hardware Disclosure

AccessLens AI was developed, tested, and validated on the following physical host hardware:

| Parameter | Host Specification | Notes / Attestation |
|---|---|---|
| **CPU Model** | AMD Ryzen 3 2200U with Radeon Vega Mobile Gfx | Dual-core, 4-thread mobile x86_64 processor |
| **Instruction Architecture** | AMD64 / x86_64 | 64-bit Windows execution environment |
| **System Memory** | 7.64 GB RAM Available | Standard low-profile development laptop |
| **Operating System** | Windows 10 (10.0.19045) | Native Windows Desktop APIs (COM UIA, SAPI) |
| **Active AI Inference Backend** | `CPUExecutionProvider` | ONNX Runtime CPU execution provider |
| **Snapdragon Hardware** | **NOT DETECTED** | Physical Snapdragon SoC is not present |
| **Qualcomm Hexagon NPU** | **NOT AVAILABLE** | No physical NPU silicon accessible |
| **Measured Snapdragon Benchmark** | **NOT AVAILABLE** | Zero simulated or fabricated Snapdragon metrics |

---

## 2. Technical Stance on Qualcomm Snapdragon & QNN

To ensure maximum integrity and avoid disqualification:

1. **No Hardware Claim:** The authors do not claim that AccessLens AI was benchmarked on physical Qualcomm Snapdragon hardware during development.
2. **No Fabricated Benchmarks:** All performance metrics reported in documentation, presentations, and benchmarks were measured on the host AMD Ryzen 3 2200U CPU. No synthetic TOPS or estimated millisecond values are attributed to Qualcomm silicon.
3. **Architectural Readiness:** The codebase contains a fully realized, test-covered Qualcomm neural processing integration layer:
   - Module: [`ai/qualcomm_backend.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/ai/qualcomm_backend.py)
   - Execution Provider Target: `QNNExecutionProvider` targeting the Qualcomm Hexagon NPU.
   - Provider Configuration: HTP backend type, burst performance mode, FP16 precision.
   - Fallback Mechanism: [`ai/runtime_selector.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/ai/runtime_selector.py) detects hardware environment at launch and gracefully routes to `CPUExecutionProvider` on non-Snapdragon systems.
4. **Verification Status in Registry:** In [`ai/model_registry.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/ai/model_registry.py), local CPU models are marked `"Verified on current AMD CPU development host (verified_on_current_host)"`, while Qualcomm NPU configurations are transparently marked `"Qualcomm-targeted model configuration — pending genuine Snapdragon validation (pending_genuine_snapdragon_validation)"`.

---

## 3. Eligibility & Competition Attestation

AccessLens AI complies with all challenge guidelines for the Qualcomm Snapdragon AI Lab Build & Present Challenge 2026:

- **Original Work:** AccessLens AI is an original software application designed and built for this challenge.
- **Local Privacy Guarantee:** All inference, image analysis, UI automation extraction, and report generation execute locally on the host machine without paid cloud services or mandatory internet access.
- **Reproducibility:** Evaluators on any Windows machine can verify the complete system using the automated test suite (`python -m pytest tests/`), the project validator (`python scripts/validate_project.py`), the AMD baseline benchmark (`python scripts/benchmark.py`), or the offline demo workflow (`python scripts/run_demo.py`).

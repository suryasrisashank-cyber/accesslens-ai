# AccessLens AI — Migration Baseline & Project Audit

**Document Date:** September 22, 2026  
**Auditor:** AccessLens Lead Architect & QA Engineering  
**Project Path:** `C:\Users\MAHADEV\.gemini\antigravity\scratch\visionvoice`  
**Upgrade Target:** Transform VisionVoice AI into **AccessLens AI** (*"See the interface. Understand the barriers. Fix them locally."*)

---

## 1. Current Architecture

The existing VisionVoice AI application is organized into clean, modular Python packages adhering to local-first desktop design:

```
visionvoice/
├── app/
│   ├── main.py                         # PySide6 application entrypoint
│   ├── ui/
│   │   ├── main_window.py              # Main dashboard with dark theme & 5 tabs
│   │   ├── components.py               # Custom UI cards, badges, image preview canvas
│   │   ├── hardware_view.py            # Honest hardware diagnostics view
│   │   ├── performance_view.py         # Local CPU benchmark display
│   │   └── history_view.py             # SQLite history log viewer
│   └── workers/
│       └── analysis_worker.py          # Background QThread for non-blocking AI/OCR
│
├── ai/
│   ├── base_backend.py                 # Abstract base class for compute backends
│   ├── cpu_backend.py                  # ONNX Runtime CPUExecutionProvider implementation
│   ├── qualcomm_backend.py             # Snapdragon NPU / QNN Execution Provider interface
│   └── model_registry.py               # Documented model registry with licenses & targets
│
├── vision/
│   ├── ocr_engine.py                   # Local RapidOCR ONNX Runtime engine + fallback
│   ├── image_analyzer.py               # Local multimodal scene, UI & text summarizer
│   ├── screen_capture.py               # Cross-monitor accessible screen grabber
│   └── image_utils.py                  # Image conversion, bounding boxes & scaling
│
├── audio/
│   └── text_to_speech.py               # Windows System.Speech SAPI speech synthesizer
│
├── hardware/
│   ├── hardware_detector.py            # Real hardware inspection (OS, CPU, RAM, GPU, NPU)
│   ├── compute_backend.py              # Backend manager & execution provider selector
│   └── backend_status.py               # Backend status enums & state definitions
│
├── privacy/
│   └── privacy_manager.py              # Local processing verification & temp file cleanup
│
├── storage/
│   └── database.py                     # SQLite history store (metadata only, no images)
│
├── demo/
│   └── samples/                        # Synthetic demo images (University, Menu, Label, Desktop)
│
├── scripts/
│   ├── validate_project.py             # Automated readiness checklist
│   ├── benchmark.py                    # Local CPU benchmark runner
│   ├── generate_demo_samples.py        # Generates test images
│   └── run_demo.py                     # 60-90 second guided presentation script
│
├── tests/                              # Comprehensive pytest suite (26 passing tests)
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 2. Current Features

| Component / Feature | Operational Status | Underlying Technology |
| :--- | :--- | :--- |
| **PySide6 Desktop UI** | Verified Functional | PySide6 6.11.2 with custom dark high-contrast theme |
| **Open Image File** | Verified Functional | Supports PNG, JPG, JPEG, WEBP, BMP |
| **Desktop Screen Capture** | Verified Functional | Multi-monitor capture via `QScreen.grabWindow(0)` |
| **On-Device OCR** | Verified Functional | `RapidOCR` using local `onnxruntime` models |
| **Multimodal Scene Analyzer** | Verified Functional | Layout segmentation, category & CTA extraction |
| **Read Aloud (TTS)** | Verified Functional | Windows native `System.Speech.Synthesis.SpeechSynthesizer` |
| **Hardware Detection** | Verified Functional | `platform`, `psutil`, Windows Registry, CIM |
| **CPU Backend Fallback** | Verified Functional | ONNX Runtime `CPUExecutionProvider` |
| **Qualcomm Backend Abstraction** | Verified Functional | Capability detector prioritizing `QNNExecutionProvider` |
| **Model Registry** | Verified Functional | Metadata, licenses (Apache-2.0, MIT), tasks, targets |
| **Privacy Manager** | Verified Functional | Ephemeral screenshot lifecycle & automatic purge |
| **SQLite History Store** | Verified Functional | Schema stores timestamp, type, summary, backend |
| **Performance Benchmark** | Verified Functional | Measures OCR, analysis, latency, process RAM |
| **Project Validation Script** | Verified Functional | Automated checklist passing all 9 modules |
| **Synthetic Demo Assets** | Verified Functional | 4 pre-rendered accessible test scenarios |

---

## 3. Current Test Results

Executed command:
```powershell
python -m pytest tests/ -v
```

**Real Result:** `26 passed in 8.78s` across 10 test modules.
- `tests/test_analyzer.py`: 3/3 passed (interface structure, category detection, signals)
- `tests/test_backend.py`: 3/3 passed (CPU backend, Qualcomm backend, compute manager)
- `tests/test_database.py`: 2/2 passed (add/get record, clear history)
- `tests/test_edge_cases.py`: 4/4 passed (blank white, blank black, nonexistent file, corrupted file)
- `tests/test_hardware.py`: 3/3 passed (profile inspect, honesty on AMD, Snapdragon matching logic)
- `tests/test_imports.py`: 1/1 passed (all packages import cleanly)
- `tests/test_ocr.py`: 2/2 passed (result structure, synthetic OCR extraction)
- `tests/test_privacy.py`: 3/3 passed (statement, temp file purge, cleanup all)
- `tests/test_screen_capture.py`: 2/2 passed (primary screen capture, temp file capture)
- `tests/test_tts.py`: 3/3 passed (initialization, rate/volume clamping, stop control)

---

## 4. Current Benchmark Measurements

Executed command:
```powershell
python scripts/benchmark.py
```

**Host Platform:** AMD Ryzen 3 2200U with Radeon Vega Mobile Gfx (AMD64, Windows 10)  
**AI Backend:** Local CPU Fallback (`CPUExecutionProvider`)  
**Snapdragon NPU:** Not Available

| Sample Name | OCR Latency | Analysis Latency | Total Latency | Process RAM | Recognized Words | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `university_admission.png` | 5,017.57 ms | 31.16 ms | 5,048.73 ms | 107.52 MB | 47 | 91.3% |
| `restaurant_menu.png` | 4,767.95 ms | 9.54 ms | 4,777.48 ms | 109.58 MB | 79 | 91.3% |
| `product_label.png` | 4,146.67 ms | 8.00 ms | 4,154.67 ms | 109.38 MB | 85 | 90.2% |
| `desktop_screenshot.png` | 4,979.04 ms | 8.22 ms | 4,987.26 ms | 107.86 MB | 70 | 88.1% |
| **Averages (Local CPU)** | **4,727.81 ms** | **14.23 ms** | **4,742.03 ms** | **~108.5 MB** | — | **90.2%** |

*Note: Measurements reflect local CPU execution on standard x86 laptop hardware. Snapdragon NPU acceleration is not claimed.*

---

## 5. Current Hardware Detection

Executed command:
```powershell
python -c "from hardware.hardware_detector import hardware_detector; p = hardware_detector.inspect(); print(p)"
```

**Actual Detected Output:**
- **OS:** Windows 10 (Build 10.0.19045)
- **Architecture:** AMD64
- **CPU Model:** AMD Ryzen 3 2200U with Radeon Vega Mobile Gfx
- **System Memory:** 7.64 GB RAM
- **GPU:** AMD Radeon(TM) Vega 3 Graphics
- **Snapdragon Detected:** `False`
- **NPU Available:** `False`
- **Backend State:** `BackendState.CPU`
- **Status Label:** `"CPU Processing"`
- **NPU Status Label:** `"Snapdragon NPU: Not Available"`
- **AI Backend Label:** `"CPU fallback"`

---

## 6. Current Qualcomm / QNN Code Status

1. **`ai/qualcomm_backend.py`**:
   - **Real:** Accurately queries `onnxruntime.get_available_providers()` for `"QNNExecutionProvider"`. Validates that host processor is ARM64 Snapdragon before attempting activation.
   - **Abstraction:** Defines the exact provider options dictionary for Qualcomm HTP (`backend_type: htp`, `htp_performance_mode: burst`, `enable_htp_fp16_precision: 1`).
   - **Unverified on Current Machine:** QNN execution cannot be verified on this AMD Ryzen laptop because the physical hardware and Qualcomm QNN runtime are absent. The fallback to `CPUExecutionProvider` is verified.
2. **`hardware/compute_backend.py`**:
   - Manages execution provider hierarchy: `QNNExecutionProvider` -> `CPUExecutionProvider`.
   - Strictly records `NPU: VERIFIED` only upon genuine runtime execution evidence.
3. **`ai/model_registry.py`**:
   - Catalogs models (`ch_PP-OCRv4_det`, `ch_ppocr_mobile_v2.0_cls`, `ch_PP-OCRv4_rec`, `VisionVoice-LayoutAnalyzer`).
   - All models document target hardware as CPU and Qualcomm Hexagon NPU.

---

## 7. Current Weaknesses & Gaps for AccessLens

1. **Missing Windows UI Automation**: VisionVoice only examines bitmap pixels. It cannot query the Windows Accessibility Tree (roles, states, accessible names, focus status, or automation IDs).
2. **Missing Deterministic Accessibility Rules**: There is no engine to flag missing accessible names, visible-vs-accessible label discrepancies, color contrast violations, or small target sizes.
3. **Missing Keyboard Focus Audit**: No capability to track Tab/Shift+Tab traversal or detect keyboard traps.
4. **Missing Evidence & Remediation**: No structured fusion of UI Automation + OCR + Computer Vision into developer-actionable recommendations.
5. **Missing Verification Script**: `scripts/verify_snapdragon_npu.py` was not yet created.
6. **Missing Synthetic Flawed Demo App**: No interactive Windows test application with intentional accessibility defects to demonstrate auditing in real time.
7. **Missing Export Formats**: No generation of formal accessibility audit reports in Markdown, JSON, and HTML.

---

## 8. Reusable Components

The following modules from VisionVoice will be **preserved and reused directly** in AccessLens AI:
- `vision/ocr_engine.py`: High-accuracy local text detection & recognition via ONNX Runtime.
- `vision/image_utils.py`: Format conversion, aspect ratio scaling, bounding box rendering.
- `vision/screen_capture.py`: Clean multi-monitor Windows screen capture.
- `audio/text_to_speech.py`: Asynchronous, cancellable Windows SAPI narration.
- `hardware/hardware_detector.py`: Real system inspection and Snapdragon detection.
- `hardware/backend_status.py`: Enums (`BackendState`) and hardware profiles.
- `hardware/compute_backend.py`: Provider hierarchy and honest state management.
- `ai/cpu_backend.py` & `ai/qualcomm_backend.py`: ONNX Runtime execution provider abstractions.
- `ai/model_registry.py`: Documented catalog of local models and licenses.
- `privacy/privacy_manager.py`: Ephemeral file lifecycle and zero-cloud attestation.
- `storage/database.py`: SQLite persistence for audit history.
- `demo/samples/*`: Existing synthetic image assets.
- `app/ui/components.py`: High-contrast dark styling, cards, status badges, preview canvas.

---

## 9. New Components Required for AccessLens AI

1. **`accessibility/ui_automation.py`**: Windows UI Automation client querying active windows and child control trees.
2. **`accessibility/element_model.py`**: Structured `UIElementModel` and `InterfaceSnapshot` capturing combined visual and programmatic state.
3. **`accessibility/rule_engine.py`**: Deterministic rule checker evaluating:
   - Missing accessible names (`ACC_NAME_MISSING`)
   - Visible vs accessible label mismatch (`ACC_NAME_MISMATCH`)
   - Insufficient contrast ratio (`CONTRAST_LOW`)
   - Non-focusable interactive controls (`KEYBOARD_UNFOCUSABLE`)
   - Small touch/click target area (`TARGET_SIZE_SMALL`)
4. **`accessibility/contrast_engine.py`**: WCAG 2.1 relative luminance and contrast ratio calculations.
5. **`accessibility/keyboard_audit.py`**: Focus tracker recording tab traversal sequences and focus loops.
6. **`accessibility/evidence_engine.py`**: Multi-signal classifier tagging findings as `MEASURED`, `DETECTED`, `INFERRED`, or `RECOMMENDED`.
7. **`accessibility/remediation_engine.py`**: Actionable code snippets (WPF, WinUI 3, WinForms, Web/HTML) for developers.
8. **`accessibility/report_generator.py`**: Audit report generator (Markdown, JSON, HTML).
9. **`demo/accesslens_demo_app.py`**: Standalone PySide6 synthetic demonstration app containing intentional accessibility barriers.
10. **`scripts/verify_snapdragon_npu.py`**: Dedicated utility verifying Snapdragon NPU hardware and QNN execution provider presence.
11. **Comprehensive Documentation Suite (`docs/`)**:
    - `docs/ARCHITECTURE.md`
    - `docs/COMPETITION_COMPLIANCE.md`
    - `docs/SNAPDRAGON_VALIDATION.md`
    - `docs/ORIGINALITY_AND_REFERENCES.md`
    - `docs/PRESENTATION_SCRIPT.md`
    - `docs/SEVERITY_MODEL.md`
    - `docs/THREAT_MODEL.md`

---

## 10. Migration Risks & Mitigation Strategy

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Breaking Existing VisionVoice Features** | High | Preserve all existing files and tests; add new capabilities additively alongside existing modules. |
| **Windows UI Automation Freezes** | Medium | Execute UIA queries inside non-blocking worker threads (`QThread`) with a 5-second timeout. |
| **Missing Native UIA Dependencies** | Medium | Use native Windows `UIAutomationCore` / COM via `ctypes` with graceful fallback to OCR + Computer Vision if UIA is unavailable. |
| **Contrast False Positives on Gradients** | Low | Explicitly label visual contrast values as *Estimated Visual Measurement* and provide confidence scores. |
| **Sensitive Data Exposure in Exports** | High | Implement regex masking for API keys, passwords, emails, and phone numbers in `privacy/privacy_manager.py` before report export. |

---

## 11. Proposed Phased Implementation Plan

- **Phase 1:** Safe migration, project branding, and `verify_snapdragon_npu.py`.
- **Phase 2:** Windows UI Automation integration (`accessibility/ui_automation.py`).
- **Phase 3:** Unified `InterfaceSnapshot` and Element Inspector UI.
- **Phase 4:** Deterministic Accessibility Rule Engine (`accessibility/rule_engine.py`).
- **Phase 5:** WCAG Contrast Calculation Engine (`accessibility/contrast_engine.py`).
- **Phase 6:** Keyboard & Focus Traversal Audit (`accessibility/keyboard_audit.py`).
- **Phase 7:** Evidence Engine & Signal Classification (`MEASURED`, `DETECTED`, `INFERRED`, `RECOMMENDED`).
- **Phase 8:** Developer Remediation Guidance & Local AI Reasoning layer.
- **Phase 9:** Audit Report Generator (Markdown, JSON, HTML).
- **Phase 10:** Sensitive Data Protection & Redaction Reviewer.
- **Phase 11:** Synthetic Demonstration Application (`demo/accesslens_demo_app.py`).
- **Phase 12:** Enhanced Benchmark System (UIA + OCR + Rules + AI latency).
- **Phase 13:** UI/UX Upgrade (Upgraded Navigation: Dashboard, Audit, Inspector, Keyboard, Findings, Reports, Hardware, Benchmark, History, Privacy, Models, Settings).
- **Phase 14:** Test Suite Expansion (Preserve 26 tests + add 20+ new accessibility tests).
- **Phase 15:** Comprehensive Documentation Suite (`docs/`).
- **Phase 16:** Final 60-90 Second Competition Demo Script & Verification.

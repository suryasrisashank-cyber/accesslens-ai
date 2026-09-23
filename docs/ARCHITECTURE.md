# AccessLens AI — System Architecture & Technical Specification

**Tagline:** *"See the interface. Understand the barriers. Fix them locally."*  
**Challenge Target:** Qualcomm Snapdragon AI Lab Build & Present Challenge 2026  
**Host Platform:** Windows 10 (AMD64 / x64 Host)  
**Verification Baseline:** 211 / 211 automated tests passing | `FINAL STATUS: READY`

> [!IMPORTANT]
> **Statement of Hardware Integrity**:  
> *"AccessLens AI was developed and validated on an AMD64 Windows development system. The current development host does not contain Snapdragon hardware, so Snapdragon NPU execution and performance claims are intentionally not fabricated. The architecture includes a Qualcomm/QNN-ready hardware abstraction layer designed for genuine Snapdragon validation when compatible hardware/runtime is available."*

> [!IMPORTANT]
> **Human Review Requirement**:  
> *"Automated accessibility findings are intended to assist accessibility QA and require human review. AccessLens AI is an Accessibility QA Assistant, not a certification authority."*

---

## 1. Complete End-to-End System Architecture

```
+-------------------------------------------------------------------------------+
|                         TARGET WINDOW / APPLICATION                           |
+-------------------------------------------------------------------------------+
         |                                                       |
         v                                                       v
+-----------------------------+                 +-------------------------------+
|    WINDOWS UI AUTOMATION    |                 |   SCREEN CAPTURE / BUFFER     |
|   - UIA Tree Hierarchy      |                 |   - Multi-Monitor DPI-Aware   |
|   - Control Patterns        |                 |   - Safe Window Bounds        |
|   - Native Accessibility    |                 +-------------------------------+
+-----------------------------+                                  |
         |                                                       v
         |                                      +-------------------------------+
         |                                      |      ON-DEVICE OCR (ORT)      |
         |                                      |   - DBNet Text Detection      |
         |                                      |   - SVTR Character Recog      |
         |                                      |   - Direction Classifier      |
         |                                      +-------------------------------+
         |                                                       |
         +--------------------------+----------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------------+
|                        MULTIMODAL EVIDENCE FUSION                             |
|   - Deterministic Bipartite Spatial Matching (IoU + Spatial Proximity)        |
|   - Deterministic Match Score: 0.4*Geom + 0.3*Text + 0.15*Type + 0.15*Prox    |
|   - Bounded Focus Adjustment & Cross-Layer Conflict Detection                 |
|   - Coordinate System Translation (UIA Screen -> Screenshot Normalized)       |
|   - Prompt Injection Shield (Adversarial Text Isolation & Marking)            |
+-------------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------------+
|                      DETERMINISTIC ACCESSIBILITY RULES                        |
|   - 13 WCAG 2.1 / Section 508 / EN 301 549 Inspection Rules                   |
|   - Name Presence, Label in Name, Target Size, Pixel Contrast (WCAG 1.4.3)    |
|   - Keyboard Traversal, Focus Traps, Focus Loops, Unreached Elements          |
+-------------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------------+
|                     LOCAL REASONING & REMEDIATION ENGINE                      |
|   - Multi-Signal Evidence Aggregation ([MEASURED], [DETECTED], etc.)          |
|   - Actionable Developer Code Fixes (XAML, WinUI, WinForms, Web)              |
|   - Human Verification Checklists (QA Assistant - Not Certification Body)     |
+-------------------------------------------------------------------------------+
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v                                                     v
+----------------------------------+        +-----------------------------------+
|      PySide6 DESKTOP GUI         |        |   AUDIT REPORTS & EXPORT ENGINE   |
|   - 10 Specialized Tabs          |        |   - JSON Machine-Readable Export  |
|   - Real-Time Highlight Canvas   |        |   - Markdown QA Audit Summary     |
|   - SAPI Speech Audio Narration  |        |   - Accessible Standalone HTML    |
|   - Worker Thread Cancellation   |        |   - SHA-256 Digest Integrity      |
+----------------------------------+        +-----------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------------+
|                HARDWARE ABSTRACTION & RUNTIME SELECTOR LAYER                  |
|   - Hardware Detector (Genuine Physical Telemetry via WinReg & CIM)           |
|   - Capability Matrix (Multi-State: NOT_DETECTED -> VERIFIED_RUNTIME)         |
|   - Runtime Selector (CPUExecutionProvider Fallback with Zero Fabrication)    |
|   - QNN Hardware Abstraction (Ready for Qualcomm Hexagon NPU / Snapdragon X)  |
+-------------------------------------------------------------------------------+
```

---

## 2. Component Directory Architecture

| Directory / Package | Purpose & Primary Responsibilities |
| :--- | :--- |
| `accessibility/` | Core accessibility engine: `ui_automation.py`, `ui_tree.py`, `element_model.py`, `rule_engine.py` (Rules 1–13), `focus_models.py`, `focus_path.py`, `keyboard_driver.py`, `keyboard_auditor.py`, `contrast_engine.py`, `coordinate_mapping.py`, `visual_models.py`, `geometry.py`, `evidence_fusion.py`, `findings.py`, `severity.py`, `evidence_engine.py`, `remediation_engine.py`, `report_generator.py`, `audit_coordinator.py`. |
| `hardware/` | Host inspection & capability matrix: `hardware_detector.py`, `capability_matrix.py`, `compute_backend.py`, and `backend_status.py` enforcing zero hardware fabrication. |
| `ai/` | Compute engine abstraction: `runtime_selector.py`, `base_backend.py`, `cpu_backend.py`, `qualcomm_backend.py` (`QNNExecutionProvider` spec), `model_registry.py`, `reasoning_models.py`, `finding_context.py`, `prompt_guard.py`, `remediation_knowledge.py`, and `local_model_provider.py`. |
| `vision/` | Visual perception: `ocr_engine.py` (ONNX Runtime RapidOCR), `image_analyzer.py` (Layout & scene understanding), `screen_capture.py` (Win32 DPI-aware & minimized window safety), and `image_utils.py`. |
| `reports/` | Multimodal reports engine: `report_models.py`, `report_generator.py`, `report_validator.py`, `report_integrity.py` (SHA-256 digest), `sensitive_data_detector.py`, and multi-format exporters (`json_exporter.py`, `markdown_exporter.py`, `html_exporter.py`). |
| `app/` | Desktop presentation: `main.py` entrypoint, `app/ui/` views (Dashboard, Accessibility Audit, Inspector, Keyboard, Findings, Reports, Hardware, Benchmark, History, Models), and `app/workers/` asynchronous `QThread` workers with cooperative cancellation. |
| `audio/` | Speech narration: `text_to_speech.py` using Windows native `System.Speech.Synthesis.SpeechSynthesizer` with rate/volume and cancellation controls. |
| `privacy/` | Data security: `privacy_manager.py` guaranteeing zero-cloud local isolation and ephemeral temp file purging. |
| `storage/` | Persistence: `database.py` SQLite metadata store with context manager timeout protection. |
| `demo/` | Synthetic assets: `samples/` pre-rendered UI graphics and `accesslens_demo_app.py` interactive flawed testing target with explicit defect banners. |
| `scripts/` | Tooling: `validate_project.py`, `benchmark.py`, `verify_snapdragon_npu.py`, `run_demo.py`, and `generate_demo_samples.py`. |
| `tests/` | Comprehensive test suite: 211 automated unit and integration tests passing with 0 failures across 17 test modules. |

---

## 3. Snapdragon Hardware Abstraction Hierarchy

```
                     ACCESSLENS AI RUNTIME SELECTOR
                                  |
          +-----------------------+-----------------------+
          |                                               |
          v                                               v
[Non-Snapdragon Hardware]                     [Snapdragon X Series PC]
   Host: AMD Ryzen / Intel                      Host: Snapdragon X Elite / Plus
   Capability: NOT_DETECTED                     Capability: AVAILABLE / VERIFIED
   Backend: CPUExecutionProvider                Backend Hierarchy:
   Status: CPU Fallback Verified                1. QNNExecutionProvider (Hexagon NPU)
   Honesty: Zero Fabrication                    2. CPUExecutionProvider (Qualcomm Oryon)
```

1. **Multi-State Capability Detection**: `CapabilityMatrix` defines five explicit lifecycle states:
   - `NOT_DETECTED`: Non-Snapdragon host (e.g., AMD64 development system).
   - `DETECTED_NOT_AVAILABLE`: Snapdragon detected, but QNN runtime missing.
   - `AVAILABLE_NOT_INITIALIZED`: Snapdragon and QNN provider present, awaiting initialization.
   - `AVAILABLE`: QNN execution provider initialized and ready for inference.
   - `VERIFIED_RUNTIME`: On-device execution verified with physical telemetry evidence.
2. **Honest CPU Fallback**: If physical Snapdragon silicon or `QNNExecutionProvider` is missing, `RuntimeSelector` falls back to `CPUExecutionProvider` and logs explicit rationale:
   ```json
   {
       "requested_backend": "qualcomm_qnn",
       "selected_backend": "cpu",
       "fallback_reason": "Non-Snapdragon host detected (AMD/Intel development machine)",
       "hardware_verified": false
   }
   ```
3. **Zero Fabrication**: At no point are NPU benchmarks or simulated Hexagon TOPS fabricated.

---

## 4. Competition Evaluation Alignment

| Judging Category | Implementation & Architectural Evidence |
| :--- | :--- |
| **Technical Implementation** | 211 automated tests passed in the verified run; single-pass sequential multimodal pipeline fusing Windows UIA, ONNX Runtime OCR, deterministic WCAG 2.1 rules, and local reasoning. Zero network/cloud calls. Connection and worker cleanup paths are covered by automated tests. |
| **Application Use Case & Innovation** | Connects visual observations, Windows accessibility metadata, keyboard behavior, evidence provenance, and developer remediation into one integrated local QA workflow. Bipartite evidence fusion anchors findings to structural UIA truth and visual OCR observations. |
| **Deployment & Accessibility** | Designed to operate locally without mandatory cloud services. Built-in Windows SAPI speech narration, accessible UI styling with contrast design targets, standalone accessible HTML reports, and automated PII/credential masking. |
| **Presentation & Documentation** | 60–90 second reproducible demo script (`scripts/run_demo.py`), synthetic test target clearly labelled (`demo/accesslens_demo_app.py`), honest hardware attestation, and complete technical specifications. |

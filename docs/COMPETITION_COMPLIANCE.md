# AccessLens AI — Competition Compliance & Evaluation Mapping

**Competition:** Qualcomm Snapdragon AI Lab Build & Present Challenge 2026  
**Project:** AccessLens AI — On-Device Accessibility Inspection & Remediation Assistant  
**Attestation:** This document outlines how the actual implementation aligns with the challenge criteria. No official Qualcomm endorsement, score guarantees, or judge approvals are claimed.

---

## 1. Technical Implementation

| Challenge Area | Implementation in AccessLens AI | Source Files |
| :--- | :--- | :--- |
| **On-Device Multimodal Pipeline** | Combines Windows UI Automation (UIA) tree extraction, on-device optical character recognition (ONNX Runtime / RapidOCR), and layout analysis into a unified `InterfaceSnapshot`. | `accessibility/audit_coordinator.py`<br>`vision/ocr_engine.py` |
| **Deterministic Rule Engine** | 100% offline rule engine executing WCAG 2.1 AA checks (missing accessible names, label-in-name mismatches, contrast ratios, target sizing, and focusability). | `accessibility/rule_engine.py`<br>`accessibility/contrast_engine.py` |
| **Snapdragon / QNN Architecture** | Clean hardware abstraction layer designed for ONNX Runtime + `QNNExecutionProvider` targeting the Qualcomm Hexagon NPU with graceful CPU fallback. | `ai/qualcomm_backend.py`<br>`hardware/compute_backend.py` |
| **Zero Hardware Fabrication** | Accurately detects and reports host processor (AMD Ryzen 3 2200U x64) as CPU Fallback; never fakes NPU execution or benchmark metrics. | `hardware/hardware_detector.py`<br>`scripts/verify_snapdragon_npu.py` |
| **Code Quality & Testing** | Comprehensive automated test suite comprising 107 unit and integration tests passing with 0 failures. | `tests/`<br>`scripts/validate_project.py` |

---

## 2. Application Use Case & Innovation

- **Beyond Descriptive Chatbots**: AccessLens AI solves a concrete software engineering challenge: assisting developers, QA engineers, and enterprise teams in identifying, understanding, and fixing Windows accessibility barriers.
- **Evidence-First Grounding**: Every reported finding distinguishes observed truth:
  - `[MEASURED]`: Mathematically verified (contrast ratio 3.1:1, target dimensions 14x14 px).
  - `[DETECTED]`: Directly extracted from Windows UIA API or OCR text streams.
  - `[INFERRED]`: Visual layout observations and interactive affordance cues.
  - `[RECOMMENDED]`: Concrete remediation code and human verification protocols.
- **Actionable Developer Remediation**: Provides copy-paste code snippets for XAML/WPF, WinUI 3, WinForms, and Web/HTML.

---

## 3. Deployment & Accessibility

- **Native Windows Desktop UI**: Built with PySide6, designed with accessible high-contrast dark theme, large readable fonts, keyboard shortcuts (`Ctrl+O`, `Ctrl+S`, `Space`, `Esc`), and zero unnecessary animations.
- **Local Text-to-Speech Narration**: Integrates local Windows `System.Speech` SAPI to read audit summaries, focus warnings, and finding remediation aloud.
- **Zero Cloud Costs / Zero Cloud Latency**: 100% on-device operation. Requires zero external API tokens, zero paid cloud LLM subscriptions, and zero external database servers.
- **Privacy by Design**: Ephemeral screenshot memory buffers; SQLite history persists only barrier counts and metadata. Automated sensitive data masking redacts credentials, emails, and phone numbers before export.

---

## 4. Presentation & Documentation

- **Reproducible Demonstration**: Includes both pre-rendered realistic sample interfaces and an interactive flawed test app (`demo/accesslens_demo_app.py`) for live competition walkthroughs.
- **Automated Validation**: `scripts/validate_project.py` outputs a clear pass/fail checklist across all 9 subsystems.
- **Honest Limitations**: Transparently documents current development on non-Qualcomm hardware and explicit verification procedures required when migrating to Snapdragon X Series PCs.

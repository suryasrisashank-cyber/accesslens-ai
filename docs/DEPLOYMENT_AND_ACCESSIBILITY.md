# AccessLens AI — Deployment & Accessibility Architecture
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**Project:** AccessLens AI  
**Tagline:** *"See the interface. Understand the barriers. Fix them locally."*  
**Deployment Target:** Windows Desktop (Windows 10 / Windows 11)

---

## 1. Windows Desktop Deployment Model

AccessLens AI is packaged as a standard Windows desktop application built with Python and PySide6 (Qt for Python). It interacts directly with Windows native subsystems:
- **UI Automation:** Uses native Windows COM UI Automation APIs to inspect running desktop windows.
- **Screen Capture:** Utilizes native Win32 `GetWindowRect` and `PrintWindow` / `BitBlt` APIs with per-monitor DPI awareness.
- **Audio Output:** Uses Windows SAPI (`System.Speech.Synthesis.SpeechSynthesizer`) for on-device voice narration without external dependencies.
- **Local Persistence:** Uses standard SQLite with connection timeout management for local audit history.

---

## 2. Local-First Processing & Zero Cloud Mandate

AccessLens AI is designed to operate locally without mandatory cloud services:
- **No Cloud Multimodal APIs:** All OCR and layout analysis execute on the local machine via ONNX Runtime.
- **No Remote Telemetry:** No user data, window titles, or on-screen images are transmitted across the network.
- **Ephemeral Buffers:** Screenshot crop buffers created during analysis are stored in ephemeral memory and discarded when audits conclude.

---

## 3. Compute Backends: CPU Fallback & Optional Snapdragon Path

The compute architecture supports dual operational paths via [`ai/runtime_selector.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/ai/runtime_selector.py):

| Execution Mode | Current Development Host | Snapdragon X Series Target |
| :--- | :--- | :--- |
| **Active Provider** | `CPUExecutionProvider` | `QNNExecutionProvider` (Hexagon NPU) |
| **Silicon** | AMD Ryzen 3 2200U (x64) | Qualcomm Snapdragon X Elite / X Plus (ARM64) |
| **Fallback Path** | Native local CPU execution | Automatic fallback to Qualcomm Oryon CPU if NPU is uninitialized |
| **Verification State** | Verified on current AMD CPU host | Pending genuine Snapdragon hardware validation |

---

## 4. Application Accessibility Features

AccessLens AI practices what it preaches by integrating accessibility features into its own desktop interface:

1. **Accessibility-Oriented UI with Contrast Targets:** Dark surface backgrounds (`#0F172A`, `#1E293B`) paired with high-contrast text (`#F8FAFC`, `#94A3B8`) targeting the WCAG 4.5:1 contrast design target for normal text where applicable.
2. **Keyboard-Accessible Controls:** All buttons, combo boxes, and table rows are keyboard focusable with visible focus rectangles. Standard shortcuts (`Ctrl+S` for capture, `Ctrl+O` for file open) are supported.
3. **Screen Reader & Speech Narration:** Native text-to-speech narration speaks finding summaries, critical defect counts, and audit completion states aloud asynchronously using Windows SAPI.
4. **Accessible HTML Report Output:** Exported HTML reports use clean semantic markup (`<h1>`–`<h3>`, `<table>`, `<dl>`), readable contrast styling, and responsive viewport sizing.

---

## 5. Privacy Modes & Sensitive Data Protection

The reporting subsystem incorporates automated sensitive data protection:
- **Finding-Only Mode:** Exports only structural metadata and remediation code without visual screenshot images.
- **Credential & PII Redaction:** [`reports/sensitive_data_detector.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/reports/sensitive_data_detector.py) scans on-screen text for API keys, passwords, email addresses, phone numbers, and local file paths, redacting them as `[REDACTED_CREDENTIAL]`, `[REDACTED_EMAIL]`, or `[REDACTED_PHONE]`.
- **Integrity Attestation:** Computes canonical SHA-256 digests over redacted evidence to ensure reports are tamper-evident.

---

## 6. Offline Demonstration Workflow

The competition demonstration workflow ([`scripts/run_demo.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/scripts/run_demo.py)) operates fully offline using pre-rendered sample graphics in `demo/samples/` and the synthetic test target application (`demo/accesslens_demo_app.py`). It requires no internet connectivity, ensuring consistent and reproducible evaluations for challenge judges.

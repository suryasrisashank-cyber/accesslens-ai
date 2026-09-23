# AccessLens AI — One-Page Project Brief
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**Project:** AccessLens AI  
**Tagline:** *"See the interface. Understand the barriers. Fix them locally."*  
**Category:** On-Device AI / Developer Tools / Accessibility QA  
**Platform:** Windows 10 & 11 Desktop (AMD64 / ARM64 QNN Ready)

---

### 1. Executive Summary
AccessLens AI is a local-first Windows accessibility QA assistant.

It combines:
- Windows UI Automation
- OCR
- Visual evidence
- Deterministic accessibility rules
- Keyboard/focus analysis
- Evidence fusion
- Local reasoning
- Developer remediation

Rather than treating accessibility auditing as an ungrounded visual guessing game or a static tree view, AccessLens fuses pixel evidence with programmatic UI trees to detect WCAG 2.1 AA barriers, generate actionable developer remediation code, and export self-contained, tamper-evident audit reports—all completely on-device without cloud telemetry.

---

### 2. The Problem
- **Developer Friction:** Identifying accessibility defects in running Windows desktop applications (WPF, WinUI 3, WinForms) requires navigating cumbersome, unintegrated developer tools like `Inspect.exe` and manually calculating contrast ratios.
- **Privacy & Security Risks:** Sending application screenshots containing proprietary IP, customer records, or credentials to third-party cloud multimodal APIs violates enterprise data compliance.
- **Disconnected Analysis:** Static linters miss dynamic runtime rendering issues; vision-only models hallucinate non-existent controls and cannot provide programmatic automation IDs or XAML fixes.

---

### 3. Key Innovations & Differentiators
- **Multimodal Evidence Fusion:** Evaluates IoU geometry, textual overlap, and control types to link visual OCR boxes with UIA nodes using a bounded Deterministic Match Score ($[0.0, 1.0]$).
- **Active Keyboard Traversal Auditing:** Synthesizes `Tab` and `Shift+Tab` keystrokes to map application focus flow as a directed graph, detecting focus traps, 2-node bounce loops, and unreachable controls.
- **Actionable Developer Remediation:** Produces framework-specific code snippets (XAML, WinUI, C#, ARIA) paired with an explicit human-in-the-loop verification checklist.
- **Privacy & Defense-in-Depth:** Zero network calls; passive prompt-injection isolation prevents malicious on-screen text from altering audit rules; automatic credential and PII redaction.
- **Cryptographic Report Integrity:** Exports structured JSON, Markdown, and standalone offline HTML reports signed with canonical SHA-256 evidence digests.

---

### 4. Current Verified Environment & Hardware Status
- **Current Verified Environment:**
  - Host CPU: AMD Ryzen 3 2200U
  - Architecture: AMD64
  - Active Backend: CPUExecutionProvider
- **Testing:**
  - 211/211 automated tests passed (0 failures).
- **Snapdragon:**
  - Not detected on current development host.
- **Qualcomm/QNN:**
  - Ready for genuine future validation. (Architecture implemented in `ai/qualcomm_backend.py` targeting `QNNExecutionProvider` with HTP burst mode).

---

### 5. Verified AMD CPU Benchmark
- Average OCR: 4760.83 ms
- Average Scene/Layout: 15.19 ms
- Average Audit/Rules/Evidence Fusion: 29.10 ms
- Average Report Generation: 180.08 ms
- Average Total Sequential Pipeline: 4985.20 ms
- Process Memory: 115.42 MB

*These measurements were obtained on the AMD Ryzen 3 2200U development system. They are a local CPU baseline and are not Snapdragon measurements.*

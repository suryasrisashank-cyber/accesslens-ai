# AccessLens AI — Unstop Innovation & Application Use Case
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**Project:** AccessLens AI  
**Tagline:** *"See the interface. Understand the barriers. Fix them locally."*  
**Positioning:** On-Device Accessibility QA Assistant for Windows Applications

---

## 1. Core Innovation

AccessLens AI addresses a fundamental fragmentation in existing accessibility QA tooling. Rather than functioning solely as an OCR text extractor, a static tree viewer, or an ungrounded visual chatbot, AccessLens connects:

1. **Visual Observations:** On-device OCR text boundaries and rendered pixel color sampling.
2. **Windows Accessibility Metadata:** Native UI Automation control patterns, accessible names, control types, bounding rectangles, and automation IDs.
3. **Keyboard Behavior:** Live focus traversal, sequential tab transitions, tab loop detection, and keyboard trap discovery.
4. **Evidence Provenance:** Multi-signal classification separating observations into `[MEASURED]`, `[DETECTED]`, `[INFERRED]`, and `[RECOMMENDED]` items.
5. **Developer Remediation:** Contextual, copy-paste code snippets for XAML, WinUI, WinForms, and Web interfaces, paired with manual verification guidance.

By fusing these layers into a single on-device pipeline, AccessLens grounds every reported barrier in reproducible structural and visual evidence.

---

## 2. Real-World Application Use Cases

### A. Windows Desktop Application Developers
Developers building WPF, WinUI 3, or WinForms applications can audit running application windows during active development. Instead of manually inspecting properties in `Inspect.exe` and cross-referencing WCAG criteria, AccessLens flags missing accessible names, undersized click targets, and contrast discrepancies, providing direct XAML code fixes.

### B. Accessibility QA & Conformance Engineers
Accessibility testers can perform rapid preliminary audits of Windows interfaces. The tool generates structured JSON for CI/CD integration, Markdown summaries for issue trackers, and self-contained accessible HTML reports for stakeholder sign-off.

### C. Keyboard Accessibility Auditing
Keyboard-only users face critical barriers when applications trap focus or omit interactive elements from the tab sequence. AccessLens reconstructs the complete focus path as a directed graph, detecting focus bounce loops, keyboard traps, and unreachable controls without requiring third-party automation tools.

### D. Regulated Enterprise Software Teams
Organizations with strict confidentiality requirements (finance, healthcare, defense) cannot transmit proprietary screens to cloud multimodal APIs. AccessLens operates locally on-device without mandatory network connections, ensuring that sensitive on-screen data remains private.

---

## 3. Product Positioning & Differentiators

| Traditional Approach | AccessLens AI Fused Approach |
| :--- | :--- |
| **Manual Inspection (`Inspect.exe`)** Requires manual traversal of each node; does not evaluate visual contrast or label mismatches. | Automatically traverses the UIA tree, correlates with visual OCR, and evaluates 13 deterministic rules simultaneously. |
| **Cloud Multimodal Vision Models** Introduces privacy leakage, unpredictable response latency, and hallucinations disconnected from the UIA tree. | 100% on-device local execution; anchors all findings to structural UIA metadata and deterministic rules. |
| **Web-Only Linters (e.g., axe-core)** Ineffective for native Windows desktop applications (WPF, WinUI, WinForms). | Native Windows UI Automation support covering desktop windows and web views alike. |

---

## 4. Human-in-the-Loop Philosophy

AccessLens AI is engineered as an **Accessibility QA Assistant**, not a compliance certification authority. Automated findings highlight areas requiring human review and provide testing checklists (e.g., testing with Windows High Contrast Mode or screen readers), empowering developers and QA engineers to make informed, verified accessibility improvements.

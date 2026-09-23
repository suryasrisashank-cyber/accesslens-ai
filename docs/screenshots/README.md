# AccessLens AI — Screenshot & Video Asset Directory

This directory stores verified visual assets, screenshots, and demonstration recordings for the AccessLens AI competition submission (Qualcomm Snapdragon AI Lab Build & Present Challenge 2026).

---

## 1. Asset Naming Convention & Index

| Filename | View / Workflow | Purpose / Key Elements |
|---|---|---|
| `01_main_dashboard.png` | Main Dashboard | Complete view of the main window, showing loaded demo target, audit controls, summary metrics, and honest AMD CPU status banner. |
| `02_hardware_attestation.png` | Hardware Attestation | Host machine specifications card (AMD Ryzen 3 2200U, AMD64), Snapdragon NOT DETECTED status, and honest CPU fallback badge. |
| `03_accessibility_findings.png` | Accessibility Findings | Finding list with severity badges (Critical, High, Medium, Low), WCAG references, confidence percentage, and finding title summary. |
| `04_evidence_visualization.png` | Evidence Visualization | Split-view layout: cropped UI element screenshot with bounding overlay alongside grounded evidence items (`[MEASURED]`, `[DETECTED]`, `[INFERRED]`). |
| `05_ui_automation_inspector.png` | UI Automation Inspector | Element inspector tree view displaying control hierarchy, automation IDs, control types, bounding rectangles, and keyboard focusable attributes. |
| `06_keyboard_focus_audit.png` | Keyboard/Focus Audit | Visual focus chain visualization, traversal order sequence, detected loops, unreached elements, and focus graph. |
| `07_remediation_guidance.png` | Remediation Guidance | Actionable code snippet editor with syntax styling (XAML / WinUI / Web), accessibility impact explanation, and explicit human verification checklist. |
| `08_report_export_interface.png` | Report/Export Interface | Markdown and JSON report preview tabs, SHA-256 evidence integrity digest banner, sensitive data redaction summary, and export action buttons. |
| `09_offline_html_report.png` | Offline HTML Report | Self-contained browser-rendered HTML report displaying executive summary cards, WCAG finding tables, evidence accordions, and 4.5:1 contrast styling. |
| `10_synthetic_demo_application.png` | Synthetic Demo Application | The standalone `demo/accesslens_demo_app.py` window exhibiting deliberate accessibility barriers and `⚠️ [DEMO / SYNTHETIC TARGET]` header banner. |

---

## 2. Capture Guidelines

1. **Resolution:** Capture at 1080p (1920x1080) or higher, 100% DPI scaling recommended.
2. **Window Framing:** Capture application windows cleanly without desktop clutter or unrelated background apps.
3. **Integrity:** Do not digitally alter status indicators or hardware banners. All screenshots must reflect actual execution on the host machine.
4. **Format:** PNG format with lossless compression.
5. **No Fake Screenshots:** Screenshots must be captured from the actual running application. DO NOT generate fake screenshots. DO NOT use mock UI images as evidence of implemented functionality.

---

> [!IMPORTANT]
> **MANUAL ACTION REQUIRED:**  
> Capture screenshots from the actual running application.

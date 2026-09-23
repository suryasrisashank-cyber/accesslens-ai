# AccessLens AI — Competition Screenshot Plan
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

This document defines the 10 required competition screenshots, detailing suggested filenames, visible interface components, demonstrated features, excluded elements, and sensitive data protections.

All screenshots must be captured from the actual running application. Do not generate fake or simulated UI screenshots.

---

### Screenshot 1: Main Dashboard (`01_main_dashboard.png`)
- **Visible Elements:** Main window navigation header, tab bar, `CPU PROCESSING` and `LOCAL ONLY` badges, action bar (Capture, Open, Demo App, Sample Selector), and initial welcome overview.
- **Feature Demonstrated:** Clean, accessibility-oriented UI layout with high contrast design targets and central command navigation.
- **Must NOT Be Visible:** Active audit overlays or error dialogs.
- **Sensitive Data Protections:** No developer desktop icons or private system background.

---

### Screenshot 2: Hardware Attestation (`02_hardware_attestation.png`)
- **Visible Elements:** Host machine specifications card (AMD Ryzen 3 2200U, AMD64, 7.64 GB RAM, Windows 10), Snapdragon & NPU Status card (`Snapdragon Hardware: Not detected`, `Qualcomm Hexagon NPU: Not available on current development host`, `Active AI Backend: CPU fallback`), and the honest hardware attestation banner.
- **Feature Demonstrated:** Un-fabricated hardware reporting, multi-state capability matrix status, and CPU fallback verification.
- **Must NOT Be Visible:** Fabricated Snapdragon execution claims, simulated NPU benchmarks, or "45 TOPS measured" text.
- **Sensitive Data Protections:** MAC addresses, serial numbers, and private local IP addresses are excluded.

---

### Screenshot 3: Accessibility Findings (`03_accessibility_findings.png`)
- **Visible Elements:** Filterable findings list, severity badges (`[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[LOW]`), WCAG reference tags (e.g., WCAG 4.1.2, 2.5.3, 1.4.3), confidence percentage, and finding title summary.
- **Feature Demonstrated:** Deterministic accessibility evaluation grounded in WCAG 2.1 AA specifications.
- **Must NOT Be Visible:** Subjective or ungrounded generative commentary; claims of guaranteed WCAG compliance.
- **Sensitive Data Protections:** User email addresses, phone numbers, or credentials from raw screen text must be masked.

---

### Screenshot 4: Evidence Visualization (`04_evidence_visualization.png`)
- **Visible Elements:** Split-view layout: cropped UI element screenshot with bounding overlay alongside grounded evidence items classified by provenance tags (`[MEASURED]`, `[DETECTED]`, `[INFERRED]`, `[RECOMMENDED]`), deterministic match score ($[0.0, 1.0]$), and conflict detection.
- **Feature Demonstrated:** Multimodal evidence fusion linking visual screen pixels with Windows UI Automation metadata.
- **Must NOT Be Visible:** Ungrounded AI hallucinations or unverified compliance claims.
- **Sensitive Data Protections:** Masked text for any input field containing personal identifiers.

---

### Screenshot 5: UI Automation Inspector (`05_ui_automation_inspector.png`)
- **Visible Elements:** Element inspector tree view displaying control hierarchy, automation IDs, control types (Button, Edit, Text, Pane), bounding rectangles, and keyboard focusable attributes.
- **Feature Demonstrated:** Native Windows UI Automation COM hierarchy inspection and property extraction.
- **Must NOT Be Visible:** Desktop background applications or uninspected windows.
- **Sensitive Data Protections:** No proprietary software names or credentials in element values.

---

### Screenshot 6: Keyboard/Focus Audit (`06_keyboard_focus_audit.png`)
- **Visible Elements:** Visual focus sequence canvas showing numbered focus path transitions, directed graph arrows, tab order index list, and detected barrier indicators (focus loops, unreachable elements).
- **Feature Demonstrated:** Active keyboard navigation auditing and sequential tab order verification.
- **Must NOT Be Visible:** Simulated key injection failures or desktop-wide mouse pointer interference.
- **Sensitive Data Protections:** Only application window controls are displayed.

---

### Screenshot 7: Remediation Guidance (`07_remediation_guidance.png`)
- **Visible Elements:** Actionable code snippet editor with syntax styling (XAML / WinUI / Web), accessibility impact explanation, and explicit human verification checklist with checkbox items.
- **Feature Demonstrated:** Developer-oriented remediation guidance and human-in-the-loop QA protocol.
- **Must NOT Be Visible:** Unqualified claims that code snippets automatically guarantee WCAG compliance.
- **Sensitive Data Protections:** No proprietary codebase paths or user tokens.

---

### Screenshot 8: Report/Export Interface (`08_report_export_interface.png`)
- **Visible Elements:** Markdown and JSON report preview tabs, SHA-256 evidence integrity digest banner, sensitive data redaction summary (`[REDACTED_EMAIL]`, `[REDACTED_CREDENTIAL]`), and export action buttons.
- **Feature Demonstrated:** Machine-readable and developer-readable report generation with integrated data protection.
- **Must NOT Be Visible:** Unmasked passwords, tokens, or personal identifiers.
- **Sensitive Data Protections:** Active redaction of all sensitive strings confirmed by visual verification.

---

### Screenshot 9: Offline HTML Report (`09_offline_html_report.png`)
- **Visible Elements:** Self-contained browser-rendered HTML report displaying executive summary cards, WCAG finding tables, evidence accordions, 4.5:1 contrast styling, and print/export stylesheet.
- **Feature Demonstrated:** Portable, standalone stakeholder report operating without external CSS/JS CDN dependencies.
- **Must NOT Be Visible:** Broken network icon, external tracking pixels, or missing stylesheets.
- **Sensitive Data Protections:** Redacted local disk paths; only relative file references.

---

### Screenshot 10: Synthetic Demo Application (`10_synthetic_demo_application.png`)
- **Visible Elements:** `demo/accesslens_demo_app.py` window showing explicit `⚠️ [DEMO / SYNTHETIC TARGET]` header banner, intentional defect labels (low contrast, missing accessible names, tiny target sizes), and live audit bounding boxes.
- **Feature Demonstrated:** Reproducible, safe offline test target for competition demonstrations and evaluator testing.
- **Must NOT Be Visible:** Appearance of real university, banking, or commercial application branding.
- **Sensitive Data Protections:** Pre-baked synthetic demo text only; zero real customer or user data.

---

> [!IMPORTANT]
> **MANUAL ACTION REQUIRED:**  
> Capture screenshots from the actual running application. Do not generate fake screenshots or mock images.

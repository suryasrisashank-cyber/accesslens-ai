# AccessLens AI — Originality Statement & Technical References

**Project:** AccessLens AI — On-Device Accessibility Inspection & Remediation Assistant  
**Challenge:** Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

---

## 1. Originality & Independent Implementation Statement

AccessLens AI is an original software application designed and implemented independently for the Qualcomm Snapdragon AI Lab Challenge 2026. The architecture, deterministic accessibility rules, evidence fusion engine, UI Automation correlation pipeline, PySide6 desktop views, and report generation systems were authored specifically for this project.

Existing third-party libraries and pretrained foundation models are utilized strictly in accordance with their respective open-source licenses and are fully acknowledged below.

---

## 2. Technical References & Official Documentation Consulted

### Qualcomm & Snapdragon Documentation
1. **Qualcomm AI Hub**: Model deployment, quantization pipelines, and ONNX Runtime execution provider documentation ([https://aihub.qualcomm.com](https://aihub.qualcomm.com)).
2. **Qualcomm Neural Processing SDK (QNN)**: Hexagon Tensor Processor (HTP) execution architecture, performance modes, and precision tuning guides.
3. **ONNX Runtime QNN Execution Provider**: Configuration reference for Microsoft ONNX Runtime with Qualcomm QNN Execution Provider.

### Microsoft Windows Accessibility & UI Automation
1. **Microsoft UI Automation Documentation**: Windows Accessibility APIs, UIAutomationCore COM interfaces, and control pattern specifications ([https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32](https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32)).
2. **AutomationProperties XAML Reference**: Attached properties for accessible names, descriptions, and tab indices in WPF, WinUI 3, and UWP.
3. **W3C Web Content Accessibility Guidelines (WCAG) 2.1**:
   - Guideline 1.4.3: Contrast (Minimum) — Level AA (4.5:1 / 3.0:1)
   - Guideline 2.1.1: Keyboard Focusability
   - Guideline 2.4.3: Focus Order
   - Guideline 2.5.3: Label in Name
   - Guideline 2.5.8: Target Size (Minimum) (24x24 px)
   - Guideline 4.1.2: Name, Role, Value

---

## 3. Third-Party Libraries & Open Source Licenses

| Component / Library | Version | License | Source / Purpose |
| :--- | :--- | :--- | :--- |
| **PySide6** | 6.11.2 | LGPL-3.0 / Commercial | Native cross-platform desktop UI framework |
| **ONNX Runtime** | 1.30.0 | MIT License | Cross-platform machine learning inference runtime |
| **RapidOCR** | 1.2.3 | Apache-2.0 | On-device text detection and recognition models |
| **Pillow (PIL)** | 12.3.0 | HPND License | Python Imaging Library for pixel and image processing |
| **NumPy** | 2.5.1 | BSD-3-Clause | Numerical array computations for contrast & image crops |
| **psutil** | 7.2.2 | BSD-3-Clause | System hardware inspection and memory telemetry |
| **pytest** | 9.1.1 | MIT License | Automated testing and verification framework |

---

## 4. What Was Independently Implemented

1. **Evidence-First Accessibility Architecture**: Multi-signal classification distinguishing `[MEASURED]`, `[DETECTED]`, `[INFERRED]`, and `[RECOMMENDED]` observations.
2. **Windows UIA & OCR Spatial Fusion**: Correlating bounding boxes from Windows UI Automation and OCR text detection to pinpoint discrepancies.
3. **Deterministic WCAG 2.1 AA Rule Engine**: Offline algorithms evaluating name presence, label concordance, contrast, touch target dimensions, and focusability.
4. **Interactive Element Inspector & Keyboard Auditor**: Real-time property inspection and tab sequence recording.
5. **Developer Remediation Engine**: Synthesizing copy-paste code snippets for XAML, WinUI 3, WinForms, and HTML.
6. **Multi-Format Report Generator**: Exporting to Markdown, JSON, and self-contained HTML with automated sensitive credential masking.
7. **Synthetic Demonstration Target App**: Standalone PySide6 application with known accessibility barriers for offline testing.
8. **Hardware Abstraction Layer**: Verifying host telemetry and enforcing zero fabrication of Snapdragon/NPU results.

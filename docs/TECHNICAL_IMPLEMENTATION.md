# AccessLens AI — Technical Implementation Document
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**Project:** AccessLens AI  
**Tagline:** *"See the interface. Understand the barriers. Fix them locally."*  
**Host Platform:** Windows 10 (AMD64 / x64 Host) | `CPUExecutionProvider` (Local CPU Fallback)  
**Verification Baseline:** 211 / 211 automated tests passed in the verified run.

---

## 1. System Architecture

AccessLens AI executes a single-pass sequential pipeline linking structural accessibility metadata, visual perception, deterministic rule evaluation, and developer remediation:

```
Windows Target Application
          |
          v
Window Selection
          |
    +-----+-----+
    |     |     |
    v     v     v
   UIA Screenshot OCR
    |     |     |
    +-----+-----+
          |
          v
Evidence Collection
          |
    +-----+------+------+
    |            |      |
    v            v      v
Accessibility Keyboard Visual
Rules           Audit   Evidence
    |            |      |
    +------------+------+
                 |
                 v
          Evidence Fusion
                 |
                 v
        Local Reasoning
                 |
                 v
        Remediation Guidance
                 |
                 v
        Human Verification
                 |
                 v
         Report Generation
          /      |      \
        JSON     MD      HTML
```

---

## 2. Windows UI Automation (UIA)

- **Module:** `accessibility/ui_automation.py`, `accessibility/ui_tree.py`, `accessibility/element_model.py`.
- **Implementation:** Interfaces with the native Windows UI Automation COM library via `comtypes` / `ctypes`.
- **Extracted Attributes:** Control type, automation ID, name, value, bounding rectangle, focusability (`IsKeyboardFocusable`), enabled state, and parent-child hierarchy.
- **Defensive Bounds:** Normalizes window-relative coordinates, handles negative multi-monitor origins, and filters empty bounding boxes.

---

## 3. Optical Character Recognition (OCR)

- **Module:** `vision/ocr_engine.py`.
- **Implementation:** RapidOCR powered by ONNX Runtime executing DBNet for text box detection and SVTR for character sequence decoding.
- **Output:** Bounding box polygons, extracted text strings, and model confidence scores.
- **Local Isolation:** Runs completely on-device without remote network calls.

---

## 4. Visual Evidence

- **Module:** `vision/screen_capture.py`, `vision/image_analyzer.py`, `accessibility/visual_models.py`.
- **Capture Safety:** Uses Win32 `user32.IsIconic(hwnd)` to detect minimized windows and `user32.IsWindow(hwnd)` to verify window validity, avoiding negative-coordinate cropping errors.
- **Pixel Sampling:** Performs regional pixel color extraction for foreground and background luminance calculation according to WCAG relative luminance specifications.

---

## 5. Deterministic Accessibility Rules

- **Module:** `accessibility/rule_engine.py`, `accessibility/contrast_engine.py`.
- **Coverage:** 13 deterministic evaluation rules mapped to WCAG 2.1 AA specifications:
  - Name presence (WCAG 4.1.2)
  - Potential label-in-name discrepancy (WCAG 2.5.3)
  - Semantic container validity (WCAG 1.3.1)
  - Keyboard focusability (WCAG 2.1.1)
  - Control role consistency (WCAG 4.1.2)
  - Touch/click target size minimum ($24 \times 24$ px) (WCAG 2.5.8)
  - Form input label association (WCAG 3.3.2)
  - Color contrast ratio (4.5:1 normal text design target) (WCAG 1.4.3)
  - Keyboard focus trap detection (WCAG 2.1.2)
  - Unreached interactive element detection (WCAG 2.1.1)
  - Keyboard focus loop detection (WCAG 2.4.3)
  - Focus traversal order consistency (WCAG 2.4.3)
  - Visual focus indicator state (WCAG 2.4.7)

---

## 6. Keyboard Traversal

- **Module:** `accessibility/keyboard_driver.py`, `accessibility/keyboard_auditor.py`, `accessibility/focus_path.py`.
- **Implementation:** Safe synthetic `Tab` / `Shift+Tab` key sequencing via native Win32 `SendInput` (with mock fallback for headless test environments).
- **Graph Modeling:** Represents traversal as a directed graph of `FocusPathTransition` edges, automatically flagging cyclic 2-node loops, trapped containers, and unvisited focusable nodes.

---

## 7. Multimodal Evidence Fusion

- **Module:** `accessibility/evidence_fusion.py`, `accessibility/geometry.py`.
- **Bipartite Matching:** Computes IoU (Intersection over Union), containment ratios, token-overlap text similarity, control-type compatibility, and centroid Euclidean proximity.
- **Deterministic Match Score:**
  $$\text{Base Score} = 0.40 \times \text{Geom} + 0.30 \times \text{Text} + 0.15 \times \text{Type} + 0.15 \times \text{Prox}$$
  $$\text{Final Score} = \min(1.0, \text{Base Score} + 0.20) \quad \text{if reliable focus evidence is present, else Base Score}$$
- **Bounds Guarantee:** Strictly bounded in $[0.0, 1.0]$.
- **Conflict Resolution:** Flags discrepancies between visual text and programmatic accessible names explicitly as conflict items.

---

## 8. Local Reasoning

- **Module:** `ai/local_model_provider.py`, `ai/reasoning_models.py`, `ai/finding_context.py`.
- **Architecture:** Symbolic rule-based reasoning engine operating locally on CPU.
- **Grounding Principle:** The local reasoning assistant does not invent findings; it explains findings that have already been established by deterministic rules and evidence fusion.

---

## 9. Developer Remediation

- **Module:** `accessibility/remediation_engine.py`, `ai/remediation_knowledge.py`.
- **Multi-Framework Fixes:** Generates context-aware snippets for WPF XAML, WinUI 3, WinForms (C#), and Web (HTML/ARIA).
- **Honest Fallback:** If framework metadata is ambiguous, the engine outputs *"Framework-specific code cannot be generated reliably from the available evidence"* and provides framework-agnostic remediation.
- **Human Verification:** Enforces a mandatory verification protocol emphasizing that automated recommendations require human review.

---

## 10. Report Generation

- **Module:** `reports/report_models.py`, `reports/report_generator.py`, `reports/report_integrity.py`.
- **Normalization:** Formats findings, elements, and evidence into validated dataclasses.
- **Exporters:**
  - Machine-readable JSON ([`reports/exporters/json_exporter.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/reports/exporters/json_exporter.py))
  - GitHub-flavored Markdown ([`reports/exporters/markdown_exporter.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/reports/exporters/markdown_exporter.py))
  - Self-contained accessible HTML ([`reports/exporters/html_exporter.py`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/reports/exporters/html_exporter.py))
- **Integrity:** Generates canonical SHA-256 evidence digests for cryptographic verification.

---

## 11. Privacy

- **Module:** `privacy/privacy_manager.py`.
- **Guarantees:** Designed to operate locally without mandatory cloud services.
- **Lifecycle Management:** Temporary crop buffers and visual screenshots are purged upon audit completion or application close.

---

## 12. Security & Prompt Injection Defense

- **Module:** `ai/prompt_guard.py`, `reports/sensitive_data_detector.py`.
- **Adversarial Isolation:** Screen text containing prompt injection patterns (e.g., `"ignore previous instructions"`) is treated as inert passive forensic data and prevented from altering reasoning rules.
- **Sensitive Data Redaction:** Automatically detects and masks API tokens, credentials, emails, phone numbers, and local absolute file paths before exporting reports.

---

## 13. Hardware Abstraction

- **Module:** `hardware/hardware_detector.py`, `hardware/compute_backend.py`, `hardware/backend_status.py`.
- **Telemetry:** Queries Windows Registry (`HARDWARE\DESCRIPTION\System\CentralProcessor\0`) and CIM (`Win32_VideoController`) without throwing.
- **State Reporting:** Accurately reflects host platform without fabrication.

---

## 14. Qualcomm / Snapdragon QNN Readiness

- **Module:** `hardware/capability_matrix.py`, `ai/qualcomm_backend.py`.
- **Specification:** Pre-configured provider dictionary targeting Qualcomm Hexagon NPU:
  ```python
  qnn_options = {
      "backend_type": "htp",
      "htp_performance_mode": "burst",
      "enable_htp_fp16_precision": "1",
  }
  ```
- **Execution Hierarchy:** `QNNExecutionProvider` (primary) $\to$ `CPUExecutionProvider` (fallback).

---

## 15. Runtime Provider Fallback

- **Module:** `ai/runtime_selector.py`.
- **Logic:** Evaluates physical hardware and registered ONNX Runtime providers. On non-Snapdragon systems, automatically selects `CPUExecutionProvider` with an explicit reason logged:
  ```json
  {
      "requested_backend": "qualcomm_qnn",
      "selected_backend": "cpu",
      "fallback_reason": "Non-Snapdragon host detected (AMD/Intel development machine)",
      "hardware_verified": false
  }
  ```

---

## 16. Automated Testing

- **Suite:** 211 automated tests passing across 17 test modules in `tests/`.
- **Execution Command:** `python -m pytest tests/`
- **Coverage Areas:** Accessibility rules, geometry math, keyboard traversal, evidence fusion, reporting schema, worker lifecycle, and hardware honesty.

---

## 17. Benchmark Methodology

- **Module:** `scripts/benchmark.py`.
- **Measurement Method:** Single-pass sequential wall-clock timing across 4 standardized sample interfaces:
  - Stage 1: On-device OCR (RapidOCR)
  - Stage 2: Scene & layout analysis
  - Stage 3: Audit, rules & evidence fusion
  - Stage 4: Multi-format report generation
- **Integrity Guarantee:** Strictly measured on host AMD CPU; zero simulated Snapdragon numbers.

---

## 18. Technical Limitations

1. **Host Silicon:** All current benchmarks reflect an AMD Ryzen 3 2200U processor. Snapdragon NPU execution has not been measured.
2. **UIA Scope:** Non-standard custom controls without accessibility peers may not expose complete trees.
3. **Contrast Sampling:** Color contrast calculated from rendered pixels is influenced by font antialiasing and subpixel rendering; visual verification is recommended.
4. **Heuristic Masking:** Automated credential and PII redaction is pattern-based and requires human review.
5. **Human Review:** AccessLens AI findings are QA assistance results, not formal accessibility compliance certifications.

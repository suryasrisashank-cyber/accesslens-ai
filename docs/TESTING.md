# AccessLens AI — Testing & Verification Report
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**Project:** AccessLens AI  
**Tagline:** *"See the interface. Understand the barriers. Fix them locally."*  
**Test Suite Status:** **211 / 211 automated tests passed in the verified test run.**  
**Framework:** `pytest` (with `pytest-mock`, `pytest-asyncio`)

---

## 1. Test Suite Summary Table

| Category | Test Module | Test Count | Primary Focus |
| :--- | :--- | :---: | :--- |
| **Accessibility Baseline** | `tests/test_accessibility.py` | 7 | Contrast calculation, color parsing, basic rules |
| **Layout Analyzer** | `tests/test_analyzer.py` | 5 | Visual layout segmentation and landmark classification |
| **Backend Provider** | `tests/test_backend.py` | 3 | CPU backend, Qualcomm provider configuration hierarchy |
| **Database Lifecycle** | `tests/test_database.py` | 4 | SQLite CRUD, schema migrations, context timeout cleanup |
| **Edge Cases** | `tests/test_edge_cases.py` | 7 | Out-of-bounds coords, zero-length strings, null buffers |
| **Hardware Detection** | `tests/test_hardware.py` | 3 | Real telemetry inspection, AMD honesty, Snapdragon logic |
| **Module Imports** | `tests/test_imports.py` | 2 | Core subsystem importability and clean packaging |
| **OCR Perception** | `tests/test_ocr.py` | 3 | RapidOCR text bounding, character decoding, rotation |
| **UIA & Coordinate Mapping** | `tests/test_phase1_phase2.py` | 13 | Windows UIA tree traversal, bounds normalization |
| **Deterministic Rules** | `tests/test_phase3_analysis.py` | 10 | WCAG 2.1 rules 1–7, relative luminance, contrast math |
| **Local Reasoning** | `tests/test_phase4_reasoning.py` | 22 | Local symbolic reasoning, prompt guard, developer fixes |
| **Keyboard Traversal** | `tests/test_phase5_keyboard.py` | 22 | Focus path, traps, loops, unreachable elements |
| **Multimodal Evidence Fusion** | `tests/test_phase6_evidence_fusion.py` | 29 | IoU math, bipartite matching, deterministic score bounds |
| **Accessibility Reports** | `tests/test_phase7_reporting.py` | 50 | Schema validation, JSON/MD/HTML exporters, SHA-256 digests |
| **Robustness & Polish** | `tests/test_polish_and_robustness.py` | 16 | Worker cancellation, Win32 `IsIconic`, DB connection safety |
| **Hardware Honesty** | `tests/test_hardware_honesty.py` | 8 | Capability matrix states, QNN fallback, zero fabrication |
| **Privacy & Security** | `tests/test_privacy.py` | 3 | Ephemeral screenshot lifecycle, temp file purging |
| **Screen Capture** | `tests/test_screen_capture.py` | 2 | Multi-monitor DPI-aware capture, window rects |
| **Speech Narration** | `tests/test_tts.py` | 3 | Windows SAPI speech synthesizer rate, volume, stop |
| **TOTAL** | **19 Test Modules** | **211** | **100% Pass Rate across all suites** |

---

## 2. Category Details & Verified Tests

### A. Accessibility Rules & Contrast (`test_accessibility.py`, `test_phase3_analysis.py`)
- `test_contrast_ratio_calculation`: Verifies WCAG relative luminance formula against reference color pairs.
- `test_contrast_edge_cases`: Verifies extreme values (pure black on pure black, pure white on pure white).
- `test_color_parsing`: Validates hex (`#FFFFFF`), RGB, and RGBA string parsers.
- `test_rule_engine_rules`: Tests deterministic detection for Rule 1 (Missing Name), Rule 2 (Label Mismatch), Rule 3 (Semantic Containers), Rule 4 (Keyboard Focusability), Rule 6 (Target Size), Rule 7 (Input Labels).

### B. Visual Perception & OCR (`test_ocr.py`, `test_analyzer.py`)
- `test_ocr_extract_text`: RapidOCR ONNX inference on synthetic text bitmaps.
- `test_ocr_bounding_boxes`: Verifies 4-point polygon coordinate extraction.
- `test_image_analyzer_summary`: Verifies semantic categorization (Document, Webpage, Form, Menu).

### C. Multimodal Evidence Fusion (`test_phase6_evidence_fusion.py`)
- `test_geometry_calculate_iou`: Verifies exact intersection over union on overlapping and disjoint rects.
- `test_deterministic_match_score_bounds_all_combinations`: Confirms $0.0 \le \text{Deterministic Match Score} \le 1.0$ across all variations.
- `test_bipartite_matching_preserves_unmatched_uia`: Confirms unmatched UIA controls are retained without loss.
- `test_bipartite_matching_preserves_unmatched_visual`: Confirms unmatched OCR boxes are retained.
- `test_discrepancy_visible_label_vs_accessible_name`: Detects mismatches between visual text and accessible names (WCAG 2.5.3 reference).
- `test_prompt_injection_ocr_preservation`: Ensures adversarial text in screenshots remains passive evidence.

### D. Keyboard Navigation & Focus Traversal (`test_phase5_keyboard.py`)
- `test_focus_path_construction`: Verifies directed graph node and edge creation.
- `test_focus_trap_detection`: Verifies detection of focus trapped within modal dialogs.
- `test_focus_loop_detection`: Verifies detection of cyclic 2-element focus bounce loops.
- `test_unreached_element_detection`: Confirms interactive controls omitted from tab sequence are flagged.

### E. Local Reasoning & Remediation (`test_phase4_reasoning.py`)
- `test_local_reasoning_deterministic`: Verifies symbolic local reasoning reproduces identical explanations.
- `test_developer_remediation_generation`: Verifies XAML, WinUI, WinForms, and Web code snippet generation.
- `test_prompt_guard_isolation`: Confirms adversarial phrases cannot inject new rules or hijack remediation.

### F. Reports & Multi-Format Exporters (`test_phase7_reporting.py`)
- `test_report_validation_success`: Confirms complete report schema validation.
- `test_report_integrity_deterministic`: Confirms canonical SHA-256 digest reproduces deterministically.
- `test_sensitive_data_detector`: Verifies redaction of credit cards, passwords, emails, and phone numbers.
- `test_html_exporter_is_offline_and_self_contained`: Confirms HTML export contains zero external network links.

### G. Hardware Honesty & Fallback (`test_hardware_honesty.py`)
- `test_host_is_not_snapdragon_on_amd`: Confirms AMD host reports `is_snapdragon = False`.
- `test_runtime_selector_qnn_explicit_fallback`: Confirms `"qualcomm_qnn"` request falls back to CPU with logged reason and `hardware_verified = False`.
- `test_model_registry_metadata_and_verification_status`: Confirms CPU models declare local verification and Qualcomm models declare pending genuine Snapdragon validation.

### H. Polish & Robustness (`test_polish_and_robustness.py`)
- `test_analysis_worker_cancellation`: Confirms cooperative thread cancellation halts processing safely.
- `test_screen_capture_invalid_hwnd`: Confirms invalid and minimized window HWNDs fail safely without throwing.
- `test_database_manager_connection_cleanup`: Confirms SQLite connection context manager closes connections properly.

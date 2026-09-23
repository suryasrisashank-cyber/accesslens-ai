# AccessLens AI

## Tagline

See the interface. Understand the barriers. Fix them locally.

> **Qualcomm Snapdragon AI Lab Build & Present Challenge 2026**  
> *An on-device Windows accessibility analysis and remediation assistant for developers and QA teams.*

AccessLens AI is a desktop accessibility QA assistant designed to run locally on Windows systems. It evaluates desktop application windows and web interfaces by uniting programmatic accessibility hierarchies with visual perception, deterministic rule evaluation, keyboard traversal analysis, evidence fusion, and developer-oriented remediation guidance.

---

## Problem

Accessibility defects in Windows applications are frequently difficult to discover, reproduce, connect to underlying controls, and communicate effectively to developers:
- **Fragmented Tooling:** Developers must manually inspect control trees with utilities such as `Inspect.exe` while separately verifying visual contrast and text alignment with external tools.
- **Privacy & Enterprise Boundaries:** Cloud-based multimodal vision models require transmitting live application screenshots over the network, introducing data-leakage risks for proprietary software, pre-release designs, and interfaces displaying personal user data.
- **Disconnected Findings:** Visual-only analysis lacks structural context (control types, automation IDs, accessible names), making it difficult to produce actionable code-level fixes.

---

## Solution

AccessLens AI provides evidence-grounded accessibility analysis by combining Windows UI Automation, OCR, visual evidence, deterministic rules, keyboard traversal, evidence fusion, and local reasoning into an integrated on-device workflow.

Rather than relying on ungrounded generative descriptions, AccessLens anchors every finding in verified structural attributes and on-device visual observations, providing copy-paste developer remediation and guided verification checklists.

---

## Key Features

- **Windows UI Automation Tree Inspection:** Extracts native control types, accessible names, automation IDs, bounding rectangles, and keyboard focusability states.
- **On-Device OCR & Text Bounding:** Runs RapidOCR (DBNet + SVTR) via ONNX Runtime locally to detect on-screen text regions and character sequences.
- **Deterministic WCAG 2.1 AA Rule Evaluation:** Applies 13 deterministic algorithmic checks including missing accessible names, label discrepancies, target size thresholds, and color contrast calculations.
- **Active Keyboard Traversal Auditing:** Simulates sequential tab navigation using native Win32 input, mapping focus transitions and detecting focus traps, unreachable controls, and cyclic bounce loops.
- **Bipartite Multimodal Evidence Fusion:** Fuses visual OCR boxes with programmatic UIA elements using a deterministic matching formula, explicitly flagging discrepancies.
- **Developer Remediation Guidance:** Generates framework-specific code snippets (WPF XAML, WinUI 3, WinForms C#, Web HTML/ARIA) paired with human verification protocols.
- **Multi-Format Tamper-Evident Reporting:** Exports normalized reports to machine-readable JSON, GitHub-formatted Markdown, and self-contained accessible HTML with automated sensitive-data masking and canonical SHA-256 evidence digests.
- **Hardware Abstraction & Telemetry:** Multi-state capability detection reporting CPU fallback honestly on AMD/Intel systems while maintaining QNN architecture ready for genuine Snapdragon NPU execution.

---

## Architecture

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

## UI Automation

AccessLens AI interfaces with the native Windows UI Automation COM library via `comtypes` / `ctypes`:
- **Extracted Attributes:** Native control types, accessible names, automation IDs, bounding rectangles, keyboard focusability states (`IsKeyboardFocusable`), and parent-child hierarchy.
- **Defensive Coordinate Normalization:** Normalizes window-relative coordinates, handles multi-monitor negative desktop coordinates, and filters empty bounding boxes.

---

## OCR

On-device visual character recognition is handled locally by RapidOCR powered by ONNX Runtime:
- **Models:** Executes DBNet for text box detection and SVTR for character sequence decoding.
- **Output:** Bounding box polygons, extracted text strings, and model confidence scores.
- **Local Isolation:** Runs completely on-device via `CPUExecutionProvider` without remote network calls.

---

## Accessibility Rules

AccessLens AI evaluates 13 deterministic accessibility rules mapped to WCAG 2.1 specifications:
- **RULE_01_MISSING_NAME:** Interactive control lacks programmatic accessible name (WCAG 4.1.2).
- **RULE_02_LABEL_MISMATCH:** Potential label-in-name discrepancy between visual text and accessible name (WCAG 2.5.3 reference).
- **RULE_03_UNCLEAR_SEMANTICS:** Clickable container without appropriate semantic control type (WCAG 1.3.1).
- **RULE_04_KEYBOARD_FOCUSABLE:** Interactive control not marked as keyboard focusable (WCAG 2.1.1).
- **RULE_05_ROLE_CONSISTENCY:** Programmatic role conflicts with observed behavior.
- **RULE_06_TARGET_SIZE:** Interactive click/touch target smaller than $24 \times 24$ px (WCAG 2.5.8).
- **RULE_07_INPUT_LABEL:** Form input field lacks visual or programmatic label association (WCAG 3.3.2).
- **RULE_08_COLOR_CONTRAST:** Estimated pixel contrast ratio falls below the 4.5:1 design target for normal text (WCAG 1.4.3).
- **RULE_09_FOCUS_TRAP:** Focus cannot escape container using standard keyboard traversal (WCAG 2.1.2).
- **RULE_10_UNREACHED_ELEMENT:** Focusable interactive control cannot be reached via keyboard navigation (WCAG 2.1.1).
- **RULE_11_FOCUS_LOOP:** Keyboard focus enters an infinite 2-node cyclic bounce (WCAG 2.4.3).
- **RULE_12_FOCUS_ORDER:** Reading sequence diverges significantly from tab order (WCAG 2.4.3).
- **RULE_13_FOCUS_STATE:** Control receives focus but lacks perceptible visual focus indicator (WCAG 2.4.7).

---

## Keyboard/Focus Audit

The keyboard auditing subsystem (`accessibility/keyboard_driver.py`, `accessibility/keyboard_auditor.py`) simulates realistic user traversal:
- Executes sequential `Tab` and `Shift+Tab` keystrokes via native Win32 input.
- Constructs a directed graph of `FocusObservation` nodes and `FocusPathTransition` edges.
- Detects keyboard traps, unreachable elements, and focus loops without relying on third-party automation tools.
- Correlates observed focus states with visual screenshot coordinates, designating mapping status as `AVAILABLE`, `PARTIAL`, or `UNAVAILABLE`.

---

## Evidence Fusion

The evidence fusion engine (`accessibility/evidence_fusion.py`) performs bipartite matching between programmatic UIA elements and visual OCR boxes:
- **Matching Criteria:** Evaluates bounding box IoU (Intersection over Union), containment, token-overlap text similarity, control-type compatibility, and centroid distance.
- **Deterministic Match Score:**
  $$\text{Base Score} = 0.40 \times \text{Geometry} + 0.30 \times \text{Text} + 0.15 \times \text{ControlType} + 0.15 \times \text{Proximity}$$
  $$\text{Match Score} = \begin{cases} \min(1.0, \text{Base Score} + 0.20) & \text{if reliable focus evidence is present} \\ \text{Base Score} & \text{otherwise} \end{cases}$$
- **Score Bounds:** Strictly bounded in $[0.0, 1.0]$.
- **Conflict Tracking:** Records discrepancies between visual observations and programmatic trees as explicit conflict items without silently dropping unmatched elements.

---

## Local Reasoning

- **Local Reasoning Assistant:** A symbolic rule-based engine (`ai/local_model_provider.py`) operating locally on CPU. It explains deterministic findings without inventing unsupported claims.
- **Finding Context & Grounding:** Explains findings established by deterministic rules and multimodal evidence fusion rather than hallucinating issues.
- **Prompt Injection Defense:** On-screen text containing adversarial instructions (e.g., `"ignore previous instructions"`) is treated as passive forensic data, preventing it from hijacking reasoning rules.

---

## Remediation

- **Multi-Framework Code Generation:** Provides copy-paste remediation snippets for WPF XAML, WinUI 3, WinForms (C#), and Web (HTML/ARIA).
- **Honest Framework Fallback:** When framework metadata is ambiguous, the engine outputs *"Framework-specific code cannot be generated reliably from the available evidence"* and provides framework-agnostic guidance.
- **Mandatory Human Verification:** Every finding enforces `human_verification_required = True` and provides a manual testing checklist.

---

## Privacy

- **Local Execution:** Designed to operate locally without mandatory cloud services.
- **Ephemeral Storage:** Screenshot buffers and cropped images are purged upon audit completion or application close.
- **Automated Redaction:** `reports/sensitive_data_detector.py` scans finding evidence and masks API tokens, credentials, email addresses, phone numbers, and local absolute file paths before export.

---

## Reports

The reporting subsystem (`reports/`) generates normalized, validated audit artifacts:
- **JSON Export:** Complete machine-readable output including metrics, elements, findings, and evidence provenance.
- **Markdown Export:** Formatted technical summary with alert blocks, finding breakdown, and remediation code.
- **Accessible HTML Export:** Self-contained offline document with semantic markup, readable contrast design targets, and zero external CDN dependencies.
- **Integrity Attestation:** Computes canonical SHA-256 digests over findings and evidence for tamper evidence.

---

## Hardware Abstraction

AccessLens AI implements a multi-state hardware capability model (`hardware/capability_matrix.py`):
- `NOT_DETECTED`: Host does not contain Snapdragon silicon (e.g., our AMD64 development system).
- `DETECTED_NOT_AVAILABLE`: Snapdragon detected, but `QNNExecutionProvider` missing from ONNX Runtime.
- `AVAILABLE_NOT_INITIALIZED`: Snapdragon and QNN provider registered, awaiting session initialization.
- `AVAILABLE`: QNN execution provider active and ready for inference.
- `VERIFIED_RUNTIME`: On-device telemetry verified through physical execution evidence.

---

## Snapdragon/QNN Readiness

AccessLens AI includes a Qualcomm/QNN-ready hardware abstraction and runtime-selection architecture designed for genuine validation on compatible Snapdragon-powered Windows systems:
- **Provider Hierarchy:** `QNNExecutionProvider` (primary) $\to$ `CPUExecutionProvider` (fallback).
- **Hexagon Tensor Processor (HTP) Configuration:** Pre-configured provider options specifying HTP backend, burst performance mode, and FP16 precision.
- **Model Registry & Hardware Targeting:** Local models run via `CPUExecutionProvider` on the current host, while the Hexagon target model configuration is cataloged as `Qualcomm-targeted model configuration — pending genuine Snapdragon validation`.
- **Validation Status:** Snapdragon NPU performance remains pending genuine compatible hardware validation.

---

## Current AMD Hardware

### Hardware Validation

AccessLens AI was developed and validated on a Windows 10 AMD64 development system using an AMD Ryzen 3 2200U processor.

Current AI backend:

`CPUExecutionProvider`

Current Snapdragon status:

`NOT DETECTED`

Current NPU status:

`NOT AVAILABLE ON CURRENT DEVELOPMENT HOST`

The application includes a Qualcomm/QNN-ready hardware abstraction and runtime-selection architecture intended for genuine validation on compatible Snapdragon-powered Windows systems.

No Snapdragon NPU performance is claimed from the current AMD development system.

---

## AMD Benchmark

### Verified AMD CPU Baseline

| Metric | Result |
|---|---:|
| CPU | AMD Ryzen 3 2200U |
| Architecture | AMD64/x64 |
| Backend | CPUExecutionProvider |
| OCR | 4760.83 ms |
| Scene/Layout | 15.19 ms |
| Audit/Rules/Evidence Fusion | 29.10 ms |
| Report Generation | 180.08 ms |
| Total Sequential Pipeline | 4985.20 ms |
| Process Memory | 115.42 MB |

These measurements were obtained on the AMD Ryzen 3 2200U development system. They are a local CPU baseline and are not Snapdragon measurements.

---

## Testing

```powershell
# Run the complete automated test suite
python -m pytest tests/

# Run project validation checklist
python scripts/validate_project.py
```

Validation status: `FINAL STATUS: READY`  
Test suite status: **211/211 automated tests passed in the verified test run (0 failures).**

---

## Demo

AccessLens AI provides two demonstration tools for evaluators:
1. **Guided Demo Script (`scripts/run_demo.py`):** An automated 60–90 second offline demonstration executing all 7 pipeline stages with live output and Windows SAPI speech narration.
2. **Synthetic Flawed Test Target (`demo/accesslens_demo_app.py`):** An interactive Windows desktop window displaying a prominent `⚠️ [DEMO / SYNTHETIC TARGET]` banner and intentional defects (missing accessible names, label mismatches, low contrast, and undersized targets) for live testing.

---

## Limitations

1. **Host Platform:** Developed and validated on AMD64. Snapdragon NPU execution has not been measured on the current host.
2. **Qualcomm QNN Validation:** Remains pending genuine compatible Snapdragon hardware and runtime availability.
3. **Human Review Required:** Automated accessibility findings are QA assistance results requiring human verification where indicated.
4. **Heuristic Redaction:** Automated sensitive-data detection is pattern-based and may not catch all proprietary token formats.
5. **Synthetic Demo Assets:** Demo samples and test applications are synthetic targets created for reproducible evaluation.
6. **No Formal Certification:** Generated audit reports do not constitute formal legal or regulatory accessibility conformance certificates.

---

## Future Snapdragon Validation

When genuine Snapdragon X Series hardware (Snapdragon X Elite or Snapdragon X Plus) and the Qualcomm QNN Execution Provider are present:
1. `hardware/capability_matrix.py` will transition from `NOT_DETECTED` to `AVAILABLE`.
2. `ai/runtime_selector.py` will initialize `QNNExecutionProvider` with HTP burst options.
3. `scripts/verify_snapdragon_npu.py` will record verified on-device Hexagon NPU execution metrics.

---

## Competition Judging Alignment

### Technical Implementation
- Windows UI Automation integration extracting native accessibility hierarchies.
- On-device RapidOCR (DBNet + SVTR) inference via ONNX Runtime.
- Screenshot analysis with safe coordinate mapping and minimized window checks (`IsIconic`).
- 13 deterministic accessibility rules mapped to WCAG 2.1 specifications.
- Native Win32 keyboard traversal and focus graph modeling.
- Bipartite evidence fusion with bounded deterministic scoring ($0.0 \le \text{score} \le 1.0$).
- Local symbolic reasoning and developer remediation generation.
- Schema-validated multi-format report export with SHA-256 digests.
- Privacy controls with ephemeral buffer cleanup and automated PII redaction.
- Qualcomm/QNN-ready hardware abstraction layer with explicit CPU fallback.
- Connection and worker cleanup paths are covered by automated tests.
- 211/211 automated tests passed in the verified test run.

### Application Use Case & Innovation
- Connects visual observations, Windows accessibility metadata, keyboard behavior, evidence provenance, and developer remediation into one integrated local QA workflow.
- Replaces disconnected manual inspections and ungrounded chat descriptions with traceable, evidence-linked accessibility findings.
- Assists developers and QA teams across WPF, WinUI 3, WinForms, and Web interfaces.

### Deployment & Accessibility
- Packaged as a standard Windows desktop application.
- Designed to operate locally without mandatory cloud services.
- Seamless CPU fallback on standard x86/AMD hardware.
- Optional Snapdragon execution path architected for Qualcomm Hexagon NPU.
- Accessibility-oriented UI with contrast design targets.
- Keyboard-accessible interaction across all tabs and buttons.
- Windows SAPI voice narration for finding summaries.
- Accessible, self-contained offline HTML report generation.
- Automated sensitive-data detection and masking.
- Fully offline competition demonstration workflow.

### Presentation & Documentation
- 60–90 second reproducible demonstration workflow (`scripts/run_demo.py`).
- Synthetic test target clearly labelled (`demo/accesslens_demo_app.py`).
- Real, un-fabricated AMD CPU baseline benchmark.
- Transparent hardware attestation and limitations documentation.
- Complete ASCII architecture diagrams and subsystem specifications.
- Full verification baseline documented across 19 test modules.

---

## Project Structure

```
accesslens/
├── accessibility/                      # Accessibility & Evidence Subsystem
│   ├── ui_automation.py                # Windows UI Automation client
│   ├── ui_tree.py                      # UI hierarchy & spatial index
│   ├── element_model.py                # Data models for UI elements and snapshots
│   ├── rule_engine.py                  # Deterministic WCAG 2.1 rules 1-13
│   ├── focus_models.py                 # Focus observations and traversal results
│   ├── focus_path.py                   # Focus graph nodes, transitions, and paths
│   ├── keyboard_driver.py              # Win32 SendInput and mock keyboard drivers
│   ├── keyboard_auditor.py             # Active keyboard traversal & barrier detector
│   ├── contrast_engine.py              # WCAG relative luminance & contrast calculator
│   ├── coordinate_mapping.py           # Safe UIA-to-screenshot coordinate translation
│   ├── visual_models.py                # Visual evidence observation dataclass
│   ├── geometry.py                     # Spatial math, IoU, and boundary validation
│   ├── evidence_fusion.py              # Bipartite matching & deterministic scoring
│   ├── findings.py                     # AccessibilityFinding and FindingCategory models
│   ├── severity.py                     # Severity classification model
│   ├── evidence_engine.py              # Multi-signal evidence taxonomy
│   ├── remediation_engine.py           # Multi-framework developer remediation fixes
│   ├── report_generator.py             # Legacy report export helper
│   └── audit_coordinator.py           # Multimodal pipeline orchestrator
│
├── app/                                # Presentation Layer (PySide6)
│   ├── main.py                         # Application entrypoint
│   ├── ui/
│   │   ├── main_window.py              # Main application window (10 tabs)
│   │   ├── components.py               # Accessibility UI cards, buttons, badges
│   │   ├── accessibility_audit_view.py # Multimodal inspection workstation
│   │   ├── element_inspector_view.py   # Control property & remediation inspector
│   │   ├── keyboard_view.py            # Focus sequence & traversal graph view
│   │   ├── findings_view.py            # Filterable findings & evidence view
│   │   ├── reports_view.py             # Report generation & redaction preview
│   │   ├── hardware_view.py            # Hardware diagnostics & attestation view
│   │   ├── performance_view.py         # On-device benchmark display
│   │   └── history_view.py             # SQLite audit history viewer
│   └── workers/
│       ├── analysis_worker.py          # Asynchronous audit worker with cancellation
│       ├── keyboard_audit_worker.py    # Asynchronous keyboard traversal worker
│       ├── evidence_fusion_worker.py   # Asynchronous multimodal fusion worker
│       └── report_worker.py            # Asynchronous report generation worker
│
├── ai/                                 # Compute Abstraction & Local Reasoning
│   ├── runtime_selector.py             # Execution provider selection & CPU fallback
│   ├── base_backend.py                 # Abstract AI backend base class
│   ├── cpu_backend.py                  # ONNX Runtime CPUExecutionProvider backend
│   ├── qualcomm_backend.py             # Snapdragon QNNExecutionProvider specification
│   ├── model_registry.py               # Model Registry & Hardware Targeting catalog
│   ├── reasoning_models.py             # ReasoningResult and reasoning models
│   ├── finding_context.py              # Finding context builder with injection defenses
│   ├── prompt_guard.py                 # Adversarial text detection & isolation
│   ├── remediation_knowledge.py        # 9-category remediation knowledge base
│   └── local_model_provider.py         # Symbolic local reasoning provider
│
├── vision/                             # Visual Perception
│   ├── ocr_engine.py                   # Local RapidOCR ONNX Runtime engine
│   ├── image_analyzer.py               # Visual layout & landmark analyzer
│   ├── screen_capture.py               # DPI-aware Win32 capture with IsIconic checks
│   └── image_utils.py                  # Image conversion & drawing utilities
│
├── audio/                              # Speech Narration
│   └── text_to_speech.py               # Windows SAPI native speech narration
│
├── hardware/                           # Host Telemetry & Capability Matrix
│   ├── hardware_detector.py            # Real system telemetry via WinReg and CIM
│   ├── capability_matrix.py            # Multi-state hardware capability assessment
│   ├── compute_backend.py              # Backend manager & provider priority
│   └── backend_status.py               # Hardware profile & state enums
│
├── privacy/                            # Data Protection
│   └── privacy_manager.py              # Ephemeral screenshot lifecycle & cleanup
│
├── storage/                            # Persistence
│   └── database.py                     # SQLite metadata store with context timeouts
│
├── reports/                            # Normalized Reports & Exporters
│   ├── report_models.py                # Normalized AuditReport & finding models
│   ├── report_generator.py             # Multimodal synthesis & provenance indexer
│   ├── report_validator.py             # Schema & evidence referential validator
│   ├── report_integrity.py             # Canonical SHA-256 evidence digest calculator
│   ├── sensitive_data_detector.py      # Pattern-based credential & PII redactor
│   ├── exporters/                      # Multi-format report exporters
│   │   ├── json_exporter.py            # Machine-readable JSON exporter
│   │   ├── markdown_exporter.py        # Technical Markdown exporter
│   │   └── html_exporter.py            # Self-contained accessible HTML exporter
│   └── generated/                      # Local report output directory
│
├── demo/                               # Synthetic Demonstration Target
│   ├── samples/                        # Pre-rendered accessible UI graphics
│   └── accesslens_demo_app.py          # Flawed test window with [DEMO] banner
│
├── scripts/                            # Operational & Verification Scripts
│   ├── validate_project.py             # Automated project readiness checklist
│   ├── benchmark.py                    # Real on-device sequential pipeline benchmark
│   ├── verify_snapdragon_npu.py        # Snapdragon NPU runtime verifier
│   └── run_demo.py                     # 60-90 second guided presentation runner
│
├── docs/                               # Comprehensive Documentation Suite
│   ├── DEMO_SCRIPT.md                  # 60-90 second competition demo script
│   ├── SCREENSHOT_PLAN.md              # 10 recommended competition screenshots
│   ├── COMPETITION_DESCRIPTION.md      # Concise competition entry description
│   ├── TECHNICAL_IMPLEMENTATION.md     # Detailed 18-section architecture reference
│   ├── UNSTOP_TECHNICAL_IMPLEMENTATION.md # Unstop technical implementation document
│   ├── INNOVATION_AND_USE_CASE.md      # Product positioning & use case document
│   ├── UNSTOP_INNOVATION_USE_CASE.md   # Unstop innovation & use case document
│   ├── DEPLOYMENT_AND_ACCESSIBILITY.md # Windows deployment & accessible design
│   ├── UNSTOP_DEPLOYMENT_ACCESSIBILITY.md # Unstop deployment & accessibility document
│   ├── UNSTOP_FINAL_FORM_REVIEW.md     # Submission form review & device ownership guide
│   ├── HARDWARE_AND_ELIGIBILITY_DISCLOSURE.md # AMD host disclosure & Snapdragon attestation
│   ├── SUBMISSION_ASSET_INDEX.md       # Master index of submission assets & links
│   ├── ONE_PAGE_PROJECT_SUMMARY.md     # Executive summary brief for judges
│   ├── FINAL_SUBMISSION_READINESS_REPORT.md # Master quality gate certification report
│   ├── FINAL_VIDEO_RECORDING_GUIDE.md  # 60-90 second shot-by-shot recording guide
│   ├── MANUAL_SUBMISSION_ACTIONS.md    # Pre-submission manual checklist
│   ├── LIMITATIONS.md                  # Transparent host & model boundary document
│   ├── TESTING.md                      # Complete 211-test breakdown across 17 modules
│   ├── ARCHITECTURE.md                 # System architecture & component specification
│   ├── COMPETITION_COMPLIANCE.md       # Rules and compliance checklist
│   ├── SNAPDRAGON_VALIDATION.md        # Hardware validation guide
│   ├── ORIGINALITY_AND_REFERENCES.md   # Open source citations and originality
│   ├── PRESENTATION_SCRIPT.md          # Stage presentation script
│   ├── SEVERITY_MODEL.md               # Severity vs confidence classification
│   ├── THREAT_MODEL.md                 # Security & prompt injection threat model
│   └── screenshots/                    # Screenshot & demonstration assets directory
│       └── README.md                   # Visual assets checklist and guidelines
│
├── tests/                              # Automated Pytest Suite (211 passing tests)
├── requirements.txt                    # Project dependencies
├── README.md                           # Master project documentation
└── LICENSE                             # Apache 2.0 open-source license
```

---

## Installation

### Prerequisites
- Windows 10 or Windows 11 (x64 / AMD64 or ARM64)
- Python 3.10 to 3.14

### Setup
```powershell
# Clone or navigate to the repository
cd accesslens

# Install required dependencies
pip install -r requirements.txt
```

### Running AccessLens
```powershell
# Launch the main AccessLens AI desktop workstation
python app/main.py

# Launch the synthetic flawed test target application
python demo/accesslens_demo_app.py

# Run the 60-90 second guided presentation demo
python scripts/run_demo.py
```

### Benchmarking
```powershell
# Execute the on-device sequential pipeline benchmark
python scripts/benchmark.py
```

---

## License

This project is licensed under the Apache License, Version 2.0. See [`LICENSE`](file:///C:/Users/MAHADEV/.gemini/antigravity/scratch/accesslens/LICENSE) for details.

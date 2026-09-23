# AccessLens AI — Accessibility Severity Model & Evidence Framework

**Project:** AccessLens AI — On-Device Accessibility Inspection & Remediation Assistant  
**Standards Reference:** W3C Web Content Accessibility Guidelines (WCAG) 2.1 Level AA & Microsoft Windows Accessibility Guidelines

> [!IMPORTANT]
> **Human Review Requirement:**
> "Automated accessibility findings are intended to assist accessibility QA and require human review."

---

## 1. Severity vs. Confidence Separation

In AccessLens AI, **Severity** and **Confidence** are strictly independent dimensions:

- **Severity (Potential Impact):** Reflects how significantly the barrier affects users relying on assistive technologies (screen readers, speech input, switch controls, keyboard navigation). Severity describes user impact, not how certain the detector is.
  - **HIGH:** Significant barrier preventing standard assistive interaction (e.g. interactive control without accessible name, unfocusable interactive control, severe contrast failure).
  - **MEDIUM:** WCAG 2.1 AA deviation or moderate accessibility barrier (e.g. visible label vs accessible name discrepancy, undersized click target, moderate contrast issue).
  - **LOW:** Minor advisory or minor usability friction (e.g. generic control type exposing action patterns).
  - **INFO:** Informational observation, focus state telemetry, or guidance.
  - *(CRITICAL is reserved strictly for deterministically verified total task blockers, such as endless keyboard focus traps).*

- **Confidence (Evidence Strength):** Reflects the mathematical or programmatic certainty of the supporting evidence:
  - Programmatic Windows UI Automation direct properties: **0.90 – 0.96**
  - OCR corroborated text overlap: **0.85 – 0.90**
  - Visual heuristic pixel inferences: **0.60 – 0.85**
  - *Confidence never claims 100% unless mathematically verified.*

---

## 2. Evidence Categorization & Traceability

Every finding exposes an evidence chain where each item is classified into one of four immutable types:

1. **`[MEASURED]`**: Mathematically calculated metrics (e.g., target dimensions 14×14 px, contrast ratio 2.4:1).
2. **`[DETECTED]`**: Directly queried from Windows UI Automation APIs or RapidOCR text recognition.
3. **`[INFERRED]`**: Contextual visual layout or semantic consistency observations.
4. **`[RECOMMENDED]`**: Specific developer remediation instructions (XAML, WinUI, WinForms, ARIA).

---

## 3. Multimodal Analysis Signals

| Signal Source | Method | Role in Analysis | Inherent Limitations |
| :--- | :--- | :--- | :--- |
| **Windows UI Automation (UIA)** | Read-only OS tree extraction via Microsoft UIAutomation API | Queries control types, accessible names, focusability, patterns, and bounds | Legacy custom controls or OwnerDraw GDI elements may omit properties |
| **RapidOCR (ONNX Runtime)** | Local ONNX OCR execution | Detects visible text on screen and correlates with UIA bounding boxes | Subject to resolution, font antialiasing, and complex graphical backgrounds |
| **Visual Analysis & Contrast** | Relative luminance and regional pixel sampling | Calculates WCAG 2.1 contrast ratios and evaluates interactive sizes | Labeled as *"Estimated from rendered pixels"*; affected by subpixel font smoothing |
| **Deterministic Rules** | Modular rule engine (`rule_engine.py`) | Evaluates compliance against WCAG 2.1 AA criteria without AI hallucinations | Evaluates static and programmatic states; cannot evaluate subjective copy quality |

---

## 4. Evidence Chain Structure

For every finding, AccessLens AI delivers a complete, grounded chain:

```
Finding Title & Severity
   ↓
Why Detected (Observation)
   ↓
Evidence (Grounded [MEASURED], [DETECTED], [INFERRED] items)
   ↓
Why This Matters (Assistive impact)
   ↓
Recommended Action (Developer code snippet)
   ↓
Human Verification (Specific check for human reviewer)
   ↓
Source Attribution
```

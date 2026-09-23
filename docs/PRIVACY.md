# AccessLens AI — Privacy Architecture & Data Governance

**Project:** AccessLens AI  
**Tagline:** *"See. Understand. Listen."*  
**Mission:** *"See the interface. Understand the barriers. Fix them locally."*  
**Document:** Local-First Privacy Specification & Governance  
**Date:** September 2026  

---

## 1. Core Privacy Philosophy

Accessibility testing tools frequently handle sensitive desktop surfaces, including enterprise dashboards, proprietary software source code, internal admin panels, and personal user data. Traditional cloud-based AI tools transmit raw screen captures and DOM/UIA trees to remote third-party servers, posing severe compliance risks under GDPR, HIPAA, and corporate intellectual property policies.

**AccessLens AI is engineered under a strict Local-First Privacy Architecture.**
- **No Cloud AI APIs:** Zero outbound API calls to OpenAI, Google Gemini, Anthropic, or external inference endpoints.
- **No Telemetry or Phone-Home:** Zero telemetry beacons, analytics trackers, or user behavioral telemetry.
- **No Account / Authentication Lock-in:** The software runs completely standalone without requiring sign-ins, API keys, or credit cards.
- **Air-Gapped Operation:** AccessLens AI functions with full fidelity in offline or air-gapped network environments.

---

## 2. Ephemeral In-Memory Data Pipeline

Desktop visual buffers and UI Automation structures are strictly ephemeral:

```
[Screen / Window] 
       │
       ▼
[Pillow/RapidOCR Buffer in RAM] ──▶ [Transient Memory Extraction]
       │                                     │
       ▼                                     ▼
[Immediate Redaction/Inspection]      [WCAG Rule Engine & Local AI]
       │                                     │
       ▼                                     ▼
[Memory Released (del / GC)]          [Structured Findings Model]
                                             │
                                             ▼
                                  [Local SQLite DB Only]
```

1. **Screen Capture Buffers:** Frame buffers captured for OCR or element inspection reside solely in volatile RAM. They are never automatically written to permanent disk storage unless the user explicitly clicks **"Export Screenshot"**.
2. **Immediate Garbage Collection:** After optical character recognition and visual bounding box calculations complete, raw pixel arrays are unreferenced and garbage collected.
3. **No Background Recording:** Audits are user-initiated snapshot evaluations or controlled keyboard traversals; continuous passive recording is not performed.

---

## 3. Sensitive Data Redaction Engine

AccessLens AI incorporates an automated, heuristic sensitive data detector (`reports/sensitive_data_detector.py`) that executes before any audit findings, JSON exports, HTML summaries, or Markdown reports are generated:

### Redaction Categories:
- **Payment Card Numbers:** Matches 13–16 digit credit/debit card sequences and replaces them with `[REDACTED_PAYMENT_CARD]`.
- **Email Addresses:** Matches standard RFC email addresses and replaces them with `[REDACTED_EMAIL]`.
- **Phone Numbers:** Matches international and domestic phone number patterns and replaces them with `[REDACTED_PHONE]`.
- **API Keys & Credentials:** Matches tokens, passwords, bearer keys, and secret tokens (`api_key`, `bearer`, `secret`, `password`) and replaces them with `[REDACTED_CREDENTIAL]`.
- **User File Paths:** Masks local user profiles (`C:\Users\<username>`) as `[REDACTED_PATH]`.

### Disclaimer & Human-in-the-Loop Review
> **Important Privacy Notice:** Automated sensitive content detection is a heuristic safeguard designed to assist privacy reviews. It does not claim or guarantee 100% identification of all personally identifiable information or proprietary secrets. Users are provided an interactive preview of audit findings prior to export, allowing manual review and redaction confirmation.

---

## 4. Local Storage Governance

Any persistence utilized by AccessLens AI is strictly local to the user's workstation:
- **Database:** Local SQLite database located in the application workspace (`storage/database.py`).
- **Reports:** Generated strictly upon explicit user request in the local `reports/generated/` folder.
- **No Remote Sync:** Database files and report exports never synchronize with remote cloud storage buckets or external servers.

---

## 5. Security & Threat Modeling Summary

As documented in `docs/THREAT_MODEL.md`:
- **Threat:** Accidental leakage of enterprise credentials displayed on screen.
  - *Mitigation:* Local-first execution prevents external transmission; heuristic detector redacts tokens before export.
- **Threat:** Prompt injection or malicious accessibility properties designed to alter AI remediation.
  - *Mitigation:* `ai/prompt_guard.py` sanitizes accessibility names and OCR tokens before evaluation; deterministic WCAG rules are isolated from heuristic reasoning.
- **Threat:** Network snooping or man-in-the-middle attacks.
  - *Mitigation:* Nil attack surface due to zero network requests during audit cycles.

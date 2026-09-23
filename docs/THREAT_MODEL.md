# AccessLens AI — Security & Privacy Threat Model

**Project:** AccessLens AI — On-Device Accessibility Inspection & Remediation Assistant  
**Core Model:** Local-First, Zero-Cloud, Least-Privilege Operation

---

## 1. Security Scope & Boundaries

AccessLens AI is an on-device accessibility QA and developer inspection tool. It operates strictly within the Windows user security context (standard user privileges) and does not require elevated administrator rights, kernel drivers, or system hooks.

### Explicit Security Boundaries:
- **No Network Egress**: The application performs zero outbound HTTP/HTTPS requests, zero telemetry uploads, and zero cloud API invocations during operation.
- **No Authentication Circumvention**: Does not attempt to bypass login screens, lockouts, or UAC prompts.
- **No Destructive Automation**: Does not submit forms, execute destructive keystrokes, or simulate unauthorized mouse clicks.
- **No Credential Harvesting**: Actively masks sensitive credential tokens, API keys, passwords, and payment card numbers before export.

---

## 2. Threat Analysis & Mitigations

| Threat Vector | Potential Impact | AccessLens AI Mitigation |
| :--- | :--- | :--- |
| **Exfiltration of Screen Data** | Visual leakage of confidential enterprise software content. | **Guaranteed On-Device Processing**: All OCR, UI Automation traversal, and rule evaluations execute strictly in local memory. No cloud communication paths exist. |
| **Residual Screenshot Exposure** | Unencrypted temporary capture bitmaps remaining on disk. | **Ephemeral Lifecycle Management**: All screen capture files registered with `PrivacyManager` are purged automatically upon session termination via Python `atexit` handlers. |
| **Sensitive Data in Reports** | Developers exporting audit reports that accidentally contain API keys or employee emails. | **Conservative Redaction Engine**: Automated regex scanning masks emails (`[REDACTED_EMAIL]`), phone numbers (`[REDACTED_PHONE]`), credentials (`[REDACTED_CREDENTIAL]`), and card sequences (`[REDACTED_PAYMENT_CARD]`). |
| **Malicious UIA Injection** | Rogue software exploiting accessibility APIs to inject keystrokes. | **Read-Only Inspection**: AccessLens AI only *reads* UIA properties (TreeScope Children and Descendants). It never writes values to arbitrary external windows or invokes actionable patterns unprompted. |
| **Denial of Service via Heavy Trees** | Complex desktop apps with thousands of controls causing memory exhaustion or UI freezes. | **Timeout & Pagination Bounds**: UIA inspection executes in isolated worker threads with a strict 6-second timeout and a configurable maximum element ceiling (default: 150 elements). |

---

## 3. Human Review & Verification Principle

Automated reports explicitly include the mandatory disclaimer:
> *"Automated findings are assistance for accessibility QA and should be reviewed by a qualified human tester."*

This ensures developer teams use AccessLens AI as an intelligent assistant to augment, rather than replace, human judgment and compliance audits.

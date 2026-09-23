# AccessLens AI — Technical Limitations & Disclaimers
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**Project:** AccessLens AI  
**Tagline:** *"See the interface. Understand the barriers. Fix them locally."*  
**Scope:** Transparent Documentation of Host, Model, and Evaluation Boundaries

---

### Explicit Project Limitations

1. **Current Host Platform is AMD64:** AccessLens AI was developed and validated on an AMD64 Windows system equipped with an AMD Ryzen 3 2200U processor.
2. **Snapdragon NPU Execution Not Measured on Current Host:** Physical Qualcomm Snapdragon silicon is not present on the development machine. Therefore, Snapdragon NPU execution and performance benchmarks have not been measured on the current host.
3. **Qualcomm QNN Validation Pending Genuine Hardware:** The architecture includes a Qualcomm/QNN-ready hardware abstraction layer (`QNNExecutionProvider` specification). Full on-device validation remains pending access to genuine Snapdragon X Series hardware and compatible runtime environments.
4. **Human Verification Required:** Automated accessibility findings are intended to assist QA teams and do not replace professional accessibility audits. All findings require human verification where indicated.
5. **Heuristic Sensitive Data Redaction:** Automated detection of credentials, API keys, and personal identifiers is pattern-based and heuristic. While conservative, it cannot guarantee detection of all proprietary or sensitive formats.
6. **Synthetic Demo Targets:** The demo application (`demo/accesslens_demo_app.py`) and pre-rendered sample graphics (`demo/samples/`) are synthetic test targets created for reproducible evaluation. They do not represent real commercial or institutional software audits.
7. **Hardware-Specific Benchmarks:** All reported latency metrics reflect the specific AMD Ryzen 3 2200U CPU development environment and should not be construed as universal performance figures.
8. **No Formal Accessibility Certification:** Generated JSON, Markdown, and HTML reports are engineering QA aids; they do not constitute formal legal or regulatory accessibility compliance certification (e.g., VPAT or WCAG compliance certificates).

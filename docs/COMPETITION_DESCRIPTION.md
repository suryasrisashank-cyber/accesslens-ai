# AccessLens AI — Competition Entry Description
## Qualcomm Snapdragon AI Lab Build & Present Challenge 2026

**PROJECT:**  
AccessLens AI

**TAGLINE:**  
See the interface. Understand the barriers. Fix them locally.

---

### PROBLEM

Accessibility defects in Windows desktop applications and web interfaces are difficult to discover, reproduce, connect to underlying UI elements, and communicate effectively to developers. Traditional testing requires manual inspection using fragmented tools like `Inspect.exe`, while cloud-based vision models introduce privacy risks, high latency, and lack direct connection to the programmatic accessibility tree.

---

### SOLUTION

AccessLens AI combines Windows UI Automation (UIA), visual OCR (RapidOCR via ONNX Runtime), screenshot evidence, keyboard focus traversal, deterministic accessibility rules, evidence fusion, and local reasoning to produce traceable findings and actionable developer remediation guidance. Rather than treating interfaces as flat pixels or raw trees in isolation, AccessLens fuses visual and structural signals into a unified inspection pipeline.

---

### PRIVACY

Processing is designed around local execution without a mandatory cloud service. All OCR inference, image analysis, UI automation extraction, and rule evaluation execute entirely on the local device, ensuring that proprietary application interfaces and sensitive on-screen data never leave the user's computer.

---

### SNAPDRAGON READINESS

The architecture includes a Qualcomm/QNN-ready hardware abstraction layer designed to target the Qualcomm Hexagon NPU on Snapdragon X Series PCs via `QNNExecutionProvider`. The current development host is AMD64, so Snapdragon NPU execution and performance benchmarks have not been claimed as measured results.

---

### VALIDATION

211/211 automated tests passed in the verified run, confirming pipeline robustness, deterministic scoring bounds, thread safety, and hardware honesty.

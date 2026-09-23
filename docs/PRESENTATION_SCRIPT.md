# AccessLens AI — 60–90 Second Competition Presentation Script

**Project:** AccessLens AI — *"See the interface. Understand the barriers. Fix them locally."*  
**Audience:** Qualcomm Snapdragon AI Lab Challenge 2026 Evaluation Panel  
**Mode:** 100% Offline, Live Reproducible Desktop Presentation

---

## Live Demonstration Flow (60–90 Seconds)

### [00:00 – 00:15] Introduction & On-Device Reality
- **Action:** Launch AccessLens AI (`python app/main.py` or run `python scripts/run_demo.py`).
- **Presenter:**  
  *"Judges, this is AccessLens AI. Traditional AI screen tools simply describe what is on screen like a chatbot. AccessLens asks a much more rigorous question: 'Can this Windows interface be understood and operated accessibly, and what evidence supports that finding?' Notice the top banner: Local Only. In the Hardware Diagnostics tab, you see our host laptop: an AMD Ryzen CPU running with verified CPU fallback. We do not fabricate NPU results on non-Qualcomm hardware. But the architecture is completely decoupled for Snapdragon X Series deployment via ONNX Runtime and QNN."*

---

### [00:15 – 00:35] Target Capture & Multimodal Fusion
- **Action:** Click **"🚀 Launch Synthetic Demo App"** to pop up the test application, then click **"📸 Capture Interface"** (or select Sample 1).
- **Presenter:**  
  *"To demonstrate with complete reproducibility, we launch our synthetic test target containing known accessibility flaws. When we click 'Capture Interface', AccessLens executes our multimodal pipeline: extracting the Windows UI Automation tree, running local ONNX OCR, and performing deterministic WCAG 2.1 checks. Within seconds, it identifies 7 distinct accessibility barriers."*

---

### [00:35 – 00:55] Evidence Engine & Developer Remediation
- **Action:** Switch to **"Findings & Evidence"** tab, click the Critical finding (*"Missing Accessible Name"* or *"Label Discrepancy"*), and click **"🔊 Read Finding Aloud"**.
- **Presenter:**  
  *"Look at how AccessLens grounds its findings. Every barrier is classified by signal type: [DETECTED] via UI Automation, [MEASURED] for color contrast ratios and button dimensions, and [INFERRED] for layout flow. In the right panel, AccessLens gives developers immediate, actionable XAML and C# remediation code. Listen as Windows SAPI reads the finding aloud for accessibility teams."*

---

### [00:55 – 01:15] Keyboard Focus Audit & Automated Reports
- **Action:** Switch to **"Keyboard Audit"** tab, click **"▶ Run Tab Traversal Audit"**, then switch to **"Reports & Redaction"** tab.
- **Presenter:**  
  *"Accessibility is not just visual. In the Keyboard Audit tab, AccessLens records sequential tab stops, detecting keyboard traps and unreachable controls. When exporting to Markdown, JSON, or HTML, our sensitive data engine automatically redacts credentials, phone numbers, and payment details."*

---

### [01:15 – 01:30] Snapdragon NPU Architecture & Conclusion
- **Action:** Switch to **"Hardware Diagnostics"** tab and highlight the QNN Execution Provider card.
- **Presenter:**  
  *"By moving text recognition and multimodal analysis from CPU to the Qualcomm Hexagon NPU on Snapdragon X Series PCs—rated up to 45 TOPS in platform specifications—AccessLens is engineered to deliver fast, private, on-device accessibility QA for every Windows developer. Thank you."*

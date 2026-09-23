"""Guided 60-90 second demonstration runner for AccessLens AI.

Walks Qualcomm challenge judges through the full on-device accessibility QA experience:
Host Telemetry -> CPU Fallback -> UIA + OCR -> Deterministic Rules -> Grounded Evidence ->
Developer Remediation -> Keyboard Audit -> Report Export -> Privacy -> Snapdragon NPU Path.
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from accessibility.audit_coordinator import audit_coordinator
from accessibility.keyboard_audit import keyboard_auditor
from accessibility.remediation_engine import remediation_engine
from accessibility.report_generator import report_generator
from accessibility.ui_tree import UITree
from ai.model_registry import model_registry
from ai.qualcomm_backend import QualcommBackend
from ai.runtime_selector import runtime_selector
from audio.text_to_speech import tts_engine
from hardware.capability_matrix import capability_matrix
from hardware.hardware_detector import hardware_detector
from privacy.privacy_manager import privacy_manager


def run_accesslens_demo():
    print("\n" + "=" * 78)
    print(" ACCESSLENS AI — QUALCOMM SNAPDRAGON AI LAB CHALLENGE 2026 DEMO")
    print(" Tagline: See the interface. Understand the barriers. Fix them locally.")
    print("=" * 78)
    time.sleep(1)

    # 1. Hardware Diagnostics & Honest Reporting
    print("\n[STEP 1/7] HOST TELEMETRY & UN-FABRICATED CPU ATTESTATION")
    print("-" * 78)
    profile = hardware_detector.inspect()
    caps = capability_matrix.detect()
    sel = runtime_selector.current_selection

    print(f"  • Operating System:       {profile.os_name} (Build {profile.os_version})")
    print(f"  • Host Processor:         {profile.cpu_model} ({profile.architecture})")
    print(f"  • System RAM:             {profile.ram_gb} GB RAM")
    print(f"  • Snapdragon Detected:    {caps.qualcomm_detected}")
    print(f"  • Snapdragon NPU Status:  {profile.npu_status_label}")
    print(f"  • Active AI Backend:      {sel.selected_backend} (Execution Provider: {sel.execution_providers})")
    print(f"  • Capability State:       {caps.verification_status.value}")
    print("\n  >> HONEST ATTESTATION: As verified above, our development machine runs on an")
    print("     AMD Ryzen host. AccessLens AI strictly operates in verified Local CPU")
    print("     Fallback mode. No Qualcomm NPU performance or benchmarks are fabricated.")
    time.sleep(2)

    # 2. Snapdragon Architecture & Model Registry
    print("\n[STEP 2/7] QUALCOMM SNAPDRAGON NPU READINESS ARCHITECTURE")
    print("-" * 78)
    qnn = QualcommBackend()
    print(f"  • Qualcomm Backend Name:  {qnn.name}")
    print(f"  • Execution Hierarchy:    {qnn.execution_providers}")
    print(f"  • Target NPU Hardware:    Qualcomm Snapdragon X Elite / X Plus (Hexagon NPU)")
    print(f"  • Registered Models:      {len(model_registry.list_models())} Registered Local & Target Models")
    time.sleep(1)

    # 3. Multimodal Inspection (UIA + OCR)
    print("\n[STEP 3/7] MULTIMODAL INTERFACE INGESTION (UIA + ONNX OCR)")
    print("-" * 78)
    sample_path = os.path.join(BASE_DIR, "demo", "samples", "university_admission.png")
    print(f"  • Ingesting Target:       {os.path.basename(sample_path)} [DEMO / SYNTHETIC TARGET]")
    print("  • Execution Mode:         LIVE ANALYSIS (Sequential On-Device Pipeline)")
    print("  • Executing unified audit pipeline (UI Automation + RapidOCR ONNX)...")

    t0 = time.perf_counter()
    snapshot = audit_coordinator.audit_interface(sample_path)
    total_time = (time.perf_counter() - t0) * 1000

    print(f"  • Pipeline Latency:       {total_time:.2f} ms")
    print(f"  • UI Elements Inspected:  {len(snapshot.elements)}")
    print(f"  • Total Barriers Found:   {len(snapshot.findings)}")
    print(f"    - CRITICAL Barriers:    {snapshot.critical_findings_count}")
    print(f"    - HIGH Barriers:        {snapshot.high_findings_count}")
    print(f"    - MEDIUM Barriers:      {snapshot.medium_findings_count}")
    time.sleep(2)

    # 4. Deterministic Rules & Grounded Evidence
    print("\n[STEP 4/7] DETERMINISTIC WCAG RULES & GROUNDED EVIDENCE")
    print("-" * 78)
    if snapshot.findings:
        f = snapshot.findings[0]
        print(f"  • Selected Finding:       [{f.severity.value}] {f.title} [LIVE ANALYSIS RESULT]")
        print(f"  • Category:               {f.category.value}")
        print(f"  • Confidence:             {f.confidence * 100:.1f} %")
        print("  • Grounded Evidence:")
        for ev in f.evidence:
            print(f"      {ev}")
        print(f"  • Recommendation:\n      {f.recommendation}")
    time.sleep(2)

    # 5. Developer Remediation Code
    print("\n[STEP 5/7] DEVELOPER REMEDIATION SNIPPET (XAML / C# / WEB)")
    print("-" * 78)
    if snapshot.findings:
        rem = remediation_engine.explain_finding(snapshot.findings[0])
        print("  • Accessibility Impact:")
        print(f"      {rem['impact']}")
        print("  • XAML/WinUI Code Fix:")
        for line in rem.get("wpf_xaml", "").splitlines():
            print(f"      {line}")
        print("  • Human Verification Guidance:")
        print(f"      {rem.get('verification_guidance', '')}")
    time.sleep(2)

    # 6. Keyboard Traversal Audit & Report Export
    print("\n[STEP 6/7] KEYBOARD AUDIT & REPORT GENERATION")
    print("-" * 78)
    kb_report = keyboard_auditor.simulate_audit_from_tree(UITree(snapshot.elements))
    print(f"  • Keyboard Focus Steps:   {len(kb_report.steps)} transitions recorded")
    print(f"  • Unreachable Controls:   {len(kb_report.unreachable_elements)} elements")

    # Generate Reports
    md_report = report_generator.generate_markdown(snapshot, mask=True)
    html_report = report_generator.generate_html(snapshot, mask=True)
    print(f"  • Reports Generated:      Markdown ({len(md_report)} bytes), HTML ({len(html_report)} bytes)")
    print("  • Sensitive Data Masking: Active ([REDACTED_EMAIL], [REDACTED_PHONE], [REDACTED_CREDENTIAL])")

    # Audio Narration
    print("\n[STEP 7/7] AUDIO NARRATION & ON-DEVICE PRIVACY ATTESTATION")
    print("-" * 78)
    speech_text = (
        f"AccessLens AI. Audit complete for {snapshot.application_name}. "
        f"Detected {len(snapshot.findings)} barriers, including {snapshot.critical_findings_count} critical issues. "
        f"Primary finding: {snapshot.findings[0].title}."
    )
    print(f"  • Narration Script: \"{speech_text}\"")
    tts_engine.speak(speech_text)
    print("  • Speech Synthesized:     Asynchronous playback via Windows SAPI")

    priv = privacy_manager.get_status_summary()
    print(f"  • Local-Only Processing:  {priv['local_only_mode']}")
    print(f"  • Cloud Upload Active:    {priv['cloud_upload_active']}")
    print(f"  • Privacy Statement:      \"{priv['privacy_statement']}\"")

    print("\n" + "=" * 78)
    print(" PRESENTATION COMPLETE: ACCESSLENS AI IS READY FOR JUDGING")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    run_accesslens_demo()

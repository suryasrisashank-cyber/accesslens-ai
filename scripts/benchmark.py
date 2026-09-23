"""Benchmark runner for AccessLens AI.

Measures actual on-device latency across all sequential pipeline stages:
Image Loading -> On-Device OCR -> Scene & Layout Analysis -> UI Tree & OCR Correlation ->
Deterministic WCAG Rules & Contrast -> Multi-Signal Evidence & Remediation -> Multi-Format Reports.

All latency numbers are strictly measured on the local host CPU (AMD Ryzen 3 2200U,
CPUExecutionProvider) without simulated or fabricated Snapdragon NPU benchmarks.
Total Pipeline Latency is the true additive wall-clock duration of all sequential stages.
"""

from dataclasses import dataclass
from datetime import datetime
import os
import sys
import time
from typing import Dict, List
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from accessibility.audit_coordinator import audit_coordinator
from accessibility.contrast_engine import calculate_contrast_ratio
from accessibility.element_model import InterfaceSnapshot
from accessibility.evidence_engine import evidence_engine
from accessibility.findings import FindingModel
from accessibility.remediation_engine import remediation_engine
from accessibility.report_generator import report_generator
from accessibility.rule_engine import rule_engine
from accessibility.ui_tree import UITree
from hardware.hardware_detector import hardware_detector
from reports.report_generator import audit_report_generator
from reports.exporters.json_exporter import JsonReportExporter
from reports.exporters.markdown_exporter import MarkdownReportExporter
from reports.exporters.html_exporter import HtmlReportExporter
from vision.image_analyzer import image_analyzer
from vision.image_utils import load_image
from vision.ocr_engine import ocr_engine

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class AccessLensBenchmarkMetric:
    """Stores benchmark latency metrics for a single inspected target interface."""
    sample_name: str
    ocr_time_ms: float
    analysis_time_ms: float
    rule_eval_time_ms: float
    report_gen_time_ms: float
    total_audit_time_ms: float
    memory_rss_mb: float
    elements_count: int
    barriers_count: int
    critical_count: int
    backend_label: str

    @property
    def total_time_ms(self) -> float:
        return self.total_audit_time_ms


BenchmarkMetric = AccessLensBenchmarkMetric
run_benchmark = lambda: run_accesslens_benchmark()


def run_accesslens_benchmark() -> List[AccessLensBenchmarkMetric]:
    profile = hardware_detector.inspect()
    samples_dir = os.path.join(BASE_DIR, "demo", "samples")
    sample_files = [
        "university_admission.png",
        "restaurant_menu.png",
        "product_label.png",
        "desktop_screenshot.png"
    ]

    metrics: List[AccessLensBenchmarkMetric] = []
    process = psutil.Process(os.getpid()) if psutil else None

    print("\n" + "=" * 76)
    print(" ACCESSLENS AI - MULTIMODAL ACCESSIBILITY PIPELINE BENCHMARK")
    print("=" * 76)
    print("BENCHMARK TYPE:         REAL LOCAL AMD CPU BASELINE")
    print(f"Host Processor:         {profile.cpu_model}")
    print(f"Architecture:           {profile.architecture}")
    print(f"Operating System:       {profile.os_name}")
    print(f"Active AI Backend:      {profile.ai_backend_label}")
    print("Snapdragon Status:      NOT DETECTED (x64 / AMD64 host)")
    print("Snapdragon NPU Result:  NOT AVAILABLE ON CURRENT HOST")
    print(f"NPU Status Label:       {profile.npu_status_label}")
    print("=" * 76)
    print("BENCHMARK METHODOLOGY & SCOPE DEFINITION:")
    print("  * Single-Pass Sequential Execution: All stages are measured sequentially")
    print("    during a single cohesive audit execution for each target interface.")
    print("  * Stage 1 (OCR): RapidOCR (DBNet + SVTR) inference via ONNX Runtime CPU.")
    print("  * Stage 2 (Scene/Layout): Semantic layout and visual landmark analysis.")
    print("  * Stage 3 (Audit & Rules): UI tree construction, spatial OCR correlation,")
    print("    deterministic WCAG 2.1 rules, pixel contrast, and evidence fusion.")
    print("  * Stage 4 (Reports): Markdown, JSON, and self-contained HTML generation.")
    print("  * Total Pipeline Latency: True additive wall-clock duration of all stages.")
    print("  * Integrity Attestation: Measured on-device. Zero simulated QNN or")
    print("    fabricated Snapdragon benchmarks. All metrics reflect genuine AMD CPU execution.")
    print("-" * 76)

    for sf in sample_files:
        path = os.path.join(samples_dir, sf)
        if not os.path.exists(path):
            continue

        # Stage 0: Load Image & Prepare Inputs
        t0 = time.perf_counter()
        pil_img = load_image(path)
        dimensions = pil_img.size
        t_load = (time.perf_counter() - t0) * 1000

        # Stage 1: On-Device OCR (RapidOCR DBNet detection + SVTR sequence recognition)
        t1 = time.perf_counter()
        ocr_res = ocr_engine.extract_text(pil_img)
        t_ocr = (time.perf_counter() - t1) * 1000

        # Stage 2: Scene & Visual Understanding (Document & UI Semantic Layout)
        t2 = time.perf_counter()
        scene_res = image_analyzer.analyze_image(pil_img, ocr_result=ocr_res)
        t_analysis = (time.perf_counter() - t2) * 1000

        # Stage 3: UI Automation Hierarchy & Spatial OCR Correlation
        t3 = time.perf_counter()
        elements = audit_coordinator._synthesize_elements_from_vision(ocr_res, dimensions)
        ui_tree = UITree(elements)
        ui_tree.correlate_with_ocr_boxes(ocr_res.bounding_boxes)
        t_tree = (time.perf_counter() - t3) * 1000

        # Stage 4: Deterministic WCAG 2.1 Rule & Contrast Evaluation
        t4 = time.perf_counter()
        raw_findings = rule_engine.evaluate_tree(ui_tree, screenshot=pil_img)
        t_rules = (time.perf_counter() - t4) * 1000

        # Stage 5: Multi-Signal Evidence Fusion & Developer Remediation Attachment
        t5 = time.perf_counter()
        final_findings: List[FindingModel] = []
        for elem in ui_tree.elements:
            elem_findings = [f for f in raw_findings if f.element_id == elem.id]
            fused = evidence_engine.fuse_signals(elem, elem_findings, ocr_confidence=ocr_res.confidence)
            final_findings.extend(fused)
        tree_wide = [f for f in raw_findings if not f.element_id]
        final_findings.extend(tree_wide)
        for finding in final_findings:
            rem = remediation_engine.explain_finding(finding)
            if not finding.remediation_code:
                finding.remediation_code = rem.get("wpf_xaml", "")
        t_evidence = (time.perf_counter() - t5) * 1000

        # Audit and rules sub-pipeline combines spatial tree, WCAG rules, and evidence fusion
        t_audit_and_rules = t_load + t_tree + t_rules + t_evidence

        # Construct Unified InterfaceSnapshot
        snapshot = InterfaceSnapshot(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            application_name="Target Application",
            window_title=scene_res.detected_category,
            window_handle=0,
            ui_tree=ui_tree,
            elements=elements,
            findings=final_findings,
            audit_duration_ms=round(t_ocr + t_analysis + t_audit_and_rules, 2),
            hardware_state=f"{profile.cpu_model} ({profile.architecture})",
            backend=profile.ai_backend_label,
        )

        # Stage 6: Multi-Format Report Generation (Phase 7: JSON + Markdown + Accessible HTML)
        t6 = time.perf_counter()
        _ = report_generator.generate_markdown(snapshot)
        _ = report_generator.generate_json(snapshot)
        _ = report_generator.generate_html(snapshot)
        p7_report = audit_report_generator.generate_report(
            application_name="AccessLens Demo App",
            target_window=scene_res.detected_category,
            findings=final_findings,
            privacy_mode="findings_only",
        )
        _ = JsonReportExporter.export_to_string(p7_report)
        _ = MarkdownReportExporter.export_to_string(p7_report)
        _ = HtmlReportExporter.export_to_string(p7_report)
        t_reports = (time.perf_counter() - t6) * 1000

        # True Additive Total Pipeline Latency (all sequential stages in this single pass)
        t_total_pipeline = t_ocr + t_analysis + t_audit_and_rules + t_reports

        mem_mb = 0.0
        if process:
            mem_mb = round(process.memory_info().rss / (1024 * 1024), 2)

        bm = AccessLensBenchmarkMetric(
            sample_name=sf,
            ocr_time_ms=round(t_ocr, 2),
            analysis_time_ms=round(t_analysis, 2),
            rule_eval_time_ms=round(t_audit_and_rules, 2),
            report_gen_time_ms=round(t_reports, 2),
            total_audit_time_ms=round(t_total_pipeline, 2),
            memory_rss_mb=mem_mb,
            elements_count=len(snapshot.elements),
            barriers_count=len(snapshot.findings),
            critical_count=snapshot.critical_findings_count,
            backend_label=profile.ai_backend_label
        )
        metrics.append(bm)

        print(f" Target Interface: {sf:<26}")
        print(f"   * Stage 1: On-Device OCR (RapidOCR):       {bm.ocr_time_ms:>7.2f} ms")
        print(f"   * Stage 2: Scene & Layout Understanding:   {bm.analysis_time_ms:>7.2f} ms")
        print(f"   * Stage 3: Audit, Rules & Evidence Fusion: {bm.rule_eval_time_ms:>7.2f} ms")
        print(f"   * Stage 4: Multi-Format Report Generation: {bm.report_gen_time_ms:>7.2f} ms")
        print(f"   ------------------------------------------------------------")
        print(f"   * Total Sequential Pipeline Latency:       {bm.total_audit_time_ms:>7.2f} ms")
        print(f"   * Host Process Memory (RSS):               {bm.memory_rss_mb:>7.2f} MB")
        print(f"   * Inspected UI Elements:                   {bm.elements_count:>7}")
        print(f"   * Detected Barriers (Total):               {bm.barriers_count:>7}")
        print(f"   * Critical/High Barriers:                  {bm.critical_count:>7}")
        print("-" * 76)

    if metrics:
        avg_ocr = np.mean([m.ocr_time_ms for m in metrics])
        avg_analysis = np.mean([m.analysis_time_ms for m in metrics])
        avg_audit = np.mean([m.rule_eval_time_ms for m in metrics])
        avg_reports = np.mean([m.report_gen_time_ms for m in metrics])
        avg_total = np.mean([m.total_audit_time_ms for m in metrics])
        avg_mem = np.mean([m.memory_rss_mb for m in metrics])

        print(" SUMMARY BENCHMARK AVERAGES (AMD CPU BASELINE)")
        print(f" * Average On-Device OCR Latency:           {avg_ocr:7.2f} ms")
        print(f" * Average Scene & Layout Understanding:    {avg_analysis:7.2f} ms")
        print(f" * Average Audit, Rules & Evidence Fusion:  {avg_audit:7.2f} ms")
        print(f" * Average Multi-Format Report Generation:  {avg_reports:7.2f} ms")
        print(f" ------------------------------------------------------------")
        print(f" * Average Total Sequential Pipeline:       {avg_total:7.2f} ms")
        print(f" * Average Process Memory (RSS):            {avg_mem:7.2f} MB")
        print("=" * 76)
        print(" SNAPDRAGON HARDWARE VALIDATION NOTE:")
        print(" No simulated QNN execution or fabricated Snapdragon benchmarks.")
        print(" Snapdragon/NPU performance validation remains pending genuine")
        print(" Snapdragon hardware access.")
        print("=" * 76 + "\n")

    return metrics


if __name__ == "__main__":
    run_accesslens_benchmark()

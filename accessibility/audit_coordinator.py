"""Multimodal accessibility audit coordinator for AccessLens AI.

Orchestrates the entire evidence-first inspection pipeline:
Window/Capture -> UI Automation -> ONNX OCR -> Visual Analysis ->
Deterministic Rules -> Evidence Fusion -> Developer Remediation -> InterfaceSnapshot.
"""

from datetime import datetime
import time
from typing import Optional, Union
import numpy as np
from PIL import Image

from accessibility.element_model import (
    FindingModel, InterfaceSnapshot, SignalType, UIElementModel
)
from accessibility.evidence_engine import evidence_engine
from accessibility.remediation_engine import remediation_engine
from accessibility.rule_engine import rule_engine
from accessibility.ui_automation import ui_automation
from accessibility.ui_tree import UITree

from hardware.hardware_detector import hardware_detector
from vision.image_analyzer import image_analyzer
from vision.image_utils import load_image
from vision.ocr_engine import ocr_engine


class AuditCoordinator:
    """Coordinates multimodal inspection across UIA, OCR, Vision, and Rules."""

    def __init__(self):
        self._last_snapshot: Optional[InterfaceSnapshot] = None

    @property
    def last_snapshot(self) -> Optional[InterfaceSnapshot]:
        return self._last_snapshot

    def audit_interface(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        window_handle: Optional[int] = None,
        app_name_override: Optional[str] = None
    ) -> InterfaceSnapshot:
        """Executes full on-device accessibility audit pipeline."""
        start_time = time.perf_counter()
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Load Image
        pil_img = load_image(image_input)
        dimensions = pil_img.size
        screenshot_path = image_input if isinstance(image_input, str) else None

        # 2. Extract UI Automation Tree
        win_title, detected_app, elements = ui_automation.inspect_window(window_handle)
        app_name = app_name_override or detected_app or "Target Application"

        # If UIA returned 0 elements (e.g. static image loaded or headless environment),
        # synthesize UI elements from layout analyzer and OCR bounding boxes
        ocr_result = ocr_engine.extract_text(pil_img)
        scene_analysis = image_analyzer.analyze_image(pil_img, ocr_result=ocr_result)

        if not elements:
            elements = self._synthesize_elements_from_vision(ocr_result, dimensions)

        # 3. Build UI Tree & Correlate with OCR Text
        ui_tree = UITree(elements)
        ui_tree.correlate_with_ocr_boxes(ocr_result.bounding_boxes)

        # 4. Evaluate Deterministic Accessibility Rules
        raw_findings = rule_engine.evaluate_tree(ui_tree, screenshot=pil_img)

        # 5. Fuse Evidence & Calibrate Confidence
        final_findings: List[FindingModel] = []
        for elem in ui_tree.elements:
            elem_findings = [f for f in raw_findings if f.element_id == elem.id]
            fused = evidence_engine.fuse_signals(elem, elem_findings, ocr_confidence=ocr_result.confidence)
            final_findings.extend(fused)

        # Include tree-wide findings (like non-sequential focus order)
        tree_wide = [f for f in raw_findings if not f.element_id]
        final_findings.extend(tree_wide)

        # 6. Attach Remediation Guidance to All Findings
        for finding in final_findings:
            remediation_info = remediation_engine.explain_finding(finding)
            if not finding.remediation_code:
                finding.remediation_code = remediation_info.get("wpf_xaml", "")

        # 7. Hardware & Runtime Telemetry
        profile = hardware_detector.inspect()
        hw_summary = f"{profile.cpu_model} ({profile.architecture})"

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        snapshot = InterfaceSnapshot(
            timestamp=timestamp_str,
            application_name=app_name,
            window_title=win_title or scene_analysis.detected_category,
            window_handle=window_handle or 0,
            elements=ui_tree.elements,
            ocr_text=ocr_result.text,
            screenshot_path=screenshot_path,
            screen_dimensions=dimensions,
            findings=final_findings,
            backend_state=profile.ai_backend_label,
            hardware_summary=hw_summary,
            audit_duration_ms=round(elapsed_ms, 2),
            keyboard_order=[e.name or e.control_type for e in ui_tree.get_interactive_elements()]
        )

        self._last_snapshot = snapshot
        return snapshot

    def _synthesize_elements_from_vision(self, ocr_result, dimensions) -> list[UIElementModel]:
        """Synthesizes structural elements from OCR bounding boxes when UIA is unavailable."""
        elements = []
        for i, box_info in enumerate(ocr_result.bounding_boxes):
            box = box_info.get("box", [])
            text = box_info.get("text", "")
            if not box or len(box) != 4:
                continue

            if isinstance(box[0], (list, tuple)):
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x, y = int(min(xs)), int(min(ys))
                w, h = int(max(xs) - x), int(max(ys) - y)
            else:
                x, y, w, h = [int(v) for v in box]

            # Infer control type from text cues
            ctype = "Text"
            t_lower = text.lower()
            if any(w_btn in t_lower for w_btn in ["apply", "submit", "order", "login", "download", "save", "button", "next"]):
                ctype = "Button"
            elif any(w_inp in t_lower for w_inp in ["enter", "type", "search", "email", "password"]):
                ctype = "Edit"

            elem = UIElementModel(
                id=f"vis_elem_{i}",
                name=text if ctype != "Button" else "",  # Some buttons intentionally lack UIA names
                control_type=ctype,
                automation_id=f"auto_{i}",
                class_name="VisualInferredControl",
                bounds=[x, y, w, h],
                is_enabled=True,
                is_visible=True,
                is_focusable=ctype in ["Button", "Edit"],
                ocr_associated_text=text
            )
            elements.append(elem)

        return elements


# Singleton instance
audit_coordinator = AuditCoordinator()

"""Unified Screenshot + UI Automation + Visual Evidence Fusion for AccessLens AI (Phase 6).

Fuses:
1. Windows UI Automation (UIA) metadata
2. Target-window screenshot pixels
3. On-device OCR visual regions
4. Geometric spatial normalization
5. Keyboard focus observations (Phase 5)
6. Deterministic WCAG accessibility findings

Core Principle: UIA evidence and visual evidence remain strictly distinguishable.
Visual inference never overwrites measured UIA state.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import difflib
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from accessibility.element_model import UIElementModel
from accessibility.evidence_engine import EvidenceEngine, EvidenceItem, EvidenceSource
from accessibility.findings import SignalType
from accessibility.focus_models import FocusObservation
from accessibility.geometry import (
    calculate_center,
    calculate_containment,
    calculate_distance,
    calculate_iou,
    clip_rect,
    rect_area,
    rect_intersection,
    rect_intersection_area,
    uia_bounds_to_screenshot_bounds,
    validate_rect,
)
from accessibility.visual_models import VisualEvidence
from ai.prompt_guard import PromptGuard


# Configurable Deterministic Matching Thresholds
STRONG_MATCH_THRESHOLD = 0.85
LIKELY_MATCH_THRESHOLD = 0.65
POSSIBLE_MATCH_THRESHOLD = 0.45


@dataclass
class EvidenceMatch:
    """Association between a programmatic UIA element and an observed visual region."""
    match_id: str
    uia_element: UIElementModel
    visual_element: VisualEvidence
    match_score: float  # Deterministic score [0.0, 1.0]
    match_classification: str  # "Strong match", "Likely match", "Possible match", "Unmatched"
    geometry_score: float = 0.0
    text_score: float = 0.0
    control_type_score: float = 0.0
    proximity_score: float = 0.0
    focus_score: float = 0.0
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    discrepancy_detected: bool = False
    discrepancy_details: str = ""
    human_verification_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": self.match_id,
            "uia_element_id": self.uia_element.element_id,
            "uia_name": self.uia_element.name,
            "control_type": self.uia_element.control_type,
            "uia_bounds": self.uia_element.bounds,
            "visual_evidence_id": self.visual_element.evidence_id,
            "visual_text": self.visual_element.text,
            "visual_bounds": self.visual_element.bounds,
            "match_score": round(self.match_score, 3),
            "match_classification": self.match_classification,
            "subscores": {
                "geometry": round(self.geometry_score, 3),
                "text": round(self.text_score, 3),
                "control_type": round(self.control_type_score, 3),
                "proximity": round(self.proximity_score, 3),
                "focus": round(self.focus_score, 3),
            },
            "discrepancy_detected": self.discrepancy_detected,
            "discrepancy_details": self.discrepancy_details,
            "evidence_count": len(self.evidence_items),
            "human_verification_required": self.human_verification_required,
        }


@dataclass
class EvidenceFusionResult:
    """Unified multimodal evidence record combining UIA, visual OCR, and focus observations."""
    target_window: str
    screenshot_metadata: Dict[str, Any]
    uia_elements: List[UIElementModel]
    visual_elements: List[VisualEvidence]
    matched_elements: List[EvidenceMatch] = field(default_factory=list)
    unmatched_uia_elements: List[UIElementModel] = field(default_factory=list)
    unmatched_visual_elements: List[VisualEvidence] = field(default_factory=list)
    evidence_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    keyboard_observations: List[FocusObservation] = field(default_factory=list)
    focus_path_mappings: List[Dict[str, Any]] = field(default_factory=list)
    fused_evidence: List[EvidenceItem] = field(default_factory=list)
    confidence: float = 1.0
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    human_verification_required: bool = True
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

    @property
    def total_uia_count(self) -> int:
        return len(self.uia_elements)

    @property
    def total_visual_count(self) -> int:
        return len(self.visual_elements)

    @property
    def matched_count(self) -> int:
        return len(self.matched_elements)

    @property
    def unmatched_uia_count(self) -> int:
        return len(self.unmatched_uia_elements)

    @property
    def unmatched_visual_count(self) -> int:
        return len(self.unmatched_visual_elements)

    @property
    def conflicts_count(self) -> int:
        return len(self.evidence_conflicts)

    @property
    def focus_mapping_status(self) -> str:
        if not self.keyboard_observations:
            return "UNAVAILABLE"
        mapped_count = sum(1 for m in self.focus_path_mappings if m.get("visual_mapped"))
        if mapped_count == len(self.keyboard_observations):
            return "AVAILABLE"
        if mapped_count > 0:
            return "PARTIAL"
        return "UNAVAILABLE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_window": self.target_window,
            "timestamp": self.timestamp,
            "screenshot_metadata": self.screenshot_metadata,
            "metrics": {
                "total_uia_elements": self.total_uia_count,
                "total_visual_elements": self.total_visual_count,
                "matched_count": self.matched_count,
                "unmatched_uia_count": self.unmatched_uia_count,
                "unmatched_visual_count": self.unmatched_visual_count,
                "conflicts_count": self.conflicts_count,
                "focus_mapping_status": self.focus_mapping_status,
            },
            "matched_elements": [m.to_dict() for m in self.matched_elements],
            "unmatched_uia_ids": [e.element_id for e in self.unmatched_uia_elements],
            "unmatched_visual_ids": [v.evidence_id for v in self.unmatched_visual_elements],
            "evidence_conflicts": self.evidence_conflicts,
            "fused_evidence_count": len(self.fused_evidence),
            "warnings": self.warnings,
            "limitations": self.limitations,
            "human_verification_required": self.human_verification_required,
        }


class EvidenceFusionEngine:
    """Deterministic, inspectable engine that correlates UIA and visual evidence."""

    def __init__(
        self,
        strong_threshold: float = STRONG_MATCH_THRESHOLD,
        likely_threshold: float = LIKELY_MATCH_THRESHOLD,
        possible_threshold: float = POSSIBLE_MATCH_THRESHOLD,
    ):
        self.strong_threshold = strong_threshold
        self.likely_threshold = likely_threshold
        self.possible_threshold = possible_threshold

    def calculate_text_similarity(self, text1: Optional[str], text2: Optional[str]) -> float:
        """Computes deterministic text similarity [0.0, 1.0].
        
        Handles casing, token containment, and SequenceMatcher Levenshtein ratio.
        """
        if not text1 or not text2:
            return 0.0

        s1 = str(text1).strip().lower()
        s2 = str(text2).strip().lower()

        if not s1 or not s2:
            return 0.0

        # Exact match
        if s1 == s2:
            return 1.0

        # Substring containment
        if s1 in s2 or s2 in s1:
            ratio = min(len(s1), len(s2)) / max(len(s1), len(s2))
            return max(0.70, ratio)

        # Token set overlap
        t1 = set(s1.split())
        t2 = set(s2.split())
        if t1 and t2:
            overlap = len(t1.intersection(t2)) / float(len(t1.union(t2)))
            if overlap > 0.0:
                return max(0.50, overlap)

        # Normalized Levenshtein ratio
        return difflib.SequenceMatcher(None, s1, s2).ratio()

    def calculate_control_type_compatibility(
        self, control_type: Optional[str], has_text: bool
    ) -> float:
        """Determines if the UIA control type is expected to display visible text."""
        if not control_type:
            return 0.50

        ctype = control_type.strip().lower()
        text_bearing_types = {
            "button", "hyperlink", "text", "textblock", "edit", "headeritem",
            "menuitem", "tabitem", "checkbox", "radiobutton", "listitem"
        }
        container_types = {"window", "pane", "group", "custom", "scrollbar", "separator"}

        if ctype in text_bearing_types:
            return 1.0 if has_text else 0.40
        if ctype in container_types:
            return 0.40
        return 0.60

    @staticmethod
    def calculate_deterministic_score(
        geometry_score: float,
        text_score: float,
        control_type_score: float,
        proximity_score: float,
        has_focus_evidence: bool = False,
    ) -> float:
        """Computes deterministic match score strictly bounded in [0.0, 1.0]."""
        base_score = (
            0.40 * geometry_score
            + 0.30 * text_score
            + 0.15 * control_type_score
            + 0.15 * proximity_score
        )
        if has_focus_evidence:
            score = min(1.0, base_score + 0.20)
        else:
            score = base_score
        return max(0.0, min(1.0, score))

    def compute_match_score(
        self,
        uia_element: UIElementModel,
        visual_element: VisualEvidence,
        window_bounds: Optional[List[int]],
        screenshot_size: Tuple[int, int],
        keyboard_observations: Optional[List[FocusObservation]] = None,
    ) -> Tuple[float, Dict[str, float]]:
        """Calculates deterministic matching score and subscores between UIA and Visual evidence.
        
        Formula:
          score = 0.40 * geometry + 0.30 * text + 0.15 * control_type + 0.15 * proximity (+ focus_boost)
        """
        # 1. Transform UIA bounds to screenshot coordinate space
        mapped_uia_bounds = uia_bounds_to_screenshot_bounds(
            uia_element.bounds, window_bounds, screenshot_size
        )
        vis_bounds = validate_rect(visual_element.bounds)

        # Geometry score: IoU + Containment
        geometry_score = 0.0
        if mapped_uia_bounds and vis_bounds:
            iou = calculate_iou(mapped_uia_bounds, vis_bounds)
            containment = max(
                calculate_containment(vis_bounds, mapped_uia_bounds),
                calculate_containment(mapped_uia_bounds, vis_bounds),
            )
            geometry_score = 0.6 * iou + 0.4 * containment
        elif not mapped_uia_bounds and not vis_bounds:
            geometry_score = 0.0

        # Text similarity score
        text_score = self.calculate_text_similarity(
            uia_element.name or uia_element.value, visual_element.text
        )

        # Control type compatibility score
        control_type_score = self.calculate_control_type_compatibility(
            uia_element.control_type, bool(visual_element.text)
        )

        # Spatial proximity score
        proximity_score = 0.0
        if mapped_uia_bounds and vis_bounds:
            c1 = calculate_center(mapped_uia_bounds)
            c2 = calculate_center(vis_bounds)
            if c1 and c2:
                dist = calculate_distance(c1, c2)
                diag = math.hypot(screenshot_size[0], screenshot_size[1])
                norm_dist = dist / max(1.0, diag)
                proximity_score = max(0.0, 1.0 - norm_dist * 3.0)

        # Keyboard focus boost
        focus_score = 0.0
        if keyboard_observations:
            for obs in keyboard_observations:
                if obs.element_id and obs.element_id == uia_element.element_id:
                    focus_score = 0.20
                    break

        score = self.calculate_deterministic_score(
            geometry_score=geometry_score,
            text_score=text_score,
            control_type_score=control_type_score,
            proximity_score=proximity_score,
            has_focus_evidence=bool(focus_score > 0.0),
        )

        subscores = {
            "geometry": geometry_score,
            "text": text_score,
            "control_type": control_type_score,
            "proximity": proximity_score,
            "focus": focus_score,
        }
        return score, subscores

    def classify_score(self, score: float) -> str:
        """Assigns human-readable classification to deterministic match score."""
        if score >= self.strong_threshold:
            return "Strong match"
        if score >= self.likely_threshold:
            return "Likely match"
        if score >= self.possible_threshold:
            return "Possible match"
        return "Unmatched"

    def fuse_evidence(
        self,
        target_window_title: str,
        uia_elements: List[UIElementModel],
        visual_elements: List[VisualEvidence],
        screenshot_size: Tuple[int, int] = (1280, 720),
        window_bounds: Optional[List[int]] = None,
        keyboard_observations: Optional[List[FocusObservation]] = None,
        screenshot_metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceFusionResult:
        """Executes full evidence fusion between UIA elements and Visual observations."""
        warnings: List[str] = []
        limitations: List[str] = [
            "Visual evidence is an investigative aid and does not override measured UI Automation state.",
            "Automated evidence fusion assists accessibility QA and requires human review."
        ]

        meta = screenshot_metadata or {
            "width": screenshot_size[0],
            "height": screenshot_size[1],
            "window_bounds": window_bounds,
            "status": "Available",
        }

        matched_elements: List[EvidenceMatch] = []
        unmatched_uia: List[UIElementModel] = []
        unmatched_visual: List[VisualEvidence] = list(visual_elements)
        conflicts: List[Dict[str, Any]] = []
        fused_evidence_items: List[EvidenceItem] = []

        # Bipartite matching: For each UIA element, find the best visual match
        used_visual_ids = set()

        for idx, uia_el in enumerate(uia_elements):
            best_match: Optional[VisualEvidence] = None
            best_score = 0.0
            best_subscores: Dict[str, float] = {}

            for vis_el in visual_elements:
                if vis_el.evidence_id in used_visual_ids:
                    continue

                score, subscores = self.compute_match_score(
                    uia_element=uia_el,
                    visual_element=vis_el,
                    window_bounds=window_bounds,
                    screenshot_size=screenshot_size,
                    keyboard_observations=keyboard_observations,
                )
                if score > best_score:
                    best_score = score
                    best_match = vis_el
                    best_subscores = subscores

            if best_match is not None and best_score >= self.possible_threshold:
                used_visual_ids.add(best_match.evidence_id)
                classification = self.classify_score(best_score)

                # Check for prompt injection in visual text
                is_suspicious = best_match.is_suspicious or PromptGuard.is_suspicious_text(best_match.text)
                if is_suspicious:
                    best_match.is_suspicious = True
                    limitations.append(
                        f"Visual evidence '{best_match.evidence_id}' contains suspicious instruction-like patterns; "
                        "isolated as passive data."
                    )

                # Check for visible label vs accessible name discrepancy
                discrepancy = False
                discrepancy_msg = ""
                uia_name = (uia_el.name or "").strip()
                vis_text = (best_match.text or "").strip()

                if uia_name and vis_text:
                    if uia_name.lower() != vis_text.lower():
                        # Substantial mismatch
                        discrepancy = True
                        discrepancy_msg = (
                            f"Potential label-in-name discrepancy — WCAG reference 2.5.3. Human verification required: Accessible Name '{uia_name}' does not match visible OCR text '{vis_text}'."
                        )

                # Build grounded evidence items
                match_evidence: List[EvidenceItem] = [
                    EvidenceEngine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=f"[UIA_MEASURED] Accessible Name: {uia_name or '<None>'}",
                        value=uia_name,
                        element_id=uia_el.element_id,
                        location=uia_el.bounds,
                    ),
                    EvidenceEngine.create_item(
                        source=EvidenceSource.OCR,
                        evidence_type=SignalType.DETECTED,
                        description=f"[OCR_DETECTED] Visible text: {vis_text or '<None>'}",
                        value=vis_text,
                        element_id=best_match.evidence_id,
                        location=best_match.bounds,
                    ),
                ]

                if best_subscores.get("geometry", 0.0) >= 0.50:
                    match_evidence.append(
                        EvidenceEngine.create_item(
                            source=EvidenceSource.SCREENSHOT,
                            evidence_type=SignalType.MEASURED,
                            description="[SCREENSHOT_MEASURED] OCR region overlaps UIA element bounds",
                            value=best_subscores.get("geometry"),
                            element_id=uia_el.element_id,
                            location=best_match.bounds,
                        )
                    )

                if discrepancy:
                    match_evidence.append(
                        EvidenceEngine.create_item(
                            source=EvidenceSource.VISUAL_ANALYSIS,
                            evidence_type=SignalType.INFERRED,
                            description=f"[FUSED] {discrepancy_msg}",
                            element_id=uia_el.element_id,
                        )
                    )
                    conflicts.append({
                        "conflict_type": "LABEL_NAME_MISMATCH",
                        "description": f"Potential label-in-name discrepancy — WCAG reference 2.5.3. Human verification required: Accessible Name '{uia_name}' does not match visible OCR text '{vis_text}'.",
                        "uia_id": uia_el.element_id,
                        "uia_name": uia_name,
                        "visual_text": vis_text,
                        "match_score": best_score,
                        "details": discrepancy_msg,
                        "source_1": "UIA_MEASURED",
                        "source_2": "OCR_DETECTED",
                    })
                else:
                    match_evidence.append(
                        EvidenceEngine.create_item(
                            source=EvidenceSource.VISUAL_ANALYSIS,
                            evidence_type=SignalType.DETECTED,
                            description="[FUSED] UIA accessible name and visible OCR text agree",
                            element_id=uia_el.element_id,
                        )
                    )

                match_record = EvidenceMatch(
                    match_id=f"match_{idx}_{best_match.evidence_id}",
                    uia_element=uia_el,
                    visual_element=best_match,
                    match_score=best_score,
                    match_classification=classification,
                    geometry_score=best_subscores.get("geometry", 0.0),
                    text_score=best_subscores.get("text", 0.0),
                    control_type_score=best_subscores.get("control_type", 0.0),
                    proximity_score=best_subscores.get("proximity", 0.0),
                    focus_score=best_subscores.get("focus", 0.0),
                    evidence_items=match_evidence,
                    discrepancy_detected=discrepancy,
                    discrepancy_details=discrepancy_msg,
                    human_verification_required=True,
                )
                matched_elements.append(match_record)
                fused_evidence_items.extend(match_evidence)
            else:
                unmatched_uia.append(uia_el)
                fused_evidence_items.append(
                    EvidenceEngine.create_item(
                        source=EvidenceSource.UI_AUTOMATION,
                        evidence_type=SignalType.DETECTED,
                        description=(
                            f"[UIA_MEASURED] UIA element '{uia_el.name or uia_el.control_type}' exists "
                            "but no reliable screenshot mapping was established."
                        ),
                        element_id=uia_el.element_id,
                        location=uia_el.bounds,
                    )
                )

        # Identify unmatched visual elements
        unmatched_visual = [
            v for v in visual_elements if v.evidence_id not in used_visual_ids
        ]
        for v in unmatched_visual:
            fused_evidence_items.append(
                EvidenceEngine.create_item(
                    source=EvidenceSource.OCR,
                    evidence_type=SignalType.DETECTED,
                    description=(
                        f"[OCR_DETECTED] Visible text/region '{v.text}' was detected "
                        "but no corresponding UIA element was identified."
                    ),
                    element_id=v.evidence_id,
                    location=v.bounds,
                )
            )

        # Focus path visual mapping
        focus_mappings: List[Dict[str, Any]] = []
        if keyboard_observations:
            focus_mappings = self.map_focus_path_to_visuals(
                observations=keyboard_observations,
                window_bounds=window_bounds,
                screenshot_size=screenshot_size,
            )

        return EvidenceFusionResult(
            target_window=target_window_title,
            screenshot_metadata=meta,
            uia_elements=uia_elements,
            visual_elements=visual_elements,
            matched_elements=matched_elements,
            unmatched_uia_elements=unmatched_uia,
            unmatched_visual_elements=unmatched_visual,
            evidence_conflicts=conflicts,
            keyboard_observations=keyboard_observations or [],
            focus_path_mappings=focus_mappings,
            fused_evidence=fused_evidence_items,
            confidence=1.0 if not conflicts else 0.85,
            warnings=warnings,
            limitations=limitations,
            human_verification_required=True,
        )

    @staticmethod
    def map_focus_path_to_visuals(
        observations: List[FocusObservation],
        window_bounds: Optional[List[int]],
        screenshot_size: Tuple[int, int],
    ) -> List[Dict[str, Any]]:
        """Maps a sequence of keyboard focus observations to screenshot pixel coordinates."""
        mappings: List[Dict[str, Any]] = []
        for obs in observations:
            mapped_box = uia_bounds_to_screenshot_bounds(
                obs.bounds, window_bounds, screenshot_size
            )
            if mapped_box:
                mappings.append({
                    "observation_id": obs.observation_id,
                    "element_name": obs.element_name,
                    "visual_mapped": True,
                    "visual_bounds": mapped_box,
                    "center": calculate_center(mapped_box),
                    "mapping_note": "Visual mapping established.",
                })
            else:
                mappings.append({
                    "observation_id": obs.observation_id,
                    "element_name": obs.element_name,
                    "visual_mapped": False,
                    "visual_bounds": None,
                    "center": None,
                    "mapping_note": "Focus target observed through UIA but visual mapping unavailable; traversal data remains available.",
                })
        return mappings

    @staticmethod
    def compare_focus_regions(
        before_image: Optional[Image.Image],
        after_image: Optional[Image.Image],
        region: Optional[List[int]],
        difference_threshold: float = 0.05,
    ) -> Dict[str, Any]:
        """Compares pixel differences in the focused region between before and after states.
        
        Guarantees that pixel change is reported as 'OBSERVED PIXEL DIFFERENCE', never claiming
        that a focus indicator definitely exists.
        """
        if before_image is None or after_image is None or not region or len(region) < 4:
            return {
                "status": "UNAVAILABLE",
                "message": "Before/after screenshots or valid bounding region unavailable.",
                "difference_ratio": 0.0,
                "human_verification_required": True,
            }

        v_box = validate_rect(region)
        if not v_box or v_box[2] <= 0 or v_box[3] <= 0:
            return {
                "status": "UNAVAILABLE",
                "message": "Invalid bounding region.",
                "difference_ratio": 0.0,
                "human_verification_required": True,
            }

        try:
            x, y, w, h = v_box
            crop_box = (x, y, x + w, y + h)

            c1 = before_image.crop(crop_box).convert("L")
            c2 = after_image.crop(crop_box).convert("L")

            # Compute absolute pixel difference
            import numpy as np
            arr1 = np.array(c1, dtype=np.int16)
            arr2 = np.array(c2, dtype=np.int16)

            diff = np.abs(arr1 - arr2)
            changed_pixels = np.sum(diff > 15)  # Slight noise threshold
            total_pixels = max(1, arr1.size)
            ratio = float(changed_pixels) / float(total_pixels)

            if ratio >= difference_threshold:
                return {
                    "status": "OBSERVED PIXEL DIFFERENCE",
                    "difference_ratio": round(ratio, 4),
                    "message": f"Pixel differences were detected in the focused element region ({ratio * 100:.1f}% changed pixels).",
                    "human_verification_required": True,
                }
            else:
                return {
                    "status": "NO RELIABLE VISUAL FOCUS CHANGE DETECTED",
                    "difference_ratio": round(ratio, 4),
                    "message": "No significant pixel difference was detected in the focused element region.",
                    "human_verification_required": True,
                }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Pixel difference comparison encountered an exception: {e}",
                "difference_ratio": 0.0,
                "human_verification_required": True,
            }


# Singleton instance
evidence_fusion_engine = EvidenceFusionEngine()

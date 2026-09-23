"""Visual Evidence Model for AccessLens AI (Phase 6).

Represents visual entities detected from screenshots, on-device OCR, and rendered pixel analysis.
Preserves forensic integrity: visual evidence remains distinct from programmatic UIA metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class VisualEvidence:
    """Normalized visual observation extracted from interface screenshots or OCR."""
    evidence_id: str
    source: str = "RapidOCR"  # e.g., "RapidOCR", "Screenshot Analysis", "Pixel Differencing"
    text: str = ""
    confidence: float = 1.0
    bounds: Optional[List[int]] = None  # Normalized [x, y, w, h] in screenshot pixel space
    center: Optional[Tuple[int, int]] = None
    screenshot_reference: Optional[str] = None  # Path, hash, or identifier of source screenshot
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    notes: str = ""
    is_suspicious: bool = False  # Set to True if text contains adversarial or instruction-like patterns
    human_verification_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Auto-compute center if bounds are provided and center is missing
        if self.bounds and len(self.bounds) >= 4 and self.center is None:
            x, y, w, h = self.bounds[0], self.bounds[1], self.bounds[2], self.bounds[3]
            if w > 0 and h > 0:
                self.center = (int(x + w / 2), int(y + h / 2))

    def to_dict(self) -> Dict[str, Any]:
        """Serializes visual evidence to standard dictionary format."""
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "text": self.text,
            "confidence": round(self.confidence, 3),
            "bounds": list(self.bounds) if self.bounds else None,
            "center": list(self.center) if self.center else None,
            "screenshot_reference": self.screenshot_reference,
            "timestamp": self.timestamp,
            "notes": self.notes,
            "is_suspicious": self.is_suspicious,
            "human_verification_required": self.human_verification_required,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_ocr_box(
        cls,
        evidence_id: str,
        box_data: Dict[str, Any],
        screenshot_ref: Optional[str] = None,
        is_suspicious: bool = False
    ) -> "VisualEvidence":
        """Factory method to construct VisualEvidence from an OCR bounding box dictionary."""
        text = str(box_data.get("text", "")).strip()
        conf = float(box_data.get("confidence", 0.8))
        raw_box = box_data.get("box", [])

        bounds = None
        center = None
        if raw_box and len(raw_box) == 4:
            # Format: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            try:
                xs = [p[0] for p in raw_box]
                ys = [p[1] for p in raw_box]
                min_x, max_x = int(min(xs)), int(max(xs))
                min_y, max_y = int(min(ys)), int(max(ys))
                w = max(1, max_x - min_x)
                h = max(1, max_y - min_y)
                bounds = [min_x, min_y, w, h]
                center = (int(min_x + w / 2), int(min_y + h / 2))
            except Exception:
                bounds = None

        return cls(
            evidence_id=evidence_id,
            source="RapidOCR",
            text=text,
            confidence=conf,
            bounds=bounds,
            center=center,
            screenshot_reference=screenshot_ref,
            is_suspicious=is_suspicious,
            human_verification_required=True,
        )

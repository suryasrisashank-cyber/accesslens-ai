"""Deterministic WCAG 2.1 color contrast calculation engine.

Computes exact relative luminance and contrast ratios based on color inputs or
regional image sampling, labeling visual samples honestly as:
"Estimated from rendered pixels"
Never claims exact semantic CSS/UI color values unless actually obtained.
"""

from dataclasses import dataclass
import math
from typing import List, Optional, Tuple, Union
import numpy as np
from PIL import Image

from accessibility.findings import AccessibilityFinding, FindingCategory, SignalType
from accessibility.severity import FindingSeverity


@dataclass
class ContrastResult:
    """WCAG 2.1 contrast evaluation result."""
    contrast_ratio: float
    fg_rgb: Tuple[int, int, int]
    bg_rgb: Tuple[int, int, int]
    fg_hex: str
    bg_hex: str
    passes_aa_normal: bool  # >= 4.5:1
    passes_aa_large: bool   # >= 3.0:1
    passes_aaa_normal: bool # >= 7.0:1
    is_estimated: bool = True
    method: str = "Estimated from rendered pixels"
    limitations: str = (
        "Rendered pixels may be influenced by antialiasing, font smoothing, "
        "subpixel rendering, or gradients; visual verification is recommended."
    )

    @property
    def summary_label(self) -> str:
        status = "Pass (WCAG AA)" if self.passes_aa_normal else "Potential Contrast Issue"
        return f"{self.contrast_ratio:.2f}:1 [{status}]"


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Formats RGB tuple as uppercase hex string #RRGGBB."""
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculates WCAG 2.1 relative luminance from sRGB tuple (0-255)."""
    srgb = [c / 255.0 for c in rgb]
    linear = [
        c / 12.92 if c <= 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)
        for c in srgb
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def calculate_contrast_ratio(
    fg_rgb: Tuple[int, int, int],
    bg_rgb: Tuple[int, int, int],
    is_estimated: bool = False
) -> ContrastResult:
    """Computes WCAG 2.1 contrast ratio between two RGB colors."""
    l1 = relative_luminance(fg_rgb)
    l2 = relative_luminance(bg_rgb)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    ratio = (lighter + 0.05) / (darker + 0.05)
    ratio = round(ratio, 2)

    method = "Estimated from rendered pixels" if is_estimated else "Measured exact color calculation"

    return ContrastResult(
        contrast_ratio=ratio,
        fg_rgb=fg_rgb,
        bg_rgb=bg_rgb,
        fg_hex=rgb_to_hex(fg_rgb),
        bg_hex=rgb_to_hex(bg_rgb),
        passes_aa_normal=ratio >= 4.5,
        passes_aa_large=ratio >= 3.0,
        passes_aaa_normal=ratio >= 7.0,
        is_estimated=is_estimated,
        method=method
    )


def sample_region_contrast(image: Image.Image, bounds: List[int]) -> Optional[ContrastResult]:
    """Estimates foreground and background colors from an image crop region.

    Clearly labeled as 'Estimated from rendered pixels'.
    """
    try:
        x, y, w, h = bounds
        if w < 4 or h < 4 or x < 0 or y < 0:
            return None

        # Clamp to image dimensions
        img_w, img_h = image.size
        x1 = max(0, min(img_w - 1, x))
        y1 = max(0, min(img_h - 1, y))
        x2 = max(x1 + 1, min(img_w, x + w))
        y2 = max(y1 + 1, min(img_h, y + h))

        crop = image.crop((x1, y1, x2, y2)).convert("RGB")
        arr = np.array(crop)

        # Background estimate: perimeter pixels (top/bottom/left/right border)
        border_pixels = np.concatenate([
            arr[0, :, :],       # top row
            arr[-1, :, :],      # bottom row
            arr[:, 0, :],       # left col
            arr[:, -1, :],      # right col
        ], axis=0)

        bg_mean = np.mean(border_pixels, axis=0).astype(int)
        bg_rgb = (int(bg_mean[0]), int(bg_mean[1]), int(bg_mean[2]))

        # Foreground estimate: pixels with highest color distance from background
        flat = arr.reshape(-1, 3)
        diffs = np.linalg.norm(flat - bg_mean, axis=1)
        top_indices = np.argsort(diffs)[-max(1, len(diffs) // 8):]
        fg_mean = np.mean(flat[top_indices], axis=0).astype(int)
        fg_rgb = (int(fg_mean[0]), int(fg_mean[1]), int(fg_mean[2]))

        return calculate_contrast_ratio(fg_rgb, bg_rgb, is_estimated=True)
    except Exception:
        return None

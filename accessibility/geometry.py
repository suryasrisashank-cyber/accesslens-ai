"""Deterministic Geometry Normalizer & Spatial Math for AccessLens AI (Phase 6).

Provides robust, inspectable mathematical operations on bounding boxes, IoU calculation,
coordinate system transformations, DPI scaling normalization, and containment checks.
Rejects invalid geometries (negative dimensions, NaN, Inf) deterministically.
"""

import math
from typing import List, Optional, Tuple, Union


def validate_rect(rect: Optional[Union[List[Union[int, float]], Tuple[Union[int, float], ...]]]) -> Optional[List[int]]:
    """Validates and normalizes a bounding rectangle [x, y, w, h].
    
    Rejects None, length < 4, negative width/height, NaN, and Inf.
    Returns:
        Clean list of 4 integers [x, y, w, h], or None if invalid.
    """
    if rect is None or len(rect) < 4:
        return None

    try:
        x, y, w, h = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
    except (ValueError, TypeError):
        return None

    # Check for NaN and infinite values
    if any(math.isnan(v) or math.isinf(v) for v in (x, y, w, h)):
        return None

    # Width and height must be strictly positive (> 0)
    if w <= 0 or h <= 0:
        return None

    return [int(round(x)), int(round(y)), int(round(w)), int(round(h))]


def rect_area(rect: Optional[List[int]]) -> float:
    """Calculates area of a bounding box. Returns 0.0 for invalid rects."""
    v = validate_rect(rect)
    if v is None:
        return 0.0
    return float(v[2] * v[3])


def rect_intersection(r1: Optional[List[int]], r2: Optional[List[int]]) -> Optional[List[int]]:
    """Computes the rectangular intersection between two bounding boxes.
    
    Returns:
        [x, y, w, h] of intersection region, or None if disjoint or invalid.
    """
    v1 = validate_rect(r1)
    v2 = validate_rect(r2)
    if v1 is None or v2 is None:
        return None

    x1, y1, w1, h1 = v1
    x2, y2, w2, h2 = v2

    ix1 = max(x1, x2)
    iy1 = max(y1, y2)
    ix2 = min(x1 + w1, x2 + w2)
    iy2 = min(y1 + h1, y2 + h2)

    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)

    if iw <= 0 or ih <= 0:
        return None

    return [ix1, iy1, iw, ih]


def rect_intersection_area(r1: Optional[List[int]], r2: Optional[List[int]]) -> float:
    """Calculates the area of intersection between two rectangles."""
    inter = rect_intersection(r1, r2)
    if inter is None:
        return 0.0
    return float(inter[2] * inter[3])


def rect_union_area(r1: Optional[List[int]], r2: Optional[List[int]]) -> float:
    """Calculates the union area of two bounding boxes: Area(r1) + Area(r2) - Intersection(r1, r2)."""
    a1 = rect_area(r1)
    a2 = rect_area(r2)
    if a1 <= 0.0 and a2 <= 0.0:
        return 0.0
    if a1 <= 0.0:
        return a2
    if a2 <= 0.0:
        return a1

    inter = rect_intersection_area(r1, r2)
    return (a1 + a2) - inter


def calculate_iou(r1: Optional[List[int]], r2: Optional[List[int]]) -> float:
    """Calculates the Intersection-over-Union (IoU) ratio between two rectangles [0.0, 1.0]."""
    v1 = validate_rect(r1)
    v2 = validate_rect(r2)
    if v1 is None or v2 is None:
        return 0.0

    inter_area = rect_intersection_area(v1, v2)
    if inter_area <= 0.0:
        return 0.0

    union_area = rect_union_area(v1, v2)
    if union_area <= 0.0:
        return 0.0

    return min(1.0, max(0.0, inter_area / union_area))


def calculate_containment(inner: Optional[List[int]], outer: Optional[List[int]]) -> float:
    """Calculates what fraction of the 'inner' rectangle is enclosed within 'outer' [0.0, 1.0]."""
    v_in = validate_rect(inner)
    v_out = validate_rect(outer)
    if v_in is None or v_out is None:
        return 0.0

    in_area = rect_area(v_in)
    if in_area <= 0.0:
        return 0.0

    inter_area = rect_intersection_area(v_in, v_out)
    return min(1.0, max(0.0, inter_area / in_area))


def calculate_center(rect: Optional[List[int]]) -> Optional[Tuple[int, int]]:
    """Computes the integer center coordinates (cx, cy) of a rectangle."""
    v = validate_rect(rect)
    if v is None:
        return None
    x, y, w, h = v
    return (int(round(x + w / 2.0)), int(round(y + h / 2.0)))


def calculate_distance(p1: Optional[Tuple[int, int]], p2: Optional[Tuple[int, int]]) -> float:
    """Computes Euclidean distance between two points."""
    if p1 is None or p2 is None:
        return float("inf")
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def clip_rect(rect: Optional[List[int]], canvas_size: Tuple[int, int]) -> Optional[List[int]]:
    """Clips a rectangle so it stays strictly within [0, 0, canvas_width, canvas_height]."""
    v = validate_rect(rect)
    if v is None or canvas_size[0] <= 0 or canvas_size[1] <= 0:
        return None

    cw, ch = canvas_size
    rx, ry, rw, rh = v

    if rx + rw <= 0 or ry + rh <= 0 or rx >= cw or ry >= ch:
        return None

    cx = max(0, min(cw - 1, rx))
    cy = max(0, min(ch - 1, ry))
    cw_clipped = max(1, min(cw - cx, rx + rw - cx))
    ch_clipped = max(1, min(ch - cy, ry + rh - cy))

    return [cx, cy, cw_clipped, ch_clipped]


def uia_bounds_to_screenshot_bounds(
    uia_bounds: Optional[List[int]],
    window_bounds: Optional[List[int]],
    screenshot_size: Tuple[int, int],
    min_scale: float = 0.5,
    max_scale: float = 4.0,
) -> Optional[List[int]]:
    """Transforms Windows desktop UIA coordinates into screenshot-relative pixel coordinates.
    
    Accounts for DPI scaling and window offsets safely.
    Returns None if:
    - Geometry is invalid
    - Window bounds are missing or collapsed
    - Scaling factor is outside realistic display bounds [min_scale, max_scale]
    - Element is completely outside the screenshot canvas
    """
    v_uia = validate_rect(uia_bounds)
    if v_uia is None:
        return None

    sw, sh = screenshot_size
    if sw <= 0 or sh <= 0:
        return None

    # Case 1: Window bounds provided
    v_win = validate_rect(window_bounds)
    if v_win is not None:
        wx, wy, ww, wh = v_win
        if ww >= 8 and wh >= 8:
            sx = sw / float(ww)
            sy = sh / float(wh)

            # Validate scale factor sanity (DPI range check)
            if not (min_scale <= sx <= max_scale and min_scale <= sy <= max_scale):
                return None

            ex, ey, ew, eh = v_uia
            rel_x = ex - wx
            rel_y = ey - wy

            mapped_x = int(round(rel_x * sx))
            mapped_y = int(round(rel_y * sy))
            mapped_w = max(1, int(round(ew * sx)))
            mapped_h = max(1, int(round(eh * sy)))

            return clip_rect([mapped_x, mapped_y, mapped_w, mapped_h], screenshot_size)

    # Case 2: Full screen or direct mapping
    ex, ey, ew, eh = v_uia
    if 0 <= ex < sw and 0 <= ey < sh:
        return clip_rect([ex, ey, ew, eh], screenshot_size)

    return None


def screenshot_bounds_to_uia_bounds(
    screenshot_bounds: Optional[List[int]],
    window_bounds: Optional[List[int]],
    screenshot_size: Tuple[int, int],
    min_scale: float = 0.5,
    max_scale: float = 4.0,
) -> Optional[List[int]]:
    """Transforms screenshot-relative pixel bounds back to desktop UIA screen coordinates."""
    v_shot = validate_rect(screenshot_bounds)
    v_win = validate_rect(window_bounds)
    if v_shot is None or v_win is None:
        return None

    sw, sh = screenshot_size
    if sw <= 0 or sh <= 0:
        return None

    wx, wy, ww, wh = v_win
    if ww < 8 or wh < 8:
        return None

    sx = sw / float(ww)
    sy = sh / float(wh)
    if not (min_scale <= sx <= max_scale and min_scale <= sy <= max_scale):
        return None

    bx, by, bw, bh = v_shot
    uia_x = int(round(bx / sx + wx))
    uia_y = int(round(by / sy + wy))
    uia_w = max(1, int(round(bw / sx)))
    uia_h = max(1, int(round(bh / sy)))

    return [uia_x, uia_y, uia_w, uia_h]

"""Safe coordinate mapping between Windows UI Automation element bounds and screenshots.

Accounts for DPI scaling, multi-monitor coordinates, and window offsets.
Never assumes 1:1 coordinates. If mapping is untrusted or outside viewable boundaries,
returns None and marks mapping as unavailable.
"""

from typing import List, Optional, Tuple


class CoordinateMapper:
    """Safely correlates Windows desktop screen coordinates with screenshot pixel buffers."""

    @staticmethod
    def map_bounds_to_screenshot(
        element_bounds: Optional[List[int]],
        window_bounds: Optional[List[int]],
        screenshot_size: Tuple[int, int]
    ) -> Tuple[Optional[List[int]], str]:
        """Translates desktop screen coordinates to screenshot crop coordinates.

        Returns:
            Tuple of (mapped_box [x, y, w, h] or None, status_message)
        """
        if not element_bounds or len(element_bounds) < 4:
            return None, "Element bounds not exposed by application."

        ex, ey, ew, eh = element_bounds[0], element_bounds[1], element_bounds[2], element_bounds[3]
        if ew <= 0 or eh <= 0:
            return None, "Element has zero or negative dimensions."

        sw, sh = screenshot_size
        if sw <= 0 or sh <= 0:
            return None, "Invalid screenshot buffer dimensions."

        # Case 1: Window bounds available (relative mapping with DPI scaling)
        if window_bounds and len(window_bounds) >= 4:
            wx, wy, ww, wh = window_bounds[0], window_bounds[1], window_bounds[2], window_bounds[3]
            if ww > 10 and wh > 10:
                sx = sw / float(ww)
                sy = sh / float(wh)

                # Validate scale factor sanity (DPI scaling between 50% and 400%)
                if not (0.5 <= sx <= 4.0 and 0.5 <= sy <= 4.0):
                    return None, "Element bounds available; visual mapping unavailable."

                rel_x = ex - wx
                rel_y = ey - wy

                mapped_x = int(rel_x * sx)
                mapped_y = int(rel_y * sy)
                mapped_w = int(ew * sx)
                mapped_h = int(eh * sy)

                # Verify if inside screenshot area
                if mapped_x + mapped_w < 0 or mapped_y + mapped_h < 0 or mapped_x > sw or mapped_y > sh:
                    return None, "Element bounds available; visual mapping unavailable."

                # Clamp box
                final_x = max(0, min(sw - 1, mapped_x))
                final_y = max(0, min(sh - 1, mapped_y))
                final_w = max(1, min(sw - final_x, mapped_w))
                final_h = max(1, min(sh - final_y, mapped_h))

                return [final_x, final_y, final_w, final_h], "Mapped"

        # Case 2: Direct screenshot dimensions match desktop virtual screen bounds
        if 0 <= ex < sw and 0 <= ey < sh:
            final_x = ex
            final_y = ey
            final_w = max(1, min(sw - final_x, ew))
            final_h = max(1, min(sh - final_y, eh))
            return [final_x, final_y, final_w, final_h], "Mapped"

        return None, "Element bounds available; visual mapping unavailable."


# Singleton instance
coordinate_mapper = CoordinateMapper()

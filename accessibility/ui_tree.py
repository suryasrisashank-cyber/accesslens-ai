"""UI Tree manager for element hierarchies and spatial indexing.

Independent of PySide6 UI. Manages tree traversal, parent/child relationships,
element lookup, and focused element detection.
"""

from typing import Dict, Iterator, List, Optional, Tuple
from accessibility.element_model import UIElementModel


class UITree:
    """Manages the hierarchical structure, traversal, and lookup for UI elements."""

    def __init__(
        self,
        elements: Optional[List[UIElementModel]] = None,
        root: Optional[UIElementModel] = None
    ):
        self._elements: List[UIElementModel] = elements or []
        self._root: Optional[UIElementModel] = root
        self._id_map: Dict[str, UIElementModel] = {}
        self._parent_map: Dict[str, Optional[str]] = {}
        self._children_map: Dict[str, List[UIElementModel]] = {}
        self.build_hierarchy()

    def build_hierarchy(self):
        """Constructs parent/child indexing and resolves root element."""
        self._id_map.clear()
        self._parent_map.clear()
        self._children_map.clear()

        for el in self._elements:
            eid = el.element_id or el.id
            if eid:
                self._id_map[eid] = el
                self._children_map[eid] = []

        # Wire up parent-child relationships
        for el in self._elements:
            eid = el.element_id or el.id
            pid = el.parent_id
            if pid:
                self._parent_map[eid] = pid
                if pid in self._children_map:
                    if el not in self._children_map[pid]:
                        self._children_map[pid].append(el)
                # Also wire object references if children list is empty
                parent_obj = self._id_map.get(pid)
                if parent_obj and el not in parent_obj.children:
                    parent_obj.children.append(el)

        # Determine root element if not explicitly provided
        if not self._root and self._elements:
            # First element without a parent, or simply the first element
            roots = [e for e in self._elements if not e.parent_id or e.parent_id not in self._id_map]
            self._root = roots[0] if roots else self._elements[0]

    @property
    def root(self) -> Optional[UIElementModel]:
        return self._root

    @root.setter
    def root(self, new_root: Optional[UIElementModel]):
        self._root = new_root

    @property
    def elements(self) -> List[UIElementModel]:
        return self._elements

    def get_parent(self, element: UIElementModel) -> Optional[UIElementModel]:
        """Returns the parent UIElementModel of the specified element, or None."""
        pid = element.parent_id
        if not pid:
            eid = element.element_id or element.id
            pid = self._parent_map.get(eid)
        if pid:
            return self._id_map.get(pid)
        return None

    def get_children(self, element: UIElementModel) -> List[UIElementModel]:
        """Returns direct child elements of the specified element."""
        if element.children and isinstance(element.children[0], UIElementModel):
            return element.children
        eid = element.element_id or element.id
        return self._children_map.get(eid, [])

    def traversal(self, order: str = "dfs") -> Iterator[UIElementModel]:
        """Traverses the UI tree starting from the root or top-level elements.

        Yields elements in depth-first order.
        """
        visited = set()

        def _dfs(node: UIElementModel):
            nid = node.element_id or node.id or id(node)
            if nid in visited:
                return
            visited.add(nid)
            yield node
            for child in self.get_children(node):
                yield from _dfs(child)

        # Start with root if set, otherwise start with top-level elements
        if self._root:
            yield from _dfs(self._root)

        for el in self._elements:
            eid = el.element_id or el.id or id(el)
            if eid not in visited:
                yield from _dfs(el)

    def traverse(self) -> Iterator[UIElementModel]:
        """Convenience alias for traversal()."""
        return self.traversal()

    def search_by_id(self, element_id: str) -> Optional[UIElementModel]:
        """Finds an element by its unique element ID."""
        return self._id_map.get(element_id)

    def get_element_by_id(self, elem_id: str) -> Optional[UIElementModel]:
        """Backward-compatible lookup by ID."""
        return self.search_by_id(elem_id)

    def search_by_control_type(self, control_type: str) -> List[UIElementModel]:
        """Searches for elements matching the specified control type (case-insensitive)."""
        target = control_type.strip().lower()
        return [
            e for e in self._elements
            if e.control_type and e.control_type.strip().lower() == target
        ]

    def search_by_name(self, name: str, exact: bool = False) -> List[UIElementModel]:
        """Searches for elements matching accessible name (case-insensitive)."""
        target = name.strip().lower()
        results = []
        for e in self._elements:
            if not e.name:
                continue
            ename = e.name.strip().lower()
            if exact and ename == target:
                results.append(e)
            elif not exact and target in ename:
                results.append(e)
        return results

    @property
    def focused_element(self) -> Optional[UIElementModel]:
        """Returns the currently focused UI element, if any."""
        return self.get_focused_element()

    def get_focused_element(self) -> Optional[UIElementModel]:
        """Returns the UI element that has keyboard focus."""
        for e in self._elements:
            if e.focused or e.has_keyboard_focus:
                return e
        return None

    def summary_counts(self) -> Dict[str, int]:
        """Calculates element breakdown summary."""
        total = len(self._elements)
        focusable = sum(1 for e in self._elements if e.focusable or e.is_focusable)
        named = sum(1 for e in self._elements if e.name and e.name.strip())
        unnamed = total - named
        return {
            "total": total,
            "focusable": focusable,
            "named": named,
            "unnamed": unnamed,
        }

    def get_interactive_elements(self) -> List[UIElementModel]:
        """Filters interactive control types (Button, Edit, CheckBox, ComboBox, Hyperlink)."""
        interactive_types = {
            "button", "edit", "checkbox", "radiobutton", "combobox",
            "hyperlink", "menuitem", "tabitem", "slider", "listitem"
        }
        return [
            e for e in self._elements
            if (e.control_type and e.control_type.lower() in interactive_types) or e.is_focusable
        ]

    def find_element_at_point(self, x: int, y: int) -> Optional[UIElementModel]:
        """Returns the innermost UI element enclosing coordinates (x, y)."""
        candidates = []
        for e in self._elements:
            if not e.bounds or len(e.bounds) < 4:
                continue
            ex, ey, ew, eh = e.bounds
            if ex <= x <= ex + ew and ey <= y <= ey + eh:
                candidates.append(e)

        if not candidates:
            return None

        # Sort by area ascending (smallest / innermost first)
        candidates.sort(key=lambda el: (el.bounds[2] if el.bounds else 0) * (el.bounds[3] if el.bounds else 0))
        return candidates[0]

    def correlate_with_ocr_boxes(self, ocr_boxes: List[dict]):
        """Associates OCR text with matching UI element bounding boxes."""
        for box_info in ocr_boxes:
            box = box_info.get("box")
            text = box_info.get("text", "").strip()
            if not box or not text:
                continue

            # Compute box center
            if len(box) == 4 and isinstance(box[0], (list, tuple)):
                cx = sum(p[0] for p in box) / 4.0
                cy = sum(p[1] for p in box) / 4.0
            elif len(box) == 4:
                cx = (box[0] + box[2]) / 2.0
                cy = (box[1] + box[3]) / 2.0
            else:
                continue

            target = self.find_element_at_point(int(cx), int(cy))
            if target:
                if target.ocr_associated_text:
                    target.ocr_associated_text += " " + text
                else:
                    target.ocr_associated_text = text

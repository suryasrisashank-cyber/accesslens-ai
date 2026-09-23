"""Focus Path model and visual path representation for AccessLens AI.

Models sequential transitions across elements, calculates transition frequencies,
detects repeated paths, and generates visual segments for UI overlays.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from accessibility.focus_models import FocusObservation


@dataclass
class FocusPathNode:
    """Individual node in the focus traversal sequence."""
    index: int
    element_id: Optional[str] = None
    name: str = "<Unnamed>"
    control_type: str = "Control"
    automation_id: str = ""
    bounds: Optional[List[int]] = None
    is_focused: bool = True
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "element_id": self.element_id,
            "name": self.name,
            "control_type": self.control_type,
            "automation_id": self.automation_id,
            "bounds": list(self.bounds) if self.bounds else None,
            "is_focused": self.is_focused,
            "timestamp": self.timestamp,
        }


@dataclass
class FocusPathTransition:
    """A directed transition from one focused element to the next."""
    from_index: int
    to_index: int
    from_name: str
    to_name: str
    from_id: str = ""
    to_id: str = ""
    from_bounds: Optional[List[int]] = None
    to_bounds: Optional[List[int]] = None
    count: int = 1
    is_repeated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_index": self.from_index,
            "to_index": self.to_index,
            "from_name": self.from_name,
            "to_name": self.to_name,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "from_bounds": list(self.from_bounds) if self.from_bounds else None,
            "to_bounds": list(self.to_bounds) if self.to_bounds else None,
            "count": self.count,
            "is_repeated": self.is_repeated,
        }


class FocusPath:
    """Represents the complete ordered path traversed by keyboard focus."""

    def __init__(
        self,
        nodes: Optional[List[FocusPathNode]] = None,
        transitions: Optional[List[FocusPathTransition]] = None,
        direction: str = "forward",
        has_loops: bool = False,
        has_trap: bool = False,
    ):
        self.nodes: List[FocusPathNode] = nodes or []
        self.transitions: List[FocusPathTransition] = transitions or []
        self.direction = direction
        self.has_loops = has_loops
        self.has_trap = has_trap

    @classmethod
    def build_from_observations(cls, observations: List[FocusObservation]) -> "FocusPath":
        """Builds a FocusPath graph from a list of FocusObservation records."""
        if not observations:
            return cls()

        nodes: List[FocusPathNode] = []
        transitions: List[FocusPathTransition] = []
        transition_counts: Dict[Tuple[str, str], int] = {}
        direction = observations[0].direction if observations else "forward"

        for idx, obs in enumerate(observations):
            node = FocusPathNode(
                index=idx + 1,
                element_id=obs.element_id,
                name=obs.element_name or "<Unnamed>",
                control_type=obs.control_type or "Control",
                automation_id=obs.automation_id or "",
                bounds=obs.bounds,
                is_focused=obs.is_focused,
                timestamp=obs.timestamp,
            )
            nodes.append(node)

            if idx > 0:
                prev_node = nodes[idx - 1]
                pair_key = (
                    prev_node.automation_id or prev_node.element_id or prev_node.name,
                    node.automation_id or node.element_id or node.name
                )
                transition_counts[pair_key] = transition_counts.get(pair_key, 0) + 1
                is_rep = transition_counts[pair_key] > 1

                trans = FocusPathTransition(
                    from_index=prev_node.index,
                    to_index=node.index,
                    from_name=prev_node.name,
                    to_name=node.name,
                    from_id=pair_key[0],
                    to_id=pair_key[1],
                    from_bounds=prev_node.bounds,
                    to_bounds=node.bounds,
                    count=transition_counts[pair_key],
                    is_repeated=is_rep,
                )
                transitions.append(trans)

        has_loops = any(t.is_repeated for t in transitions)
        return cls(nodes=nodes, transitions=transitions, direction=direction, has_loops=has_loops)

    def get_visual_segments(self) -> List[Dict[str, Any]]:
        """Returns coordinate lines and step annotations for screenshot visual overlay.
        
        Returns empty list if coordinates are not available for mapping.
        """
        segments: List[Dict[str, Any]] = []
        for trans in self.transitions:
            if trans.from_bounds and trans.to_bounds:
                fb = trans.from_bounds
                tb = trans.to_bounds
                # Calculate center points
                p1 = (fb[0] + fb[2] // 2, fb[1] + fb[3] // 2)
                p2 = (tb[0] + tb[2] // 2, tb[1] + tb[3] // 2)
                segments.append({
                    "start_point": p1,
                    "end_point": p2,
                    "from_name": trans.from_name,
                    "to_name": trans.to_name,
                    "from_step": trans.from_index,
                    "to_step": trans.to_index,
                    "is_repeated": trans.is_repeated,
                })
        return segments

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "node_count": len(self.nodes),
            "transition_count": len(self.transitions),
            "has_loops": self.has_loops,
            "has_trap": self.has_trap,
            "nodes": [n.to_dict() for n in self.nodes],
            "transitions": [t.to_dict() for t in self.transitions],
        }

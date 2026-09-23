"""Unit tests for AccessLens AI Phase 1 and Phase 2.

Tests normalized ElementModel, UITree, parent/child relationships,
tree traversal, element lookup, missing property handling, UI Automation adapter initialization,
mock extraction, and InterfaceSnapshot data integrity.
Deterministic tests with zero external dependencies.
"""

import json
import pytest
from typing import List

from accessibility.element_model import ElementModel, InterfaceSnapshot, UIElementModel
from accessibility.ui_automation import UIAutomationClient, UIAutomationInspectionResult
from accessibility.ui_tree import UITree


def test_element_model_initialization():
    """Verifies all normalized fields in ElementModel."""
    elem = ElementModel(
        element_id="btn_ok",
        parent_id="dialog_main",
        control_type="Button",
        name="OK",
        automation_id="btn_confirm",
        class_name="WPFButton",
        bounds=[100, 200, 80, 32],
        enabled=True,
        visible=True,
        focusable=True,
        focused=False,
        value="Confirm",
        text="OK",
        patterns=["InvokePattern"]
    )
    assert elem.element_id == "btn_ok"
    assert elem.parent_id == "dialog_main"
    assert elem.control_type == "Button"
    assert elem.name == "OK"
    assert elem.automation_id == "btn_confirm"
    assert elem.class_name == "WPFButton"
    assert elem.bounds == [100, 200, 80, 32]
    assert elem.enabled is True
    assert elem.visible is True
    assert elem.focusable is True
    assert elem.focused is False
    assert elem.value == "Confirm"
    assert elem.text == "OK"
    assert elem.patterns == ["InvokePattern"]

    # Test backward-compatible aliases
    assert elem.id == "btn_ok"
    assert elem.is_enabled is True
    assert elem.is_visible is True
    assert elem.is_focusable is True
    assert elem.has_keyboard_focus is False
    assert elem.supported_patterns == ["InvokePattern"]


def test_element_model_missing_properties():
    """Verifies that unobtained properties remain None and are not invented."""
    elem = ElementModel(element_id="elem_minimal")

    assert elem.element_id == "elem_minimal"
    assert elem.parent_id is None
    assert elem.control_type is None
    assert elem.name is None
    assert elem.automation_id is None
    assert elem.class_name is None
    assert elem.bounds is None
    assert elem.enabled is None
    assert elem.visible is None
    assert elem.focusable is None
    assert elem.focused is None
    assert elem.value is None
    assert elem.text is None

    # Verifies display helper returns "Not available" for None fields
    assert elem.get_property_display("control_type") == "Not available"
    assert elem.get_property_display("name") == "Not available"
    assert elem.get_property_display("automation_id") == "Not available"
    assert elem.get_property_display("bounds") == "Not available"
    assert elem.get_property_display("enabled") == "Not available"
    assert elem.get_property_display("value") == "Not available"


def test_ui_tree_creation_and_root():
    """Verifies UITree creation and root identification."""
    w = ElementModel(element_id="win", control_type="Window", name="Main Window")
    b = ElementModel(element_id="btn", parent_id="win", control_type="Button", name="Submit")
    tree = UITree([w, b])

    assert tree.root is not None
    assert tree.root.element_id == "win"
    assert len(tree.elements) == 2


def test_ui_tree_parent_child_relationships():
    """Verifies parent/child hierarchy traversal and querying."""
    root = ElementModel(element_id="root_win", control_type="Window", name="App")
    panel = ElementModel(element_id="panel_1", parent_id="root_win", control_type="Pane", name="Form")
    btn1 = ElementModel(element_id="btn_1", parent_id="panel_1", control_type="Button", name="Save")
    btn2 = ElementModel(element_id="btn_2", parent_id="panel_1", control_type="Button", name="Cancel")

    tree = UITree([root, panel, btn1, btn2])

    # Check parent
    assert tree.get_parent(panel) == root
    assert tree.get_parent(btn1) == panel
    assert tree.get_parent(btn2) == panel
    assert tree.get_parent(root) is None

    # Check children
    root_children = tree.get_children(root)
    assert len(root_children) == 1
    assert root_children[0].element_id == "panel_1"

    panel_children = tree.get_children(panel)
    assert len(panel_children) == 2
    assert {c.element_id for c in panel_children} == {"btn_1", "btn_2"}


def test_ui_tree_traversal():
    """Verifies depth-first traversal order through elements."""
    root = ElementModel(element_id="w", control_type="Window")
    child_a = ElementModel(element_id="a", parent_id="w", control_type="Pane")
    child_b = ElementModel(element_id="b", parent_id="w", control_type="Pane")
    grandchild = ElementModel(element_id="g", parent_id="a", control_type="Button")

    tree = UITree([root, child_a, child_b, grandchild])

    traversed_ids = [e.element_id for e in tree.traversal()]
    # DFS should visit root -> child_a -> grandchild -> child_b
    assert traversed_ids == ["w", "a", "g", "b"]
    assert len(list(tree.traverse())) == 4


def test_ui_tree_element_lookup():
    """Verifies element lookup by ID, control type, and accessible name."""
    e1 = ElementModel(element_id="id_1", control_type="Button", name="Save Changes")
    e2 = ElementModel(element_id="id_2", control_type="Edit", name="Username Input")
    e3 = ElementModel(element_id="id_3", control_type="Button", name="Cancel")

    tree = UITree([e1, e2, e3])

    # Search by ID
    assert tree.search_by_id("id_1") == e1
    assert tree.search_by_id("non_existent") is None
    assert tree.get_element_by_id("id_2") == e2

    # Search by control type (case-insensitive)
    buttons = tree.search_by_control_type("button")
    assert len(buttons) == 2
    assert {b.element_id for b in buttons} == {"id_1", "id_3"}

    edits = tree.search_by_control_type("EDIT")
    assert len(edits) == 1
    assert edits[0].element_id == "id_2"

    # Search by name
    res_exact = tree.search_by_name("Cancel", exact=True)
    assert len(res_exact) == 1
    assert res_exact[0].element_id == "id_3"

    res_sub = tree.search_by_name("change")
    assert len(res_sub) == 1
    assert res_sub[0].element_id == "id_1"


def test_ui_tree_focused_element_and_summary():
    """Verifies focused element detection and summary count metrics."""
    e1 = ElementModel(element_id="e1", control_type="Window", name="Win")
    e2 = ElementModel(element_id="e2", control_type="Edit", name="User", focusable=True, focused=True)
    e3 = ElementModel(element_id="e3", control_type="Button", name="", focusable=True, focused=False)

    tree = UITree([e1, e2, e3])

    # Focused element
    focused = tree.focused_element
    assert focused is not None
    assert focused.element_id == "e2"

    # Summary counts
    counts = tree.summary_counts()
    assert counts["total"] == 3
    assert counts["focusable"] == 2
    assert counts["named"] == 2
    assert counts["unnamed"] == 1


def test_ui_automation_adapter_initialization():
    """Verifies UIAutomationClient initialization and timeout configuration."""
    client = UIAutomationClient(timeout_sec=4.5)
    assert client.timeout_sec == 4.5
    # Should safely report boolean for is_windows
    assert isinstance(client.is_windows(), bool)


def test_ui_automation_mock_extraction(monkeypatch):
    """Verifies UI Automation data ingestion and property preservation using deterministic mock data."""
    mock_payload = {
        "window_title": "Calculator",
        "app_name": "CalculatorApp",
        "elements": [
            {
                "id": "c_win",
                "name": "Calculator Window",
                "control_type": "Window",
                "automation_id": "CalcFrame",
                "class_name": "ApplicationFrameWindow",
                "is_enabled": True,
                "is_focusable": False,
                "is_focused": False,
                "bounds": [100, 100, 400, 600],
                "is_visible": True,
                "value": None,
                "patterns": ["WindowPattern"]
            },
            {
                "id": "c_btn_eq",
                "name": "Equals",
                "control_type": "Button",
                "automation_id": "equalButton",
                "class_name": "Button",
                "is_enabled": True,
                "is_focusable": True,
                "is_focused": False,
                "bounds": [300, 500, 80, 50],
                "is_visible": True,
                "value": None,
                "patterns": ["InvokePattern"]
            },
            {
                # Element with missing properties
                "id": "c_unnamed",
                "name": None,
                "control_type": "Custom",
                "automation_id": None,
                "class_name": None,
                "is_enabled": True,
                "is_focusable": False,
                "is_focused": False,
                "bounds": None,
                "is_visible": True,
                "value": None,
                "patterns": []
            }
        ]
    }

    client = UIAutomationClient()
    monkeypatch.setattr(client, "_run_powershell", lambda script: json.dumps(mock_payload))
    monkeypatch.setattr(client, "is_windows", lambda: True)

    result = client.inspect_window(12345)
    assert isinstance(result, UIAutomationInspectionResult)
    assert result.window_title == "Calculator"
    assert result.app_name == "CalculatorApp"
    assert len(result.elements) == 3
    assert result.status_message == "Partial accessibility metadata available."

    # Verify first element
    el0 = result.elements[0]
    assert el0.element_id == "c_win"
    assert el0.name == "Calculator Window"
    assert el0.bounds == [100, 100, 400, 600]

    # Verify element with missing properties preserves None
    el2 = result.elements[2]
    assert el2.element_id == "c_unnamed"
    assert el2.name is None
    assert el2.automation_id is None
    assert el2.class_name is None
    assert el2.bounds is None

    # Verify UITree is populated
    assert result.ui_tree is not None
    assert len(result.ui_tree.elements) == 3


def test_interface_snapshot_creation():
    """Verifies InterfaceSnapshot initialization with Phase 1/2 fields and future placeholders."""
    w = ElementModel(element_id="w", control_type="Window", name="Demo App")
    tree = UITree([w])

    snapshot = InterfaceSnapshot(
        timestamp="2026-09-22T12:00:00Z",
        application_name="DemoApp.exe",
        window_title="Demo Main Window",
        ui_tree=tree,
        hardware_state="Local AMD CPU",
        backend="CPUExecutionProvider"
    )

    assert snapshot.timestamp == "2026-09-22T12:00:00Z"
    assert snapshot.application_name == "DemoApp.exe"
    assert snapshot.window_title == "Demo Main Window"
    assert snapshot.ui_tree == tree
    assert snapshot.hardware_state == "Local AMD CPU"
    assert snapshot.backend == "CPUExecutionProvider"

    # Future phase fields initialized to empty/None
    assert snapshot.ocr_result is None
    assert snapshot.visual_observations == []
    assert snapshot.deterministic_findings == []
    assert snapshot.keyboard_observations == []
    assert snapshot.evidence == []

    # Synchronization with backward compatibility elements
    assert len(snapshot.elements) == 1
    assert snapshot.elements[0].element_id == "w"

    d = snapshot.to_dict()
    assert d["application_name"] == "DemoApp.exe"
    assert d["window_title"] == "Demo Main Window"
    assert d["elements_count"] == 1
    assert d["backend"] == "CPUExecutionProvider"

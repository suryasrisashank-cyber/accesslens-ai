"""Comprehensive automated tests for AccessLens AI accessibility subsystem."""

from PIL import Image, ImageDraw
import pytest

from accessibility.audit_coordinator import audit_coordinator
from accessibility.contrast_engine import (
    calculate_contrast_ratio, relative_luminance, sample_region_contrast
)
from accessibility.element_model import (
    FindingCategory, FindingModel, FindingSeverity,
    InterfaceSnapshot, SignalType, UIElementModel
)
from accessibility.evidence_engine import evidence_engine
from accessibility.keyboard_audit import KeyboardAuditor, keyboard_auditor
from accessibility.remediation_engine import remediation_engine
from accessibility.report_generator import report_generator
from accessibility.rule_engine import rule_engine
from accessibility.ui_tree import UITree


def test_element_model_properties():
    elem = UIElementModel(
        id="btn_1",
        name="Submit Form",
        control_type="Button",
        automation_id="submit_btn",
        bounds=[10, 20, 100, 40],
        is_focusable=True
    )
    assert elem.display_label == '[Button] "Submit Form"'
    d = elem.to_dict()
    assert d["id"] == "btn_1"
    assert d["control_type"] == "Button"
    assert d["bounds"] == [10, 20, 100, 40]


def test_ui_tree_spatial_search():
    e1 = UIElementModel(id="w1", name="Window", control_type="Window", bounds=[0, 0, 800, 600])
    e2 = UIElementModel(id="b1", name="Apply", control_type="Button", bounds=[50, 50, 120, 40], is_focusable=True)
    tree = UITree([e1, e2])

    # Point inside button
    target = tree.find_element_at_point(60, 60)
    assert target is not None
    assert target.id == "b1"

    # Point outside button but in window
    target_win = tree.find_element_at_point(400, 400)
    assert target_win is not None
    assert target_win.id == "w1"

    # Interactive elements
    interactive = tree.get_interactive_elements()
    assert len(interactive) == 1
    assert interactive[0].id == "b1"


def test_contrast_calculation():
    # Black on White: 21:1
    res_bw = calculate_contrast_ratio((0, 0, 0), (255, 255, 255))
    assert res_bw.contrast_ratio >= 20.0
    assert res_bw.passes_aa_normal is True
    assert res_bw.passes_aaa_normal is True

    # Low contrast gray on white: #AAAAAA on #FFFFFF: ~2.3:1
    res_low = calculate_contrast_ratio((170, 170, 170), (255, 255, 255))
    assert res_low.contrast_ratio < 4.5
    assert res_low.passes_aa_normal is False


def test_rule_missing_accessible_name():
    # Button with empty accessible name
    unnamed_button = UIElementModel(
        id="btn_icon",
        name="",
        control_type="Button",
        bounds=[100, 100, 80, 40],
        is_focusable=True
    )
    findings = rule_engine.evaluate_element(unnamed_button)
    assert any("Missing Accessible Name" in f.title for f in findings)
    f_missing = next(f for f in findings if "Missing" in f.title)
    assert f_missing.category == FindingCategory.LABEL
    assert f_missing.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]


def test_rule_label_in_name_mismatch():
    mismatched_btn = UIElementModel(
        id="btn_mismatch",
        name="Order Food Online",
        control_type="Button",
        ocr_associated_text="Contact Support Inquiry",
        bounds=[100, 100, 150, 40],
        is_focusable=True
    )
    findings = rule_engine.evaluate_element(mismatched_btn)
    assert any("Discrepancy" in f.title for f in findings)


def test_rule_unfocused_interactive_element():
    unfocused_btn = UIElementModel(
        id="btn_nofocus",
        name="Click Here",
        control_type="Button",
        bounds=[100, 100, 100, 40],
        is_focusable=False  # Barrier: interactive but cannot be tabbed to
    )
    findings = rule_engine.evaluate_element(unfocused_btn)
    assert any("Focusable" in f.title for f in findings)


def test_rule_small_target_size():
    tiny_btn = UIElementModel(
        id="btn_tiny",
        name="Close",
        control_type="Button",
        bounds=[10, 10, 14, 14],  # 14x14 pixels < 24px WCAG 2.5.8
        is_focusable=True
    )
    findings = rule_engine.evaluate_element(tiny_btn)
    assert any("Undersized" in f.title for f in findings)


def test_keyboard_auditor():
    auditor = KeyboardAuditor()
    auditor.start_audit()
    auditor.record_focus("Search Input", "Edit", "search_box", [10, 10, 100, 30])
    auditor.record_focus("Search Button", "Button", "search_btn", [120, 10, 80, 30])
    auditor.record_focus("Search Button", "Button", "search_btn", [120, 10, 80, 30])  # Duplicate step

    report = auditor.stop_audit()
    assert len(report.steps) == 3
    assert any("Duplicate Focus" in f.title for f in report.findings)


def test_evidence_engine_formatting():
    msg = evidence_engine.format_evidence_item(SignalType.MEASURED, "Contrast ratio 2.1:1")
    assert msg.startswith("[MEASURED]")


def test_sensitive_data_masking():
    raw_text = (
        "User email: developer@qualcomm.com\n"
        "Contact: +1 (555) 234-5678\n"
        "Credit card: 4111 2222 3333 4444\n"
        "api_key: sk_live_abcdef1234567890\n"
    )
    masked = report_generator.mask_sensitive_data(raw_text)
    assert "[REDACTED_EMAIL]" in masked
    assert "[REDACTED_PHONE]" in masked
    assert "[REDACTED_PAYMENT_CARD]" in masked
    assert "[REDACTED_CREDENTIAL]" in masked
    assert "developer@qualcomm.com" not in masked


def test_report_generation():
    snapshot = InterfaceSnapshot(
        timestamp="2026-09-22 12:00:00",
        application_name="TestApp",
        window_title="Main Test Window",
        window_handle=1234,
        elements=[],
        findings=[
            FindingModel(
                id="f1",
                title="Missing Accessible Name",
                category=FindingCategory.LABEL,
                severity=FindingSeverity.CRITICAL,
                confidence=0.95,
                evidence=["[DETECTED] Button has no accessible name"],
                recommendation="Provide accessible name",
                remediation_code="AutomationProperties.SetName(b, 'Save');"
            )
        ],
        backend_state="CPU Fallback",
        hardware_summary="AMD Ryzen 3 2200U"
    )

    md = report_generator.generate_markdown(snapshot)
    assert "# ACCESSLENS AI ACCESSIBILITY AUDIT REPORT" in md
    assert "Missing Accessible Name" in md

    js = report_generator.generate_json(snapshot)
    assert '"application_name": "TestApp"' in js

    html = report_generator.generate_html(snapshot)
    assert "<!DOCTYPE html>" in html
    assert "Missing Accessible Name" in html

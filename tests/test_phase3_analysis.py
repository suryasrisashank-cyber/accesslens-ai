"""Deterministic Unit Tests for AccessLens AI Phase 3 — Evidence-First Analysis.

Covers all 16 required tests:
1. Missing accessible name
2. Interactive vs non-interactive filtering
3. Visible-name match
4. Visible-name mismatch
5. Insufficient OCR evidence
6. Focusability issue
7. Interactive size observation
8. Label detection
9. Contrast ratio calculation
10. Estimated contrast labeling
11. Evidence generation
12. Finding serialization
13. Severity model
14. Confidence separation from severity
15. Human verification flag
16. UIA-to-screenshot mapping

Uses synthetic deterministic data with zero external dependencies.
"""

from PIL import Image, ImageDraw
import pytest

from accessibility.coordinate_mapping import coordinate_mapper
from accessibility.contrast_engine import (
    calculate_contrast_ratio, relative_luminance, sample_region_contrast
)
from accessibility.element_model import ElementModel, UIElementModel
from accessibility.evidence_engine import (
    EvidenceItem, EvidenceSource, evidence_engine
)
from accessibility.findings import (
    AccessibilityFinding, FindingCategory, FindingModel, SignalType
)
from accessibility.rule_engine import (
    ContrastRule, FocusabilityRule, InteractiveSizeRule,
    LabelRule, MissingAccessibleNameRule, NameMismatchRule,
    SemanticMismatchRule, rule_engine
)
from accessibility.severity import FindingSeverity, describe_severity
from accessibility.ui_tree import UITree


# Test 1: Missing accessible name
def test_missing_accessible_name():
    rule = MissingAccessibleNameRule()
    btn = ElementModel(element_id="btn_unnamed", control_type="Button", name="", focusable=True)
    findings = rule.evaluate(btn)
    assert len(findings) == 1
    assert "Missing Accessible Name" in findings[0].title
    assert findings[0].category == FindingCategory.LABEL
    assert findings[0].severity in [FindingSeverity.HIGH, FindingSeverity.MEDIUM]
    assert findings[0].confidence >= 0.90


# Test 2: Interactive vs non-interactive filtering
def test_interactive_vs_non_interactive_filtering():
    rule = MissingAccessibleNameRule()
    # Non-interactive controls with empty name should NOT trigger missing name finding
    pane = ElementModel(element_id="p1", control_type="Pane", name="")
    window = ElementModel(element_id="w1", control_type="Window", name="")
    group = ElementModel(element_id="g1", control_type="Group", name="")

    assert len(rule.evaluate(pane)) == 0
    assert len(rule.evaluate(window)) == 0
    assert len(rule.evaluate(group)) == 0


# Test 3: Visible-name match
def test_visible_name_match():
    rule = NameMismatchRule()
    btn = ElementModel(
        element_id="btn_ok",
        control_type="Button",
        name="Submit Application",
        ocr_associated_text="Submit Application"
    )
    findings = rule.evaluate(btn)
    assert len(findings) == 0


# Test 4: Visible-name mismatch
def test_visible_name_mismatch():
    rule = NameMismatchRule()
    btn = ElementModel(
        element_id="btn_mismatch",
        control_type="Button",
        name="Search",
        ocr_associated_text="Submit Application"
    )
    findings = rule.evaluate(btn)
    assert len(findings) == 1
    assert "Discrepancy" in findings[0].title
    assert findings[0].category == FindingCategory.LABEL


# Test 5: Insufficient OCR evidence
def test_insufficient_ocr_evidence():
    rule = NameMismatchRule()
    # Too short OCR text should not cause false positive
    btn_short = ElementModel(
        element_id="b1",
        control_type="Button",
        name="OK",
        ocr_associated_text="OK"
    )
    assert len(rule.evaluate(btn_short)) == 0

    # Empty OCR text
    btn_empty_ocr = ElementModel(
        element_id="b2",
        control_type="Button",
        name="Cancel",
        ocr_associated_text=""
    )
    assert len(rule.evaluate(btn_empty_ocr)) == 0


# Test 6: Focusability issue
def test_focusability_issue():
    rule = FocusabilityRule()
    btn = ElementModel(
        element_id="btn_unfoc",
        control_type="Button",
        name="Delete Record",
        enabled=True,
        visible=True,
        focusable=False
    )
    findings = rule.evaluate(btn)
    assert len(findings) == 1
    assert "Potential Keyboard Accessibility Issue" in findings[0].title
    assert findings[0].category == FindingCategory.KEYBOARD
    assert findings[0].severity == FindingSeverity.HIGH


# Test 7: Interactive size observation
def test_interactive_size_observation():
    rule = InteractiveSizeRule(min_size=24)
    # Small 16x16 icon button
    small_btn = ElementModel(
        element_id="btn_tiny",
        control_type="Button",
        name="Close",
        bounds=[100, 100, 16, 16]
    )
    findings = rule.evaluate(small_btn)
    assert len(findings) == 1
    assert "Potentially Small Interactive Target" in findings[0].title
    assert findings[0].category == FindingCategory.TARGET_SIZE
    assert findings[0].signal_type == SignalType.MEASURED


# Test 8: Label detection for input controls
def test_label_detection():
    rule = LabelRule()
    # Edit field with no accessible name and no nearby OCR text
    unlabeled_input = ElementModel(
        element_id="txt_user",
        control_type="Edit",
        name="",
        ocr_associated_text=""
    )
    findings = rule.evaluate(unlabeled_input)
    assert len(findings) == 1
    assert "Input May Lack a Clear Accessible Label" in findings[0].title
    assert findings[0].category == FindingCategory.LABEL


# Test 9: Contrast ratio calculation
def test_contrast_ratio_calculation():
    # Pure black on white: 21:1
    res_bw = calculate_contrast_ratio((0, 0, 0), (255, 255, 255))
    assert res_bw.contrast_ratio >= 20.9
    assert res_bw.passes_aa_normal is True

    # Gray #888888 on White #FFFFFF: ~3.5:1 (fails AA 4.5:1)
    res_gray = calculate_contrast_ratio((136, 136, 136), (255, 255, 255))
    assert res_gray.contrast_ratio < 4.5
    assert res_gray.passes_aa_normal is False


# Test 10: Estimated contrast labeling
def test_estimated_contrast_labeling():
    # Synthetic 50x50 image with light background and gray text
    img = Image.new("RGB", (50, 50), (240, 240, 240))
    d = ImageDraw.Draw(img)
    d.rectangle([15, 15, 35, 35], fill=(120, 120, 120))

    res = sample_region_contrast(img, [0, 0, 50, 50])
    assert res is not None
    assert res.is_estimated is True
    assert "Estimated from rendered pixels" in res.method
    assert "antialiasing" in res.limitations.lower()


# Test 11: Evidence generation and chain
def test_evidence_generation():
    ev_item = evidence_engine.create_item(
        source=EvidenceSource.UI_AUTOMATION,
        evidence_type=SignalType.DETECTED,
        description="IsKeyboardFocusable: False",
        value=False,
        element_id="btn_1"
    )
    assert ev_item.source == "UI_AUTOMATION"
    assert ev_item.type == "DETECTED"
    assert "[DETECTED]" in str(ev_item)

    finding = AccessibilityFinding(
        finding_id="f1",
        title="Test Barrier",
        category=FindingCategory.KEYBOARD,
        severity=FindingSeverity.HIGH,
        confidence=0.88,
        evidence=[ev_item],
        observation="Test observation",
        impact="Test impact",
        recommendation="Test recommendation"
    )
    chain = evidence_engine.build_evidence_chain(finding)
    assert chain["finding_title"] == "Test Barrier"
    assert chain["observation"] == "Test observation"
    assert len(chain["evidence"]) == 1


# Test 12: Finding serialization
def test_finding_serialization():
    finding = AccessibilityFinding(
        finding_id="f_serial_1",
        title="Serialization Test",
        category=FindingCategory.LABEL,
        severity=FindingSeverity.MEDIUM,
        confidence=0.85,
        status="open",
        affected_element_id="elem_42",
        source="Windows UI Automation",
        observation="Observation text",
        impact="Impact description",
        recommendation="Remediation steps",
        human_verification_required=True
    )
    d = finding.to_dict()
    assert d["finding_id"] == "f_serial_1"
    assert d["category"] == "NAME_AND_LABEL"
    assert d["severity"] == "MEDIUM"
    assert d["confidence"] == 0.85
    assert d["affected_element_id"] == "elem_42"
    assert d["human_verification_required"] is True


# Test 13: Severity levels
def test_severity_levels():
    assert FindingSeverity.INFO == "INFO"
    assert FindingSeverity.LOW == "LOW"
    assert FindingSeverity.MEDIUM == "MEDIUM"
    assert FindingSeverity.HIGH == "HIGH"
    assert FindingSeverity.CRITICAL == "CRITICAL"

    desc = describe_severity(FindingSeverity.HIGH)
    assert "High impact" in desc


# Test 14: Confidence separation from severity
def test_confidence_separation_from_severity():
    # Valid finding with high severity but calibrated moderate confidence
    finding = AccessibilityFinding(
        finding_id="f_calib",
        title="High Severity Moderate Confidence",
        category=FindingCategory.KEYBOARD,
        severity=FindingSeverity.HIGH,
        confidence=0.62,
        human_verification_required=True
    )
    assert finding.severity == FindingSeverity.HIGH
    assert finding.confidence == 0.62
    # Confidence must not automatically force severity change


# Test 15: Human verification flag
def test_human_verification_flag():
    btn = ElementModel(element_id="b", control_type="Button", name="")
    findings = rule_engine.evaluate_element(btn)
    assert len(findings) >= 1
    for f in findings:
        assert f.human_verification_required is True


# Test 16: UIA-to-screenshot coordinate mapping
def test_coordinate_mapping():
    # Element at (150, 150, 100, 50) within window at (100, 100, 800, 600)
    # Screenshot is 800x600 (scale 1.0)
    elem_bounds = [150, 150, 100, 50]
    win_bounds = [100, 100, 800, 600]
    screenshot_size = (800, 600)

    mapped, msg = coordinate_mapper.map_bounds_to_screenshot(elem_bounds, win_bounds, screenshot_size)
    assert mapped is not None
    # Relative x = 150 - 100 = 50; relative y = 150 - 100 = 50
    assert mapped == [50, 50, 100, 50]
    assert msg == "Mapped"

    # Offscreen or invalid bounds mapping
    offscreen_bounds = [5000, 5000, 100, 50]
    unmapped, unmsg = coordinate_mapper.map_bounds_to_screenshot(offscreen_bounds, win_bounds, screenshot_size)
    assert unmapped is None
    assert "unavailable" in unmsg

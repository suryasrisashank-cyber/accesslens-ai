"""Local AI reasoning and developer remediation guidance engine.

Translates deterministic accessibility findings and multi-signal evidence into
developer code fixes across XAML/WinUI, WinForms, and Web/HTML with human verification guidance.
"""

from typing import Dict, List, Optional
from accessibility.element_model import (
    FindingCategory, FindingModel, FindingSeverity,
    SignalType, UIElementModel
)


class RemediationEngine:
    """Generates precise developer remediation code and contextual explanations."""

    def explain_finding(self, finding: FindingModel) -> Dict[str, str]:
        """Provides technical context, accessibility impact, and remediation code."""
        category = finding.category
        name = finding.element_name or "control"
        ctype = finding.element_type or "Element"

        # 1. Missing Accessible Name
        if category == FindingCategory.LABEL and "Missing" in finding.title:
            return {
                "impact": "Screen readers (Narrator, NVDA, JAWS) announce this control as 'button' without indicating its purpose, disorienting non-sighted users.",
                "wpf_xaml": f'<Button AutomationProperties.Name="Descriptive Action Title"\n        AutomationProperties.HelpText="Explains the result of invoking this control" />',
                "winui_xaml": f'<Button x:Name="{name or "ActionButton"}"\n        AutomationProperties.Name="Descriptive Action Title" />',
                "winforms": f'this.{name or "actionButton"}.AccessibleName = "Descriptive Action Title";\nthis.{name or "actionButton"}.AccessibleDescription = "Performs the primary action";',
                "web_html": f'<button aria-label="Descriptive Action Title">Icon</button>',
                "verification_guidance": "Run Windows Narrator (Ctrl+Win+Enter) and press Tab until this control receives focus. Verify that Narrator speaks the descriptive title aloud."
            }

        # 2. Label vs Accessible Name Discrepancy
        if category == FindingCategory.LABEL and "Discrepancy" in finding.title:
            return {
                "impact": "Voice-control users (Windows Voice Access) activate buttons by speaking visible labels. If the programmatic name diverges, voice activation commands will fail.",
                "wpf_xaml": f'<!-- Ensure AutomationProperties.Name matches visible text exactly -->\n<Button Content="Submit Application"\n        AutomationProperties.Name="Submit Application" />',
                "winui_xaml": f'<Button Content="Submit Application"\n        AutomationProperties.Name="Submit Application" />',
                "winforms": f'this.button.Text = "Submit Application";\nthis.button.AccessibleName = "Submit Application";',
                "web_html": f'<button aria-label="Submit Application">Submit Application</button>',
                "verification_guidance": "Enable Windows Voice Access and say 'Click <visible label>'. Verify that the control activates without error."
            }

        # 3. Unfocusable Interactive Element
        if category == FindingCategory.KEYBOARD and "Focusable" in finding.title:
            return {
                "impact": "Keyboard-only navigators and switch-control users cannot tab to this element, creating an impassable workflow barrier.",
                "wpf_xaml": f'<Control Focusable="True" IsTabStop="True" KeyDown="OnControlKeyDown" />',
                "winui_xaml": f'<Control IsTabStop="True" KeyDown="OnControlKeyDown" />',
                "winforms": f'this.{name or "customControl"}.TabStop = true;',
                "web_html": f'<div role="button" tabindex="0" onkeydown="handleKey(event)">Action</div>',
                "verification_guidance": "Disconnect the mouse. Navigate using only the Tab key. Confirm that a visible focus rectangle highlights this control."
            }

        # 4. Undersized Click Target
        if category == FindingCategory.TARGET_SIZE:
            return {
                "impact": "Users with tremors, motor impairments, or touchscreens frequently miss small targets or trigger adjacent controls accidentally.",
                "wpf_xaml": f'<Button MinWidth="32" MinHeight="32" Padding="8,6" />',
                "winui_xaml": f'<Button MinWidth="32" MinHeight="32" Padding="8,6" />',
                "winforms": f'this.button.MinimumSize = new System.Drawing.Size(32, 32);',
                "web_html": f'button {{\n  min-width: 32px;\n  min-height: 32px;\n  padding: 6px 12px;\n}}',
                "verification_guidance": "Verify on a high-DPI display or touchscreen that the physical target measures at least 24x24 px (preferably 44x44 px)."
            }

        # 5. Low Color Contrast
        if category == FindingCategory.CONTRAST:
            return {
                "impact": "Low-vision users or individuals operating laptops in bright sunlight cannot discern low-contrast text against its background.",
                "wpf_xaml": f'<TextBlock Foreground="#FFFFFF" Background="#1E293B" /> <!-- Ratio > 7:1 -->',
                "winui_xaml": f'<TextBlock Foreground="{{ThemeResource TextFillColorPrimaryBrush}}" />',
                "winforms": f'this.label.ForeColor = System.Drawing.Color.White;\nthis.label.BackColor = System.Drawing.Color.FromArgb(20, 24, 33);',
                "web_html": f'color: #FFFFFF;\nbackground-color: #1A1D27; /* 10.5:1 ratio */',
                "verification_guidance": "Test with Windows High Contrast Mode (Left Alt + Left Shift + PrintScreen) to verify legibility across all contrast themes."
            }

        # Generic / Fallback
        return {
            "impact": "May introduce usability or accessibility barriers for assistive technology users.",
            "wpf_xaml": f'<!-- Review element accessibility properties -->',
            "winui_xaml": f'<!-- Review element accessibility properties -->',
            "winforms": f'// Review AccessibleName and AccessibleRole properties',
            "web_html": f'<!-- Review ARIA role and label properties -->',
            "verification_guidance": "Insufficient evidence for automated remediation — requires human verification by an accessibility QA tester."
        }

    def generate_speech_narration(self, finding: FindingModel) -> str:
        """Formulates clear, concise speech script for Read Aloud accessibility narration."""
        sev = finding.severity.value.lower()
        cat = finding.category.value.replace("_", " ").lower()
        title = finding.title
        rec = finding.recommendation
        target = f"on {finding.element_type} '{finding.element_name}'" if finding.element_name else ""

        return (
            f"Accessibility finding. Severity {sev}. Category: {cat}. "
            f"{title} {target}. "
            f"Recommendation: {rec}"
        )


# Singleton instance
remediation_engine = RemediationEngine()

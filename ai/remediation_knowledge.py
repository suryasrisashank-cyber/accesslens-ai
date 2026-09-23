"""Structured accessibility remediation knowledge base for AccessLens AI.

Defines deterministic remediation guidance, technical impacts, developer action steps,
and verification workflows for 9 distinct accessibility issue categories.
Follows strict rule: Only generate framework-specific code when the application framework
is reliably detected from metadata; otherwise, return agnostic guidance.
"""

from typing import Any, Dict, List, Optional


class RemediationKnowledgeBase:
    """Central repository of deterministic accessibility remediation guidance."""

    @staticmethod
    def get_category_guidance(
        category_key: str,
        element_name: str = "",
        control_type: str = "Element",
        detected_framework: Optional[str] = None,
        context_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Retrieves structured guidance for a specific accessibility defect category."""
        ctrl_display = element_name or control_type or "control"
        framework_key = (detected_framework or "").lower().strip()

        # 1. Missing Accessible Name
        if category_key == "MISSING_ACCESSIBLE_NAME":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<Button AutomationProperties.Name="Descriptive Action Title"\n        AutomationProperties.HelpText="Explains the result of invoking this control" />',
                winui=f'<Button x:Name="{element_name or "ActionButton"}"\n        AutomationProperties.Name="Descriptive Action Title" />',
                winforms=f'this.{element_name or "actionButton"}.AccessibleName = "Descriptive Action Title";\nthis.{element_name or "actionButton"}.AccessibleDescription = "Performs the primary action";',
                web=f'<button aria-label="Descriptive Action Title">{ctrl_display}</button>'
            )
            return {
                "issue_type": "Missing Accessible Name (WCAG 4.1.2)",
                "short_description": f"The interactive {control_type} does not expose a programmatic accessible name.",
                "why_it_matters": (
                    "Assistive technologies (screen readers like Windows Narrator, NVDA, JAWS, and voice navigation tools) "
                    "rely on the programmatic accessible name to announce control purpose to non-sighted or low-vision users. "
                    "Without a name, the element is announced only by its generic role (e.g., 'button'), leaving users unable "
                    "to determine what will occur when activated."
                ),
                "recommended_fix": (
                    f"Assign a concise, descriptive accessible name to '{ctrl_display}'. "
                    "Ensure the name succinctly describes the primary action (e.g., 'Save document' rather than 'Button')."
                ),
                "developer_actions": [
                    f"Set the accessible name property on '{ctrl_display}' in the source markup or control initialization.",
                    "If the control displays visible text, ensure the accessible name matches or includes the visible text.",
                    "If the control is an icon button without visible text, provide a descriptive name and tooltip/help text.",
                    "Avoid generic or redundant words such as 'button', 'icon', or 'graphic' in the name itself."
                ],
                "verification_steps": [
                    "Launch Windows Narrator (Ctrl+Win+Enter) and navigate to the element using Tab or CapsLock+Arrow keys.",
                    "Listen to the announcement: verify Narrator speaks the control's descriptive purpose and role.",
                    "Inspect the element in Windows Accessibility Insights or Inspect.exe to confirm Name is non-empty.",
                    "Verify that the name remains consistent across all localized languages supported by the application."
                ],
                "human_review_required": True,
                "limitations": "Automated inspection confirms whether a name property is populated, but cannot evaluate if the name clearly conveys user intent.",
                "code_remediation": framework_code,
            }

        # 2. Name Mismatch (Visible text vs Programmatic name)
        elif category_key == "NAME_MISMATCH":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<!-- Ensure AutomationProperties.Name matches visible text exactly -->\n<Button Content="{element_name or "Action"}"\n        AutomationProperties.Name="{element_name or "Action"}" />',
                winui=f'<Button Content="{element_name or "Action"}"\n        AutomationProperties.Name="{element_name or "Action"}" />',
                winforms=f'this.{element_name or "btn"}.Text = "{element_name or "Action"}";\nthis.{element_name or "btn"}.AccessibleName = "{element_name or "Action"}";',
                web=f'<button aria-label="{element_name or "Action"}">{element_name or "Action"}</button>'
            )
            return {
                "issue_type": "Visible Label and Programmatic Name Mismatch (WCAG 2.5.3)",
                "short_description": f"The programmatic accessible name does not contain or match the visible text label.",
                "why_it_matters": (
                    "Users operating Windows Voice Access or speech recognition software activate interface controls by speaking "
                    "their visible labels aloud. If the programmatic name diverges from what is seen on screen, speech commands "
                    "fail to target the control. Additionally, sighted screen-reader users experience cognitive disorientation "
                    "when speech output contradicts the visual display."
                ),
                "recommended_fix": (
                    f"Align the programmatic accessible name of '{ctrl_display}' so that it starts with or matches the visible text."
                ),
                "developer_actions": [
                    "Inspect the visible label text rendered on screen and compare it with the control's programmatic Name property.",
                    "Update the accessibility name attribute so that the exact visible string is present at the start of the accessible name.",
                    "Avoid overriding the accessible name with unrelated internal IDs or abbreviations."
                ],
                "verification_steps": [
                    "Enable Windows Voice Access and issue the command 'Click <visible label>'. Verify activation succeeds.",
                    "Inspect the element in Accessibility Insights: verify that the Name property starts with the visible text.",
                    "Verify with a screen reader that both visual and auditory cues convey the same action."
                ],
                "human_review_required": True,
                "limitations": "OCR bounding box correlation may occasionally pair text from an adjacent label. Visual verification confirms label ownership.",
                "code_remediation": framework_code,
            }

        # 3. Semantic Mismatch
        elif category_key == "SEMANTIC_MISMATCH":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<!-- Use semantic Button instead of generic border/canvas -->\n<Button Content="Trigger Action" />',
                winui=f'<Button Content="Trigger Action" />',
                winforms=f'// Replace custom Panel click handler with standard Button control',
                web=f'<!-- Replace clickable div with semantic button -->\n<button type="button">Trigger Action</button>'
            )
            return {
                "issue_type": "Control Role and Semantic Mismatch (WCAG 1.3.1 / 4.1.2)",
                "short_description": f"The visual representation or user interaction behaves as an interactive control, but programmatic role is generic.",
                "why_it_matters": (
                    "When clickable or interactive controls are built using generic non-interactive containers (such as Panes, "
                    "Images, or Divs) without correct roles, screen readers fail to communicate available interactions, "
                    "and standard keyboard activation (Enter/Space) is typically missing."
                ),
                "recommended_fix": (
                    f"Refactor '{ctrl_display}' to use a native semantic control (e.g. Button, Link, CheckBox) "
                    "or explicitly declare the correct accessibility role and control type."
                ),
                "developer_actions": [
                    "Replace generic container elements with native semantic controls (e.g. Button) wherever feasible.",
                    "If custom controls are necessary, implement standard UIA control patterns (InvokePattern, TogglePattern).",
                    "Ensure keyboard event listeners respond to both Enter and Space bar activation."
                ],
                "verification_steps": [
                    "Inspect control type in Accessibility Insights: ensure it reports the expected role (e.g., Button, CheckBox).",
                    "Verify that pressing Enter or Space when focused activates the control identically to a mouse click."
                ],
                "human_review_required": True,
                "limitations": "Heuristic role inference requires manual confirmation of intended interaction design.",
                "code_remediation": framework_code,
            }

        # 4. Focusability Issue
        elif category_key == "FOCUSABILITY_ISSUE":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<Control Focusable="True" IsTabStop="True" KeyDown="OnControlKeyDown" />',
                winui=f'<Control IsTabStop="True" KeyDown="OnControlKeyDown" />',
                winforms=f'this.{element_name or "control"}.TabStop = true;',
                web=f'<div role="button" tabindex="0" onkeydown="handleKeyDown(event)">Action</div>'
            )
            return {
                "issue_type": "Keyboard Focusability Violation (WCAG 2.1.1)",
                "short_description": f"The interactive {control_type} cannot receive keyboard focus through sequential navigation.",
                "why_it_matters": (
                    "Keyboard-only navigators, users with tremors, screen-reader users, and individuals using switch hardware "
                    "cannot reach unfocusable interactive elements using the Tab key. This creates an impassable barrier that "
                    "completely blocks essential workflows."
                ),
                "recommended_fix": (
                    f"Enable keyboard focusability and tab stop properties on '{ctrl_display}', and wire keyboard activation."
                ),
                "developer_actions": [
                    "Set IsTabStop=True (or tabindex='0' for web views) on the interactive control.",
                    "Ensure the control is part of the logical tab order and not skipped during forward/backward traversal.",
                    "Implement keyboard event handling (Enter and Space) corresponding to click handlers."
                ],
                "verification_steps": [
                    "Disconnect the mouse and navigate through the view using only Tab and Shift+Tab.",
                    "Confirm the element receives focus in a predictable, logical sequence.",
                    "Confirm that a visible focus indicator clearly outlines the element when focused."
                ],
                "human_review_required": True,
                "limitations": "Automated UIA checks verify the IsKeyboardFocusable flag, but logical tab sequence order requires end-to-end traversal testing.",
                "code_remediation": framework_code,
            }

        # 5. Interactive Region Size
        elif category_key == "INTERACTIVE_REGION_SIZE":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<Button MinWidth="32" MinHeight="32" Padding="8,6" /> <!-- Prefer 44x44 for touch -->',
                winui=f'<Button MinWidth="32" MinHeight="32" Padding="8,6" />',
                winforms=f'this.{element_name or "btn"}.MinimumSize = new System.Drawing.Size(32, 32);',
                web=f'button {{\n  min-width: 32px;\n  min-height: 32px;\n  padding: 8px 12px;\n}}'
            )
            return {
                "issue_type": "Target Size Below Recommendation (WCAG 2.5.8 / 2.5.5)",
                "short_description": f"The interactive bounding box of {control_type} is smaller than standard touch/click guidelines.",
                "why_it_matters": (
                    "Undersized click targets cause high error rates for individuals with motor disabilities, tremors, or those "
                    "operating touchscreen laptops. Users often fail to activate the intended target or inadvertently trigger "
                    "adjacent controls."
                ),
                "recommended_fix": (
                    f"Increase the minimum clickable bounds of '{ctrl_display}' to at least 24x24 px (minimum) or 44x44 px (enhanced target size)."
                ),
                "developer_actions": [
                    "Increase control padding or set explicit MinWidth and MinHeight constraints.",
                    "Ensure adequate visual spacing (at least 8px) between adjacent interactive targets.",
                    "Verify that expanding the touch target does not clip surrounding layout elements."
                ],
                "verification_steps": [
                    "Inspect the bounding rectangle in Accessibility Insights: verify width and height meet or exceed 24x24 px.",
                    "Test activation on a touch screen or with a high-DPI mouse pointer without hitting adjacent buttons."
                ],
                "human_review_required": True,
                "limitations": "WCAG 2.5.8 provides exceptions for inline text links and user-agent default controls.",
                "code_remediation": framework_code,
            }

        # 6. Missing or Unclear Label
        elif category_key == "MISSING_UNCLEAR_LABEL":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<Label Target="{{Binding ElementName={element_name or "TargetInput"}}}" Content="Email Address:" />\n<TextBox x:Name="{element_name or "TargetInput"}" />',
                winui=f'<TextBox Header="Email Address" />',
                winforms=f'// Associate Label with input control via AccessibleName',
                web=f'<label for="inputId">Email Address</label>\n<input id="inputId" type="email" />'
            )
            return {
                "issue_type": "Missing Form Control Label (WCAG 1.3.1 / 3.3.2)",
                "short_description": f"The input or form control lacks an explicitly associated text label.",
                "why_it_matters": (
                    "Users navigating forms need clear labels describing expected inputs (e.g. 'Email address', 'Birth date'). "
                    "Without programmatic label associations, screen readers cannot announce what data the user should enter."
                ),
                "recommended_fix": (
                    f"Associate a descriptive visual label with the input control using platform labeling mechanisms (e.g. LabeledBy or Header)."
                ),
                "developer_actions": [
                    "Add an explicit visual label adjacent to the form control.",
                    "Programmatically connect the label to the control using LabeledBy or target binding.",
                    "Provide helpful placeholder or watermark text as supplementary context, not as a replacement for labels."
                ],
                "verification_steps": [
                    "Focus the input field with Windows Narrator active: ensure the prompt name is spoken before accepting text.",
                    "Verify the label remains visible when the input field contains text."
                ],
                "human_review_required": True,
                "limitations": "Visual proximity heuristic indicates likely association, but programmatic binding must be verified.",
                "code_remediation": framework_code,
            }

        # 7. Contrast Observation
        elif category_key == "CONTRAST_OBSERVATION":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<TextBlock Foreground="#FFFFFF" Background="#1E293B" /> <!-- Contrast ratio > 7:1 -->',
                winui=f'<TextBlock Foreground="{{ThemeResource TextFillColorPrimaryBrush}}" />',
                winforms=f'this.{element_name or "lbl"}.ForeColor = System.Drawing.Color.White;\nthis.{element_name or "lbl"}.BackColor = System.Drawing.Color.FromArgb(30, 41, 59);',
                web=f'color: #FFFFFF;\nbackground-color: #1E293B; /* 9.5:1 ratio */'
            )
            return {
                "issue_type": "Color Contrast Observation (WCAG 1.4.3)",
                "short_description": f"The estimated or measured text contrast ratio falls below the 4.5:1 threshold (or 3.0:1 for large text).",
                "why_it_matters": (
                    "Low visual contrast impedes text readability for people with low vision, color blindness, aging eyes, or "
                    "anyone using screens in bright outdoor environments."
                ),
                "recommended_fix": (
                    f"Adjust foreground text color or background surface color on '{ctrl_display}' to achieve at least a 4.5:1 contrast ratio."
                ),
                "developer_actions": [
                    "Sample the RGB color values of the text glyphs and background surface.",
                    "Adjust text darkness or surface brightness to reach minimum 4.5:1 contrast (or 7:1 for AAA).",
                    "Support Windows High Contrast Mode themes (Contrast Black, Contrast White)."
                ],
                "verification_steps": [
                    "Use a color contrast analyzer tool on the rendered screen pixels.",
                    "Enable Windows High Contrast Mode (Left Alt + Left Shift + PrintScreen) to verify legibility across high-contrast themes."
                ],
                "human_review_required": True,
                "limitations": "Pixel sampling on rendered gradients or font anti-aliasing can produce variations; human color inspection confirms true contrast.",
                "code_remediation": framework_code,
            }

        # 8. Focus State Observation
        elif category_key == "FOCUS_STATE_OBSERVATION" or category_key == "FOCUS_STATE_UNCERTAINTY":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<Style TargetType="Button">\n    <Setter Property="FocusVisualStyle">\n        <Setter.Value>\n            <Style>\n                <Setter Property="Control.Template">\n                    <Setter.Value>\n                        <ControlTemplate>\n                            <Rectangle Stroke="#38BDF8" StrokeThickness="2" StrokeDashArray="1 2" Margin="-2"/>\n                        </ControlTemplate>\n                    </Setter.Value>\n                </Setter>\n            </Style>\n        </Setter.Value>\n    </Setter>\n</Style>',
                winui=f'<Button FocusVisualPrimaryBrush="#38BDF8" FocusVisualPrimaryThickness="2" />',
                winforms=f'// Handle Paint event to draw focus rectangle when control.Focused == true',
                web=f'button:focus-visible {{\n  outline: 2px solid #38BDF8;\n  outline-offset: 2px;\n}}'
            )
            return {
                "issue_type": "Focus State Visibility / Uncertainty (WCAG 2.4.7)",
                "short_description": f"The active focus state on {control_type} may lack a distinct, high-contrast visual indicator or could not be reliably verified via UI Automation.",
                "why_it_matters": (
                    "Users navigating via keyboard must know which control currently possesses input focus at all times. "
                    "When focus outlines are suppressed or low-contrast, keyboard navigation becomes unusable."
                ),
                "recommended_fix": (
                    f"Ensure '{ctrl_display}' renders a prominent, high-contrast visible focus rectangle when focused and correctly exposes focus state to UI Automation."
                ),
                "developer_actions": [
                    "Never suppress default focus rings (e.g. avoid outline: none without replacing it).",
                    "Provide a focus outline with at least 3:1 contrast against adjacent colors and 2px thickness.",
                    "Ensure custom controls raise standard UIA AutomationFocusChanged events."
                ],
                "verification_steps": [
                    "Tab into the element with the keyboard and verify that the focus indicator is clearly distinguishable.",
                    "Verify with Windows Narrator or Inspect.exe that HasKeyboardFocus is True.",
                    "Test across all application theme modes (dark, light, high-contrast)."
                ],
                "human_review_required": True,
                "limitations": "Focus state appearance requires interactive visual inspection; automated signals flag unverified or suppressed focus indicators.",
                "code_remediation": framework_code,
            }

        # 9. Potential Keyboard Focus Trap (WCAG 2.1.2)
        elif category_key == "POTENTIAL_FOCUS_TRAP":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<!-- Ensure container allows Tab traversal continuation -->\n<Grid KeyboardNavigation.TabNavigation="Continue">\n    <!-- Child controls -->\n</Grid>',
                winui=f'<!-- Ensure container does not trap focus unless explicitly in a modal dialog -->\n<StackPanel XYFocusKeyboardNavigation="Enabled" />',
                winforms=f'// Handle KeyDown event to allow Escape or forward Tab to advance focus\nif (e.KeyCode == Keys.Escape) {{ this.Parent.Focus(); }}',
                web=f'// Release trap or support Escape key:\nelement.addEventListener("keydown", (e) => {{\n  if (e.key === "Escape") {{ closeModal(); }}\n}});'
            )
            return {
                "issue_type": "Potential Keyboard Focus Trap (WCAG 2.1.2)",
                "short_description": "Keyboard focus entered a subset of controls and could not escape using standard Tab navigation.",
                "why_it_matters": (
                    "If keyboard focus becomes confined to a sub-region with no exit route, keyboard-only users become stuck "
                    "and cannot navigate to the rest of the application without using a mouse."
                ),
                "recommended_fix": (
                    "Verify whether keyboard focus can intentionally enter and exit this region. If this is a modal dialog, provide "
                    "a clear Escape key exit handler. For standard containers, ensure Tab navigation continues to subsequent controls."
                ),
                "developer_actions": [
                    "Reproduce the keyboard navigation sequence using Tab and Shift+Tab.",
                    "Determine whether the containment is an intentional modal dialog or an accidental focus loop.",
                    "Ensure pressing Tab on the last element in a non-modal container advances focus to the next control.",
                    "For modal dialogs, implement an Escape key handler to close the dialog and restore focus to the triggering element."
                ],
                "verification_steps": [
                    "Navigate through the container using Tab until the last child control is reached.",
                    "Press Tab again and verify focus advances outside the container (or cycles cleanly in an approved modal).",
                    "Press Escape in modal contexts to verify focus returns to the primary workspace.",
                    "Test with keyboard-only navigation without touching the mouse."
                ],
                "human_review_required": True,
                "limitations": "Focus containment can be intentional in modal dialogs; human review is required to verify design intent.",
                "code_remediation": framework_code,
            }

        # 10. Unexpected Focus Loop
        elif category_key == "UNEXPECTED_FOCUS_LOOP":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<!-- Configure container navigation mode to Continue rather than Cycle -->\nKeyboardNavigation.SetTabNavigation(container, KeyboardNavigationMode.Continue);',
                winui=f'<!-- Allow focus progression past container -->\n<ItemsControl TabNavigation="Local" />',
                winforms=f'// Ensure Form or Panel does not intercept Tab keys improperly\nthis.KeyPreview = false;',
                web=f'// Ensure focus can leave component:\nlastElement.addEventListener("keydown", (e) => {{\n  if (e.key === "Tab" && !e.shiftKey) {{ nextSection.focus(); }}\n}});'
            )
            return {
                "issue_type": "Unexpected Keyboard Focus Loop (WCAG 2.4.3)",
                "short_description": "Keyboard focus repeatedly cycled through the same controls rather than progressing forward.",
                "why_it_matters": (
                    "Unintended focus loops force users into circular navigation, creating confusion and making content "
                    "outside the loop unreachable via standard sequential keyboard navigation."
                ),
                "recommended_fix": (
                    "Configure container controls to allow focus to exit once the last child element has been tabbed past."
                ),
                "developer_actions": [
                    "Inspect the container's tab navigation mode (e.g. Continue vs Cycle).",
                    "Verify whether child controls inadvertently cycle focus internally.",
                    "Ensure subsequent interactive sections have valid IsTabStop and TabIndex properties."
                ],
                "verification_steps": [
                    "Tab through all elements in the container and confirm focus advances to the next logical section.",
                    "Reverse tab using Shift+Tab and confirm focus moves backward to the previous section."
                ],
                "human_review_required": True,
                "limitations": "Cyclical navigation is acceptable inside certain widget patterns (e.g. tab strips, carousels); human verification determines appropriateness.",
                "code_remediation": framework_code,
            }

        # 11. Unreached Interactive Element
        elif category_key == "UNREACHED_INTERACTIVE_ELEMENT":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<!-- Include element in tab sequence -->\n<{ctrl_display} IsTabStop="True" TabIndex="5" />',
                winui=f'<!-- Ensure control is keyboard focusable and tab stop -->\n<{ctrl_display} IsTabStop="True" />',
                winforms=f'this.{element_name or "control"}.TabStop = true;\nthis.{element_name or "control"}.TabIndex = 5;',
                web=f'<{ctrl_display} tabindex="0">{element_name or "Interactive Control"}</{ctrl_display}>'
            )
            return {
                "issue_type": "Interactive Element Not Observed During Traversal (WCAG 2.1.1)",
                "short_description": f"The interactive {control_type} was not observed during controlled keyboard Tab traversal.",
                "why_it_matters": (
                    "Interactive controls that are not observed during sequential Tab traversal may be unavailable to keyboard-only "
                    "navigators, or may rely on arrow keys or custom shortcuts."
                ),
                "recommended_fix": (
                    f"Verify whether '{ctrl_display}' should be included in the primary Tab order by verifying its TabStop / tabindex property and visibility state."
                ),
                "developer_actions": [
                    f"Verify whether '{ctrl_display}' has IsTabStop=True (WPF/WinUI) or tabindex=\"0\" (Web).",
                    "Check if the element is inside a collapsed, disabled, or hidden container.",
                    "If custom navigation (such as Arrow keys) is used instead of Tab, document the expected shortcut keys."
                ],
                "verification_steps": [
                    "Navigate the full view using Tab and verify that this element receives focus.",
                    "Confirm the element displays a visible focus indicator upon landing.",
                    "Activate the element using Space or Enter to confirm full keyboard operability."
                ],
                "human_review_required": True,
                "limitations": "Elements in collapsed menus, conditional views, or composite widgets (using arrow-key navigation) may legitimately not be observed via Tab.",
                "code_remediation": framework_code,
            }

        # 12. Focus Order vs Spatial Layout Discrepancy
        elif category_key == "FOCUS_ORDER_DISCREPANCY":
            framework_code = RemediationKnowledgeBase._resolve_code(
                framework_key=framework_key,
                wpf=f'<!-- Align XAML visual order with logical reading order -->\n<StackPanel Orientation="Vertical">\n    <Button Content="Step 1" TabIndex="1" />\n    <Button Content="Step 2" TabIndex="2" />\n</StackPanel>',
                winui=f'<!-- Ensure tab sequence matches visual reading order -->\n<Button TabIndex="1" />',
                winforms=f'// Set sequential tab index matching top-to-bottom layout\nthis.btn1.TabIndex = 1;\nthis.btn2.TabIndex = 2;',
                web=f'<!-- Ensure DOM order matches visual CSS layout (avoid arbitrary positive tabindex) -->\n<div class="form-row">\n  <input type="text" />\n</div>'
            )
            return {
                "issue_type": "Focus Sequence / Spatial Order Discrepancy (WCAG 2.4.3)",
                "short_description": "Keyboard focus order differs significantly from the visual top-to-bottom, left-to-right reading order.",
                "why_it_matters": (
                    "When focus jumps unexpectedly across different screen regions instead of following the natural visual layout, "
                    "sighted keyboard users and screen magnification users can become disoriented."
                ),
                "recommended_fix": (
                    "Reorder elements in the visual or markup tree to match the logical reading sequence, or adjust TabIndex properties."
                ),
                "developer_actions": [
                    "Compare the visual layout with the observed Tab traversal path.",
                    "Avoid arbitrary TabIndex values that override natural DOM / markup order.",
                    "Align markup hierarchy with visual presentation to maintain intuitive reading flow."
                ],
                "verification_steps": [
                    "Navigate sequentially through the view using Tab.",
                    "Verify that the focus indicator progresses predictably in a natural reading direction."
                ],
                "human_review_required": True,
                "limitations": "Visual order is an investigative heuristic; certain non-linear forms have intentional logical order that differs from simple spatial layout.",
                "code_remediation": framework_code,
            }

        # 9. Insufficient Evidence (Fallback)
        else:
            return {
                "issue_type": "Insufficient Evidence for Automated Conclusion",
                "short_description": "Available telemetry and accessibility metadata are insufficient for deterministic automated conclusion.",
                "why_it_matters": (
                    "Automated analysis cannot conclusively verify accessibility barriers without adequate signals. "
                    "Relying on incomplete automated data risks false positives or misleading developer guidance."
                ),
                "recommended_fix": (
                    "Perform manual accessibility inspection and user verification with assistive technologies."
                ),
                "developer_actions": [
                    "Inspect the control in Windows Accessibility Insights for Windows.",
                    "Review application source code for proper accessibility attributes.",
                    "Conduct manual keyboard and screen reader testing."
                ],
                "verification_steps": [
                    "Reproduce the user flow manually.",
                    "Test with Windows Narrator and keyboard-only navigation.",
                    "Document accessibility verification results."
                ],
                "human_review_required": True,
                "limitations": "Insufficient evidence for automated remediation — requires human verification by an accessibility QA tester.",
                "code_remediation": "Framework-specific code cannot be generated reliably from the available evidence.",
            }

    @staticmethod
    def _resolve_code(framework_key: str, wpf: str, winui: str, winforms: str, web: str) -> str:
        """Returns framework-specific code if framework is reliably known; otherwise returns agnostic message."""
        if framework_key in ["wpf"]:
            return f"// WPF / XAML Remediation:\n{wpf}"
        elif framework_key in ["winui", "uwp", "xamarin", "maui"]:
            return f"// WinUI / Windows App SDK Remediation:\n{winui}"
        elif framework_key in ["winforms", "windowsforms"]:
            return f"// Windows Forms Remediation:\n{winforms}"
        elif framework_key in ["chrome", "edge", "electron", "web", "html"]:
            return f"<!-- Web / Electron HTML Remediation: -->\n{web}"
        else:
            return "Framework-specific code cannot be generated reliably from the available evidence."


# Global knowledge base instance
remediation_knowledge_base = RemediationKnowledgeBase()

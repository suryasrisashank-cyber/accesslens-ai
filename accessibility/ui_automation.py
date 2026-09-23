"""Windows UI Automation client and element tree extractor.

Extracts real accessible control hierarchies from Windows applications
using Microsoft UIAutomation APIs with safe error handling and timeout protection.
Never invents metadata; unavailable properties remain None.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from accessibility.element_model import ElementModel, UIElementModel
from accessibility.ui_tree import UITree


class UIAutomationInspectionResult(tuple):
    """Encapsulates UI Automation extraction results while remaining unpackable as a 3-tuple."""

    def __new__(
        cls,
        window_title: str,
        app_name: str,
        elements: List[UIElementModel],
        status_message: str = "Ready",
        ui_tree: Optional[UITree] = None
    ):
        return super().__new__(cls, (window_title, app_name, elements))

    def __init__(
        self,
        window_title: str,
        app_name: str,
        elements: List[UIElementModel],
        status_message: str = "Ready",
        ui_tree: Optional[UITree] = None
    ):
        self.window_title = window_title
        self.app_name = app_name
        self.elements = elements
        self.status_message = status_message
        self.ui_tree = ui_tree or UITree(elements)


class UIAutomationClient:
    """Queries Windows UI Automation trees for target desktop windows in read-only mode."""

    def __init__(self, timeout_sec: float = 6.0):
        self.timeout_sec = timeout_sec

    def is_windows(self) -> bool:
        return sys.platform == "win32"

    def is_available(self) -> bool:
        """Verifies if Windows UI Automation assemblies are loadable on this system."""
        if not self.is_windows():
            return False
        ps_check = """
try {
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    Write-Output "AVAILABLE"
} catch {
    Write-Output "UNAVAILABLE"
}
"""
        res = self._run_powershell(ps_check)
        return bool(res and "AVAILABLE" in res)

    def list_open_windows(self) -> List[Dict[str, Any]]:
        """Enumerates visible, titled top-level windows available for accessibility inspection."""
        if not self.is_windows():
            return []

        ps_script = """
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = [System.Windows.Automation.Condition]::TrueCondition
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)

$list = @()
foreach ($w in $windows) {
    try {
        $name = $w.Current.Name
        $rect = $w.Current.BoundingRectangle
        $class = $w.Current.ClassName
        $handle = $w.Current.NativeWindowHandle
        $off = $w.Current.IsOffscreen
        $pid = $w.Current.ProcessId

        # Filter out tiny or unnamed hidden helper windows
        if ($name -and -not $off -and $rect.Width -gt 150 -and $rect.Height -gt 100) {
            $pname = ""
            try { $pname = (Get-Process -Id $pid -ErrorAction SilentlyContinue).ProcessName } catch {}

            $list += @{
                handle = $handle
                title = $name
                class_name = $class
                process_name = $pname
                bounds = @([int]$rect.X, [int]$rect.Y, [int]$rect.Width, [int]$rect.Height)
            }
        }
    } catch { }
}

$list | ConvertTo-Json -Depth 2
"""
        res = self._run_powershell(ps_script)
        if not res:
            return []

        try:
            data = json.loads(res)
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            return []
        except Exception:
            return []

    def inspect_window(
        self,
        window_handle: Optional[int] = None,
        max_elements: int = 150
    ) -> UIAutomationInspectionResult:
        """Inspects target window and extracts normalized UIElementModel list and UITree.

        Read-only inspection: does NOT click, type, or mutate the target application.
        Returns:
            UIAutomationInspectionResult (unpackable as (window_title, app_name, elements))
        """
        if not self.is_windows():
            return UIAutomationInspectionResult(
                "Non-Windows Host", "GenericApp", [],
                status_message="Windows UI Automation unavailable."
            )

        handle_filter = (
            f"$win = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]{window_handle})"
            if window_handle else """
$focus = [System.Windows.Automation.AutomationElement]::FocusedElement
if (-not $focus) { $focus = [System.Windows.Automation.AutomationElement]::RootElement }
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$cur = $focus
while ($cur -and $cur.Current.ControlType.ProgrammaticName -ne 'ControlType.Window') {
    $p = $walker.GetParent($cur)
    if (-not $p -or $p -eq [System.Windows.Automation.AutomationElement]::RootElement) { break }
    $cur = $p
}
$win = if ($cur) { $cur } else { $focus }
"""
        )

        ps_script = f"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

try {{
    {handle_filter}

    if (-not $win) {{
        Write-Output "{{\\"error\\": \\"No target window identified\\"}}"
        exit 0
    }}

    $winTitle = $win.Current.Name
    $winClass = $win.Current.ClassName
    $winRect = $win.Current.BoundingRectangle
    $winPid = $win.Current.ProcessId
    $appName = ""
    try {{ $appName = (Get-Process -Id $winPid -ErrorAction SilentlyContinue).ProcessName }} catch {{}}

    $cond = [System.Windows.Automation.Condition]::TrueCondition
    $descendants = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond)

    $items = @()
    $limit = [Math]::Min($descendants.Count, {max_elements})

    for ($i = 0; $i -lt $limit; $i++) {{
        $el = $descendants[$i]
        try {{
            $r = $el.Current.BoundingRectangle
            $cname = $el.Current.ControlType.ProgrammaticName.Replace('ControlType.', '')
            $nameVal = $el.Current.Name
            $autoId = $el.Current.AutomationId
            $className = $el.Current.ClassName

            # Value pattern extraction
            $val = $null
            try {{
                $valPat = $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                if ($valPat) {{ $val = $valPat.Current.Value }}
            }} catch {{}}

            # Supported patterns
            $pats = @()
            try {{
                $sup = $el.GetSupportedPatterns()
                foreach ($p in $sup) {{
                    $pats += $p.ProgrammaticName.Replace('Pattern.', '')
                }}
            }} catch {{}}

            $items += @{{
                id = "elem_" + $i
                name = if ([string]::IsNullOrEmpty($nameVal)) {{ $null }} else {{ $nameVal }}
                control_type = if ([string]::IsNullOrEmpty($cname)) {{ $null }} else {{ $cname }}
                automation_id = if ([string]::IsNullOrEmpty($autoId)) {{ $null }} else {{ $autoId }}
                class_name = if ([string]::IsNullOrEmpty($className)) {{ $null }} else {{ $className }}
                is_enabled = $el.Current.IsEnabled
                is_focusable = $el.Current.IsKeyboardFocusable
                is_focused = $el.Current.HasKeyboardFocus
                bounds = @([int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height)
                is_visible = -not $el.Current.IsOffscreen
                value = $val
                patterns = $pats
            }}
        }} catch {{ }}
    }}

    @{{
        window_title = $winTitle
        window_class = $winClass
        app_name = $appName
        elements = $items
    }} | ConvertTo-Json -Depth 3
}} catch {{
    Write-Output "{{\\"error\\": \\"UIA extraction exception\\"}}"
}}
"""
        raw_json = self._run_powershell(ps_script)
        if not raw_json:
            return UIAutomationInspectionResult(
                "Active Desktop", "DesktopApp", [],
                status_message="Windows UI Automation unavailable."
            )

        try:
            data = json.loads(raw_json)
            if "error" in data:
                return UIAutomationInspectionResult(
                    "Desktop", "WindowsApp", [],
                    status_message="Windows UI Automation unavailable."
                )

            win_title = data.get("window_title") or "Active Desktop Window"
            app_name = data.get("app_name") or data.get("window_class") or "WindowsApp"
            raw_elements = data.get("elements", [])

            elements: List[UIElementModel] = []
            has_missing_props = False

            for item in raw_elements:
                # Retain None when property is missing
                ename = item.get("name")
                if ename == "":
                    ename = None

                ctype = item.get("control_type")
                aid = item.get("automation_id")
                cname = item.get("class_name")
                b_raw = item.get("bounds")
                bounds = b_raw if (isinstance(b_raw, list) and len(b_raw) == 4) else None

                enabled = item.get("is_enabled")
                visible = item.get("is_visible")
                focusable = item.get("is_focusable")
                focused = item.get("is_focused")
                val = item.get("value")
                pats = item.get("patterns") or []

                if ename is None or aid is None or bounds is None:
                    has_missing_props = True

                elem = UIElementModel(
                    element_id=item.get("id", f"elem_{len(elements)}"),
                    name=ename,
                    control_type=ctype,
                    automation_id=aid,
                    class_name=cname,
                    bounds=bounds,
                    enabled=enabled,
                    visible=visible,
                    focusable=focusable,
                    focused=focused,
                    value=val,
                    text=val,
                    patterns=pats,
                    raw_data=item
                )
                elements.append(elem)

            status_msg = "Partial accessibility metadata available." if has_missing_props else "Ready"
            tree = UITree(elements)
            return UIAutomationInspectionResult(
                win_title, app_name, elements,
                status_message=status_msg,
                ui_tree=tree
            )
        except Exception:
            return UIAutomationInspectionResult(
                "Active Desktop", "DesktopApp", [],
                status_message="Windows UI Automation unavailable."
            )

    def inspect_current_window(self, max_elements: int = 150) -> UIAutomationInspectionResult:
        """Inspects the currently active or focused application window."""
        return self.inspect_window(window_handle=None, max_elements=max_elements)

    def _run_powershell(self, script_content: str) -> Optional[str]:
        """Executes a PowerShell script block safely via temporary file to prevent shell quoting bugs."""
        fd, temp_path = tempfile.mkstemp(suffix=".ps1")
        os.close(fd)

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        try:
            res = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy", "Bypass",
                    "-File", temp_path
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout_sec
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
            return None
        except Exception:
            return None
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass


# Singleton instance
ui_automation = UIAutomationClient()

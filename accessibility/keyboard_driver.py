"""Keyboard Driver abstraction for AccessLens AI (Phase 5).

Provides abstract KeyboardDriver interface, deterministic MockKeyboardDriver for unit tests,
and WindowsKeyboardDriver using native Windows user32 APIs without third-party automation dependencies.
"""

from abc import ABC, abstractmethod
import ctypes
import sys
import time
from typing import List, Optional


class KeyboardDriver(ABC):
    """Abstract interface for sending controlled keyboard inputs during accessibility audits."""

    @abstractmethod
    def focus_target_window(self, hwnd: int) -> bool:
        """Brings the target window to the foreground and verifies focus."""
        pass

    @abstractmethod
    def press_tab(self) -> bool:
        """Sends a single forward TAB keystroke to the active window."""
        pass

    @abstractmethod
    def press_shift_tab(self) -> bool:
        """Sends a single reverse SHIFT+TAB keystroke combination to the active window."""
        pass

    @abstractmethod
    def stop(self):
        """Cancels any pending driver actions."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the driver runtime is available on the current host."""
        pass

    @abstractmethod
    def get_foreground_window(self) -> Optional[int]:
        """Returns the native handle (HWND) of the currently focused foreground window."""
        pass

    @abstractmethod
    def is_window_valid(self, hwnd: int) -> bool:
        """Returns True if the target window handle remains valid and alive."""
        pass


class MockKeyboardDriver(KeyboardDriver):
    """Deterministic in-memory keyboard driver for automated testing.
    
    Guarantees zero keystrokes are sent to the desktop during unit tests.
    """

    def __init__(self, current_hwnd: int = 1001):
        self._current_hwnd = current_hwnd
        self._is_active = True
        self.recorded_actions: List[str] = []

    def focus_target_window(self, hwnd: int) -> bool:
        self.recorded_actions.append(f"focus_window_{hwnd}")
        self._current_hwnd = hwnd
        return True

    def press_tab(self) -> bool:
        if not self._is_active:
            return False
        self.recorded_actions.append("TAB")
        return True

    def press_shift_tab(self) -> bool:
        if not self._is_active:
            return False
        self.recorded_actions.append("SHIFT+TAB")
        return True

    def stop(self):
        self._is_active = False
        self.recorded_actions.append("STOP")

    def is_available(self) -> bool:
        return True

    def get_foreground_window(self) -> Optional[int]:
        return self._current_hwnd

    def is_window_valid(self, hwnd: int) -> bool:
        return hwnd > 0 and self._is_active


class WindowsKeyboardDriver(KeyboardDriver):
    """Windows-native keyboard driver using built-in user32 APIs via ctypes.
    
    Zero third-party library dependencies (no pyautogui, no pynput).
    Strictly restricted to TAB and SHIFT+TAB keystrokes.
    """

    VK_TAB = 0x09
    VK_SHIFT = 0x10
    KEYEVENTF_KEYUP = 0x0002

    def __init__(self):
        self._is_windows = sys.platform == "win32"
        self._user32 = ctypes.windll.user32 if self._is_windows else None
        self._target_hwnd: Optional[int] = None

    def is_available(self) -> bool:
        return self._is_windows and self._user32 is not None

    def get_foreground_window(self) -> Optional[int]:
        if not self.is_available():
            return None
        try:
            hwnd = self._user32.GetForegroundWindow()
            return int(hwnd) if hwnd else None
        except Exception:
            return None

    def is_window_valid(self, hwnd: int) -> bool:
        if not self.is_available() or not hwnd:
            return False
        try:
            return bool(self._user32.IsWindow(hwnd))
        except Exception:
            return False

    def focus_target_window(self, hwnd: int) -> bool:
        if not self.is_available() or not self.is_window_valid(hwnd):
            return False
        try:
            self._target_hwnd = hwnd
            self._user32.SetForegroundWindow(hwnd)
            time.sleep(0.08)  # Brief pause for OS focus handoff
            fg = self.get_foreground_window()
            return fg == hwnd
        except Exception:
            return False

    def release_all_modifiers(self):
        """Unconditionally releases VK_TAB and VK_SHIFT to prevent stuck keys."""
        if self.is_available():
            try:
                self._user32.keybd_event(self.VK_TAB, 0, self.KEYEVENTF_KEYUP, 0)
            except Exception:
                pass
            try:
                self._user32.keybd_event(self.VK_SHIFT, 0, self.KEYEVENTF_KEYUP, 0)
            except Exception:
                pass

    def press_tab(self) -> bool:
        """Sends a single controlled Tab press with guaranteed key-up release."""
        if not self.is_available():
            return False
        try:
            self._user32.keybd_event(self.VK_TAB, 0, 0, 0)
            time.sleep(0.02)
            return True
        except Exception:
            return False
        finally:
            try:
                self._user32.keybd_event(self.VK_TAB, 0, self.KEYEVENTF_KEYUP, 0)
            except Exception:
                pass

    def press_shift_tab(self) -> bool:
        """Sends a single controlled Shift+Tab combination with guaranteed key-up release."""
        if not self.is_available():
            return False
        shift_down = False
        tab_down = False
        try:
            self._user32.keybd_event(self.VK_SHIFT, 0, 0, 0)
            shift_down = True
            time.sleep(0.01)
            self._user32.keybd_event(self.VK_TAB, 0, 0, 0)
            tab_down = True
            time.sleep(0.02)
            return True
        except Exception:
            return False
        finally:
            if tab_down:
                try:
                    self._user32.keybd_event(self.VK_TAB, 0, self.KEYEVENTF_KEYUP, 0)
                except Exception:
                    pass
            if shift_down:
                try:
                    self._user32.keybd_event(self.VK_SHIFT, 0, self.KEYEVENTF_KEYUP, 0)
                except Exception:
                    pass

    def stop(self):
        """Release any potentially stuck keys safely."""
        self.release_all_modifiers()

    def __del__(self):
        """Destructor to ensure modifier keys are never left pressed on process cleanup."""
        self.release_all_modifiers()

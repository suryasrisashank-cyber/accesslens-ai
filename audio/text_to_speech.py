"""Local Text-To-Speech engine for VisionVoice AI.

Provides on-device voice narration using Windows native System.Speech synthesis.
Runs asynchronously without blocking the desktop UI and supports instant cancellation.
"""

import os
import subprocess
import sys
import tempfile
import threading
from typing import Callable, Optional


class TextToSpeechEngine:
    """Windows on-device text-to-speech engine with stop/pause control."""

    def __init__(self):
        self._current_process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._is_speaking: bool = False
        self._rate: int = 1  # -10 to 10
        self._volume: int = 90  # 0 to 100
        self._current_temp_script: Optional[str] = None

    @property
    def is_speaking(self) -> bool:
        with self._lock:
            if self._current_process is not None:
                poll = self._current_process.poll()
                self._is_speaking = (poll is None)
            return self._is_speaking

    def set_rate(self, rate: int):
        """Sets speech speed rate (-10 slow to +10 fast)."""
        self._rate = max(-10, min(10, rate))

    def set_volume(self, volume: int):
        """Sets speech volume (0 to 100)."""
        self._volume = max(0, min(100, volume))

    def stop(self):
        """Immediately stops any ongoing speech narration."""
        with self._lock:
            if self._current_process is not None:
                try:
                    self._current_process.terminate()
                    self._current_process.kill()
                except Exception:
                    pass
                self._current_process = None
            self._is_speaking = False
            self._cleanup_temp_script()

    def _cleanup_temp_script(self):
        if self._current_temp_script and os.path.exists(self._current_temp_script):
            try:
                os.remove(self._current_temp_script)
            except Exception:
                pass
            self._current_temp_script = None

    def speak(
        self,
        text: str,
        on_started: Optional[Callable[[], None]] = None,
        on_finished: Optional[Callable[[], None]] = None
    ):
        """Speaks the provided text asynchronously on a background thread."""
        if not text or not text.strip():
            return

        # Stop any existing playback first
        self.stop()

        def _run():
            with self._lock:
                self._is_speaking = True

            if on_started:
                try:
                    on_started()
                except Exception:
                    pass

            try:
                self._execute_sapi_speech(text)
            except Exception as e:
                print(f"[TTS Error] Speech playback encountered an issue: {e}", file=sys.stderr)
            finally:
                with self._lock:
                    self._is_speaking = False
                    self._current_process = None
                    self._cleanup_temp_script()

                if on_finished:
                    try:
                        on_finished()
                    except Exception:
                        pass

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _execute_sapi_speech(self, text: str):
        """Executes speech synthesis via a dedicated Windows PowerShell script."""
        # Sanitize text by removing double quotes or escaping
        safe_text = text.replace('"', '""').replace("`", "``")

        ps_script_content = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = {self._rate}
$synth.Volume = {self._volume}
$text = @"
{safe_text}
"@
$synth.Speak($text)
"""
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as f:
            f.write(ps_script_content)
            temp_path = f.name

        with self._lock:
            self._current_temp_script = temp_path

        cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-File", temp_path
        ]

        # Hide window on Windows
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        with self._lock:
            self._current_process = proc

        proc.wait()


# Global singleton instance
tts_engine = TextToSpeechEngine()

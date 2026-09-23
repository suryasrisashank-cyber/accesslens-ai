"""Prompt Injection & Adversarial Text Guard for AccessLens AI.

Ensures that UI text and OCR detections are treated strictly as passive,
untrusted evidence data. Never executes or allows UI strings to hijack reasoning rules.
"""

from typing import Optional
from ai.finding_context import FindingContextBuilder


class PromptGuard:
    """Security guard identifying untrusted and adversarial prompt injection strings."""

    @staticmethod
    def is_suspicious_text(text: Optional[str]) -> bool:
        """Determines if text contains instruction-like phrases or override attempts."""
        return FindingContextBuilder.detect_suspicious_text(text)

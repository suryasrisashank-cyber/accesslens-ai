"""Sensitive Data Detection & Redaction Engine for AccessLens AI (Phase 7).

Scans OCR text, element names, and accessibility properties for potential
credentials, API tokens, payment card sequences, emails, and phone numbers.
Applies conservative redaction safeguards prior to export while acknowledging
that automated heuristic pattern matching is not an absolute PII guarantee.
"""

import re
from typing import Any, Dict, List, Tuple


class SensitiveDataDetector:
    """Heuristic scanner and redactor for potential sensitive content in audit evidence."""

    NOTICE_POTENTIAL_SENSITIVE = (
        "Potential sensitive content detected; review before export."
    )
    LIMITATION_DISCLAIMER = (
        "Automated sensitive content detection is a heuristic safeguard designed to "
        "assist privacy reviews. It does not claim or guarantee 100% identification "
        "of all personally identifiable information or proprietary secrets."
    )

    def __init__(self):
        # Compiled patterns: (pattern_name, regex, replacement_token)
        self._patterns: List[Tuple[str, re.Pattern, str]] = [
            (
                "PAYMENT_CARD",
                re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
                "[REDACTED_PAYMENT_CARD]",
            ),
            (
                "EMAIL_ADDRESS",
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
                "[REDACTED_EMAIL]",
            ),
            (
                "PHONE_NUMBER",
                re.compile(
                    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
                ),
                "[REDACTED_PHONE]",
            ),
            (
                "API_OR_CREDENTIAL_KEY",
                re.compile(
                    r"(?:api[_-]?key|secret|token|password|bearer)[\s:=]+['\"]?([A-Za-z0-9_\-\.]{12,})['\"]?",
                    re.IGNORECASE,
                ),
                "[REDACTED_CREDENTIAL]",
            ),
            (
                "USER_FILE_PATH",
                re.compile(
                    r"(?:[A-Za-z]:\\Users\\[^\s\\/]+|/home/[^\s/]+)",
                    re.IGNORECASE,
                ),
                "[REDACTED_PATH]",
            ),
        ]

    def scan_text(self, text: str) -> List[Dict[str, Any]]:
        """Scans string for potential sensitive patterns and returns findings list."""
        if not text or not isinstance(text, str):
            return []

        findings: List[Dict[str, Any]] = []
        for name, pattern, _ in self._patterns:
            for match in pattern.finditer(text):
                findings.append({
                    "pattern_type": name,
                    "matched_sample": match.group(0)[:12] + "..." if len(match.group(0)) > 12 else match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                })
        return findings

    def contains_sensitive_content(self, text: str) -> bool:
        """Returns True if any sensitive pattern matches."""
        return len(self.scan_text(text)) > 0

    def redact_text(self, text: str) -> str:
        """Conservatively masks credentials, phone numbers, payment cards, emails, and user paths."""
        if not text or not isinstance(text, str):
            return text or ""

        redacted = text
        for _, pattern, token in self._patterns:
            redacted = pattern.sub(token, redacted)
        return redacted

    def sanitize_dictionary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively applies redaction to string values in a dictionary."""
        sanitized: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self.redact_text(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dictionary(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.redact_text(v) if isinstance(v, str)
                    else (self.sanitize_dictionary(v) if isinstance(v, dict) else v)
                    for v in value
                ]
            else:
                sanitized[key] = value
        return sanitized


# Global singleton instance
sensitive_data_detector = SensitiveDataDetector()

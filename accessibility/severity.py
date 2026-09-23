"""Severity model for AccessLens AI accessibility findings.

Defines standard severity ratings: INFO, LOW, MEDIUM, HIGH, and CRITICAL.
Severity reflects potential accessibility impact on users, distinct from confidence.
"""

from enum import Enum


class FindingSeverity(str, Enum):
    """WCAG and accessibility severity levels."""
    INFO = "INFO"           # Informational observation or best practice advice
    LOW = "LOW"             # Minor advisory or minor usability friction
    MEDIUM = "MEDIUM"       # WCAG AA deviation or moderate accessibility barrier
    HIGH = "HIGH"           # Significant barrier preventing standard assistive interaction
    CRITICAL = "CRITICAL"   # Total blocker for screen readers or keyboard navigation (requires deterministic proof)


Severity = FindingSeverity


def describe_severity(severity: FindingSeverity) -> str:
    """Returns human-readable explanation of severity tier."""
    descriptions = {
        FindingSeverity.INFO: "Informational: Good practice suggestion or system observation.",
        FindingSeverity.LOW: "Low impact: Minor inconvenience; workaround available.",
        FindingSeverity.MEDIUM: "Medium impact: WCAG 2.1 AA deviation affecting specific assistive tools.",
        FindingSeverity.HIGH: "High impact: Serious barrier significantly impeding interaction.",
        FindingSeverity.CRITICAL: "Critical: Complete blocker preventing task completion for assistive users."
    }
    return descriptions.get(severity, "Unclassified severity level.")

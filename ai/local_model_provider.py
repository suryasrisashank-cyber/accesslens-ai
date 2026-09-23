"""Local model provider abstraction and deterministic reasoning engine for AccessLens AI.

Provides the LocalModelProvider interface supporting:
- RULE_BASED_LOCAL (deterministic rule-based reasoning engine on CPU)
- ONNX_LOCAL (extensible for on-device quantized ONNX models)
- QNN_LOCAL (extensible for Snapdragon Hexagon NPU via QNN Execution Provider)
- UNAVAILABLE

On current AMD Ryzen development hardware, operates honestly via RULE_BASED_LOCAL on CPU
with zero simulated NPU claims and zero cloud dependencies.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from ai.finding_context import FindingContextBuilder
from ai.reasoning_models import ReasoningResult
from ai.remediation_knowledge import remediation_knowledge_base


class ProviderState(str, Enum):
    """Available runtime states for local AI reasoning."""
    RULE_BASED_LOCAL = "RULE_BASED_LOCAL"
    ONNX_LOCAL = "ONNX_LOCAL"
    QNN_LOCAL = "QNN_LOCAL"
    UNAVAILABLE = "UNAVAILABLE"


class LocalModelProvider(ABC):
    """Abstract interface for local accessibility reasoning providers."""

    @property
    @abstractmethod
    def provider_state(self) -> ProviderState:
        """Returns the current operational state of the provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns whether the provider is currently initialized and operational."""
        pass

    @abstractmethod
    def model_info(self) -> Dict[str, Any]:
        """Returns honest metadata describing the reasoning engine and runtime."""
        pass

    @abstractmethod
    def generate_reasoning(self, context: Dict[str, Any]) -> ReasoningResult:
        """Generates evidence-grounded explanation and remediation from finding context."""
        pass

    @abstractmethod
    def generate_remediation(self, context: Dict[str, Any]) -> ReasoningResult:
        """Generates actionable developer remediation guidance and code."""
        pass


class RuleBasedReasoningEngine(LocalModelProvider):
    """Built-in deterministic local reasoning engine.
    
    Operates 100% locally on CPU using structured accessibility knowledge.
    Does not require generative model weights or cloud endpoints.
    """

    def __init__(self):
        self._provider_state = ProviderState.RULE_BASED_LOCAL

    @property
    def provider_state(self) -> ProviderState:
        return self._provider_state

    def is_available(self) -> bool:
        return True

    def model_info(self) -> Dict[str, Any]:
        return {
            "model_name": "AccessLens Rule-Based Remediation Engine",
            "model_version": "1.0",
            "provider": ProviderState.RULE_BASED_LOCAL.value,
            "task": "Accessibility reasoning & developer remediation",
            "source": "AccessLens AI Local-First Architecture",
            "runtime": "CPU",
            "execution_provider": "CPUExecutionProvider",
            "verification_status": "Verified (Local CPU)",
            "local_only": True,
            "availability": True,
            "description": "Deterministic, evidence-grounded accessibility reasoning and remediation engine.",
        }

    def generate_reasoning(self, context: Dict[str, Any]) -> ReasoningResult:
        """Produces a structured explanation of the finding grounded strictly in evidence."""
        return self._synthesize_result(context, is_remediation_focused=False)

    def generate_remediation(self, context: Dict[str, Any]) -> ReasoningResult:
        """Produces actionable developer remediation steps and verification checklists."""
        return self._synthesize_result(context, is_remediation_focused=True)

    def _synthesize_result(self, context: Dict[str, Any], is_remediation_focused: bool) -> ReasoningResult:
        finding_id = context.get("finding_id", "unknown_finding")
        title = context.get("title", "")
        category = context.get("category", "")
        severity = context.get("severity", "MEDIUM")
        confidence = context.get("confidence", 0.8)
        element_data = context.get("element", {}) or {}
        evidence_items = context.get("evidence", []) or []
        evidence_ids = context.get("evidence_ids", []) or []
        detected_framework = context.get("detected_framework")
        is_suspicious = context.get("is_untrusted_instruction_detected", False)

        ctrl_name = element_data.get("name", "")
        ctrl_type = element_data.get("control_type", "Element")

        # Prompt injection protection: If the control name itself is adversarial, use sanitized reference for recommendations
        sanitized_ctrl_name = ctrl_name
        if is_suspicious and FindingContextBuilder.detect_suspicious_text(ctrl_name):
            sanitized_ctrl_name = f"{ctrl_type} (untrusted content)"

        # Determine Defect Category Key
        cat_key = self._classify_defect_category(title, category, evidence_items, element_data)

        # Retrieve structured guidance from Knowledge Base
        guidance = remediation_knowledge_base.get_category_guidance(
            category_key=cat_key,
            element_name=sanitized_ctrl_name,
            control_type=ctrl_type,
            detected_framework=detected_framework,
            context_details=context,
        )

        # Build Grounded Evidence Summary
        if not evidence_items:
            evidence_summary = (
                "No explicit evidence items were captured for this finding. "
                "The observation relies on basic element properties."
            )
        else:
            evidence_lines = []
            for ev in evidence_items:
                ev_id = ev.get("evidence_id", "ev")
                sig_type = ev.get("signal_type", "DETECTED")
                desc = ev.get("description", "")
                evidence_lines.append(f"[{sig_type}] ({ev_id}): {desc}")
            evidence_summary = "\n".join(evidence_lines)

        # Build Confidence Explanation
        confidence_explanation = self._explain_confidence(confidence, evidence_items, cat_key)

        # Build Summary
        summary = (
            f"AccessLens evaluated '{sanitized_ctrl_name or ctrl_type}' ({ctrl_type}) and identified: {title}. "
            f"Severity evaluated as {severity} with confidence {confidence * 100:.0f}%. "
            f"{guidance['short_description']}"
        )

        limitations = guidance.get("limitations", "")
        if is_suspicious:
            limitations += (
                " [SECURITY NOTE: Adversarial or instruction-like text patterns were detected in the interface data. "
                "All UI/OCR strings were strictly isolated as passive data to prevent prompt override.]"
            )

        # Build remediation text with code snippet
        code_part = guidance.get("code_remediation", "")
        remediation_text = guidance["recommended_fix"]
        if code_part:
            remediation_text += f"\n\nImplementation:\n{code_part}"

        return ReasoningResult(
            finding_id=finding_id,
            summary=summary,
            why_it_matters=guidance["why_it_matters"],
            evidence_summary=evidence_summary,
            confidence_explanation=confidence_explanation,
            remediation=remediation_text,
            developer_actions=guidance["developer_actions"],
            verification_steps=guidance["verification_steps"],
            limitations=limitations,
            human_verification_required=True,  # Always mandatory
            evidence_references=evidence_ids,
            generated_by="Deterministic Local Reasoning",
            model_name="AccessLens Rule-Based Remediation Engine",
            model_version="1.0",
            runtime="CPU",
        )

    def _classify_defect_category(
        self,
        title: str,
        category: str,
        evidence: List[Dict[str, Any]],
        element: Dict[str, Any],
    ) -> str:
        """Maps finding title, category, and evidence to one of the 9 defect keys."""
        t_low = title.lower()
        c_low = category.lower()

        # Check for insufficient evidence first
        if "insufficient" in t_low or (not evidence and not element.get("name") and not element.get("control_type")):
            return "INSUFFICIENT_EVIDENCE"

        if "trap" in t_low:
            return "POTENTIAL_FOCUS_TRAP"
        if "focus loop" in t_low or "cyclical" in t_low:
            return "UNEXPECTED_FOCUS_LOOP"
        if "not reached" in t_low or "unreached" in t_low:
            return "UNREACHED_INTERACTIVE_ELEMENT"
        if "spatial order" in t_low or "focus sequence" in t_low or "order discrepancy" in t_low:
            return "FOCUS_ORDER_DISCREPANCY"
        if "focus state" in t_low or "focus uncertain" in t_low:
            return "FOCUS_STATE_UNCERTAINTY"
        if "missing accessible name" in t_low or ("label" in c_low and "missing" in t_low and "name" in t_low):
            return "MISSING_ACCESSIBLE_NAME"
        if "semantic" in t_low or "role" in t_low:
            return "SEMANTIC_MISMATCH"
        if "mismatch" in t_low or "discrepancy" in t_low or ("visible" in t_low and "name" in t_low):
            return "NAME_MISMATCH"
        if "focusable" in t_low or "keyboard" in c_low or "tab" in t_low:
            return "FOCUSABILITY_ISSUE"
        if "size" in t_low or "target" in t_low or "bounds" in t_low:
            return "INTERACTIVE_REGION_SIZE"
        if "form" in t_low or "label" in t_low and "unclear" in t_low or "input" in t_low:
            return "MISSING_UNCLEAR_LABEL"
        if "contrast" in t_low or "color" in c_low or "luminance" in t_low:
            return "CONTRAST_OBSERVATION"
        if "focus indicator" in t_low:
            return "FOCUS_STATE_OBSERVATION"

        # Category based fallback
        if "label" in c_low or "name" in c_low:
            return "MISSING_ACCESSIBLE_NAME"
        if "contrast" in c_low:
            return "CONTRAST_OBSERVATION"
        if "keyboard" in c_low:
            return "FOCUSABILITY_ISSUE"
        if "target" in c_low or "size" in c_low:
            return "INTERACTIVE_REGION_SIZE"

        return "INSUFFICIENT_EVIDENCE"

    def _explain_confidence(
        self,
        confidence: float,
        evidence_items: List[Dict[str, Any]],
        cat_key: str,
    ) -> str:
        """Generates evidence-grounded explanation for the confidence score."""
        num_signals = len(evidence_items)
        has_measured = any(e.get("signal_type") == "MEASURED" for e in evidence_items)
        has_detected = any(e.get("signal_type") == "DETECTED" for e in evidence_items)

        if confidence >= 0.90:
            if has_measured:
                return (
                    f"Confidence is high ({confidence * 100:.0f}%) because the finding is grounded in mathematically "
                    f"measured properties (such as pixel bounds or contrast ratios) directly from interface telemetry."
                )
            elif has_detected:
                return (
                    f"Confidence is high ({confidence * 100:.0f}%) because the programmatic attribute was directly detected "
                    f"from the Windows UI Automation accessibility tree."
                )
            else:
                return (
                    f"Confidence is high ({confidence * 100:.0f}%) based on concordant structural signals across the element tree."
                )
        elif confidence >= 0.70:
            return (
                f"Confidence is moderate ({confidence * 100:.0f}%) based on {num_signals} observed signal(s). "
                "Visual or structural heuristics suggest an accessibility barrier, but contextual verification is recommended."
            )
        else:
            return (
                f"Confidence is low ({confidence * 100:.0f}%) due to limited or ambiguous evidence signals. "
                "Human QA testing is required to confirm whether this affects assistive technology users."
            )


# Global default local model provider instance
local_model_provider = RuleBasedReasoningEngine()

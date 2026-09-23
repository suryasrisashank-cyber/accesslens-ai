"""Model registry for AccessLens AI.

Tracks all AI models with comprehensive metadata, licenses, sources,
supported execution providers (CPU / Snapdragon QNN), precision, and
honest verification status.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ModelMetadata:
    name: str
    task: str
    format: str
    runtime: str
    license: str
    source: str
    target: str
    cpu_supported: bool
    qnn_supported: bool
    verification_status: str
    description: str = ""
    parameters_or_size: str = ""
    notes: str = ""
    provider: str = "AccessLens"
    local_only: bool = True
    model_name: str = ""
    model_version: str = "1.0.0"
    precision: str = "FP32"
    target_hardware: str = "Local CPU"
    execution_provider: str = "CPUExecutionProvider"

    def __post_init__(self):
        if not self.model_name:
            self.model_name = self.name


class ModelRegistry:
    """Model Registry & Hardware Verification catalog for AccessLens AI."""

    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._register_default_models()

    def _register_default_models(self):
        # 1. OCR Text Detector
        self.register(ModelMetadata(
            name="ch_PP-OCRv4_det",
            model_name="ch_PP-OCRv4_det",
            model_version="4.0.0",
            task="Optical Character Recognition (Text Detection)",
            format="ONNX",
            runtime="ONNX Runtime (CPU / QNN)",
            precision="FP32",
            target_hardware="Local CPU (x64 / ARM64)",
            execution_provider="CPUExecutionProvider",
            license="Apache-2.0",
            source="PaddleOCR / RapidOCR (Baidu & Open Source Community)",
            target="Text bounding box localization on screen content",
            cpu_supported=True,
            qnn_supported=True,
            verification_status="Verified on current AMD CPU development host (verified_on_current_host)",
            description="Ultra-lightweight DBNet text detector optimized for low latency on edge devices.",
            parameters_or_size="4.7 MB",
            notes="Deployable to Qualcomm Hexagon NPU via INT8/FP16 quantization."
        ))

        # 2. OCR Text Classifier
        self.register(ModelMetadata(
            name="ch_ppocr_mobile_v2.0_cls",
            model_name="ch_ppocr_mobile_v2.0_cls",
            model_version="2.0.0",
            task="Text Direction Classification (Orientation)",
            format="ONNX",
            runtime="ONNX Runtime (CPU / QNN)",
            precision="FP32",
            target_hardware="Local CPU (x64 / ARM64)",
            execution_provider="CPUExecutionProvider",
            license="Apache-2.0",
            source="PaddleOCR / RapidOCR",
            target="Text box orientation normalization (0/180 deg)",
            cpu_supported=True,
            qnn_supported=True,
            verification_status="Verified on current AMD CPU development host (verified_on_current_host)",
            description="MobileNet-based lightweight classifier for rotated text regions.",
            parameters_or_size="1.4 MB",
            notes="Fast pre-processing step for vertical and angled computer text."
        ))

        # 3. OCR Text Recognizer
        self.register(ModelMetadata(
            name="ch_PP-OCRv4_rec",
            model_name="ch_PP-OCRv4_rec",
            model_version="4.0.0",
            task="Text Recognition (Character Sequence Decoding)",
            format="ONNX",
            runtime="ONNX Runtime (CPU / QNN)",
            precision="FP32",
            target_hardware="Local CPU (x64 / ARM64)",
            execution_provider="CPUExecutionProvider",
            license="Apache-2.0",
            source="PaddleOCR / RapidOCR",
            target="Image to sequence text extraction",
            cpu_supported=True,
            qnn_supported=True,
            verification_status="Verified on current AMD CPU development host (verified_on_current_host)",
            description="SVTR sequence recognition model with high accuracy on document & web fonts.",
            parameters_or_size="10.8 MB",
            notes="Full English, numeric, and international symbol support."
        ))

        # 4. Multimodal UI & Layout Feature Analyzer
        self.register(ModelMetadata(
            name="VisionVoice-LayoutAnalyzer-v1",
            model_name="VisionVoice-LayoutAnalyzer-v1",
            model_version="1.0.0",
            task="Document & UI Semantic Layout Segmentation",
            format="ONNX / Python Native Heuristics",
            runtime="ONNX Runtime / Local Rule Engine",
            precision="FP32",
            target_hardware="Local CPU (x64 / ARM64)",
            execution_provider="CPUExecutionProvider",
            license="MIT",
            source="AccessLens AI On-Device Pipeline",
            target="Semantic classification (Webpage, Document, Menu, Code, Form)",
            cpu_supported=True,
            qnn_supported=True,
            verification_status="Verified on current AMD CPU development host (verified_on_current_host)",
            description="High-speed spatial and textual layout analyzer extracting CTAs, buttons, and deadlines.",
            parameters_or_size="Local Module (< 1 MB)",
            notes="Ready for Qualcomm HTP execution provider."
        ))

        # 5. Deterministic Accessibility Reasoning & Remediation Engine
        self.register(ModelMetadata(
            name="AccessLens Rule-Based Remediation Engine",
            model_name="AccessLens Rule-Based Remediation Engine",
            model_version="1.0.0",
            task="Accessibility Reasoning & Developer Remediation",
            format="Python Native Heuristics / Knowledge Base",
            runtime="Local CPU",
            precision="N/A (Symbolic / Rule-Based)",
            target_hardware="Local CPU",
            execution_provider="CPUExecutionProvider",
            license="Apache-2.0",
            source="AccessLens AI Local-First Architecture",
            target="Evidence-grounded explanation and developer remediation",
            cpu_supported=True,
            qnn_supported=False,
            verification_status="Verified on current AMD CPU development host (verified_on_current_host)",
            provider="AccessLens",
            local_only=True,
            description="Deterministic, zero-cloud accessibility reasoning and developer remediation assistant.",
            parameters_or_size="Built-in (< 1 MB)",
            notes="Offline-first. Generates actionable fixes across XAML, WinForms, and Web. Zero cloud API calls."
        ))

        # 6. Qualcomm Hexagon NPU Target Pipeline (Snapdragon X Readiness)
        self.register(ModelMetadata(
            name="AccessLens-QNN-HTP-Target",
            model_name="AccessLens-QNN-HTP-Target",
            model_version="1.0.0",
            task="NPU Accelerated Accessibility Barrier & Text Inference",
            format="ONNX (QNN HTP Context Binary Ready)",
            runtime="QNNExecutionProvider",
            precision="INT8 / FP16",
            target_hardware="Qualcomm Hexagon NPU (HTP)",
            execution_provider="QNNExecutionProvider",
            license="Apache-2.0",
            source="Qualcomm AI Hub / AccessLens Pipeline Specification",
            target="Qualcomm Snapdragon X Elite / X Plus Hexagon NPU target",
            cpu_supported=False,
            qnn_supported=True,
            verification_status="Qualcomm-targeted model configuration — pending genuine Snapdragon validation (pending_genuine_snapdragon_validation)",
            provider="AccessLens / Qualcomm QNN",
            local_only=True,
            description="Architecture definition for Hexagon Tensor Processor inference acceleration.",
            parameters_or_size="Optimized HTP Subgraph",
            notes="Pending physical Snapdragon X Series hardware access for on-device validation."
        ))

    def register(self, model: ModelMetadata):
        self._models[model.name] = model

    def get_model(self, name: str) -> Optional[ModelMetadata]:
        return self._models.get(name)

    def list_models(self) -> List[ModelMetadata]:
        return list(self._models.values())

    def get_models_for_task(self, task: str) -> List[ModelMetadata]:
        return [m for m in self._models.values() if task.lower() in m.task.lower()]


# Singleton instance
model_registry = ModelRegistry()

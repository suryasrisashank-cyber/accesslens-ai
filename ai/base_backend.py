"""Base compute backend interface for VisionVoice AI."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIBackend(ABC):
    """Abstract base class for all AI computation engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the backend."""
        pass

    @property
    @abstractmethod
    def execution_providers(self) -> List[str]:
        """List of ONNX execution providers prioritized by this backend."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the backend runtime dependencies and hardware are available."""
        pass

    @abstractmethod
    def get_status_info(self) -> Dict[str, Any]:
        """Returns diagnostic status dictionary."""
        pass

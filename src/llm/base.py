# Base LLM interface
# Abstract base class that defines the common interface for all LLM implementations

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseLLM(ABC):
    """Abstract base class for LLM implementations"""

    def __init__(self, model: str, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM is available"""
        pass

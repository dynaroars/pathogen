# LLM factory and provider registry
# Creates LLM instances for performance analysis - supports Groq (free, fast) and OpenAI (paid, reliable)

import yaml
import os
from typing import Dict, Any
from .base import BaseLLM
from .groq_llm import GroqLLM
from .openai_llm import OpenAILLM

class LLMFactory:
    """Factory for creating LLM instances"""

    _registry = {
        'groq': GroqLLM,
        'openai': OpenAILLM,
    }

    @classmethod
    def create_llm(cls, provider: str, model: str = None, config: Dict[str, Any] = None) -> BaseLLM:
        """Create an LLM instance"""
        if provider not in cls._registry:
            raise ValueError(f"Unknown LLM provider: {provider}")

        # Load provider-specific config if not provided
        if config is None:
            config = cls._load_provider_config(provider)

        # Use default model if not specified
        if model is None:
            model = config.get('default_model')
            if not model:
                raise ValueError(f"No model specified and no default model for provider: {provider}")

        llm_class = cls._registry[provider]
        return llm_class(model, config)

    @classmethod
    def _load_provider_config(cls, provider: str) -> Dict[str, Any]:
        """Load provider-specific configuration"""
        config_path = "config/llm_configs.yaml"

        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                configs = yaml.safe_load(f)
                return configs.get('providers', {}).get(provider, {})

        return {}

    @classmethod
    def list_available_providers(cls) -> Dict[str, bool]:
        """List available providers and their availability"""
        availability = {}

        for provider_name in cls._registry:
            try:
                # Try to create a dummy instance to check availability
                config = cls._load_provider_config(provider_name)
                if not config:
                    availability[provider_name] = False
                    continue

                # Create instance with default model
                default_model = config.get('default_model')
                if default_model:
                    llm = cls.create_llm(provider_name, default_model, config)
                    availability[provider_name] = llm.is_available()
                else:
                    availability[provider_name] = False

            except Exception:
                availability[provider_name] = False

        return availability

# OpenAI LLM implementation
# Provides interface to OpenAI's GPT models via their API

import os
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from typing import Dict, Any
from .base import BaseLLM

class OpenAILLM(BaseLLM):
    """OpenAI LLM implementation"""

    def __init__(self, model: str, config: Dict[str, Any]):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Install with: pip install openai")

        super().__init__(model, config)
        api_key = os.getenv(config.get('api_key_env', 'OPENAI_API_KEY'))

        if not api_key:
            raise ValueError("OpenAI API key not found")

        self.client = openai.OpenAI(api_key=api_key)

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        return OPENAI_AVAILABLE and bool(os.getenv('OPENAI_API_KEY'))

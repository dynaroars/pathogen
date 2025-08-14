import os
import requests
from typing import Dict, Any
from .base import BaseLLM

class GroqLLM(BaseLLM):
    """Groq LLM implementation"""

    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        self.api_key = os.getenv(config.get('api_key_env', 'GROQ_API_KEY'))
        self.base_url = config.get('base_url', 'https://api.groq.com/openai/v1')

        if not self.api_key:
            raise ValueError(f"API key not found in environment variable")

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Groq API"""
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get('temperature', self.temperature),
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content']

        except requests.exceptions.RequestException as e:
            raise Exception(f"Groq API error: {e}")

    def is_available(self) -> bool:
        """Check if Groq API is available"""
        return bool(self.api_key)

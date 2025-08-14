# LLM functionality tests
# Tests for LLM factory, base classes, and provider implementations

import pytest
import os
from unittest.mock import Mock, patch
from pathlib import Path

import sys
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from llm.factory import LLMFactory
from llm.base import BaseLLM
from llm.groq_llm import GroqLLM

class MockLLM(BaseLLM):
    """Mock LLM for testing"""

    def generate(self, prompt: str, **kwargs) -> str:
        return "Mock response"

    def is_available(self) -> bool:
        return True

class TestLLMFactory:
    """Test LLM factory functionality"""

    def test_create_unknown_provider(self):
        """Test creating unknown provider raises error"""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMFactory.create_llm("unknown_provider")

    def test_registry_contains_expected_providers(self):
        """Test that registry contains expected providers"""
        expected_providers = ['groq', 'openai']

        for provider in expected_providers:
            assert provider in LLMFactory._registry

    @patch('llm.groq_llm.requests')
    def test_groq_llm_initialization(self, mock_requests):
        """Test Groq LLM initialization"""
        config = {
            'base_url': 'https://api.groq.com/openai/v1',
            'timeout': 60
        }

        llm = GroqLLM("llama2-70b-4096", config)

        assert llm.model == "llama2-70b-4096"
        assert llm.base_url == "https://api.groq.com/openai/v1"
        assert llm.timeout == 60

class TestBaseLLM:
    """Test base LLM functionality"""

    def test_base_llm_initialization(self):
        """Test base LLM initialization"""
        config = {
            'temperature': 0.8,
            'max_tokens': 2000
        }

        llm = MockLLM("test-model", config)

        assert llm.model == "test-model"
        assert llm.temperature == 0.8
        assert llm.max_tokens == 2000

    def test_base_llm_abstract_methods(self):
        """Test that base LLM defines abstract methods"""
        assert hasattr(BaseLLM, 'generate')
        assert hasattr(BaseLLM, 'is_available')

import pytest
from core.llm.litellm_client import LiteLLMProvider, LiteLLMRouter

def test_litellm_provider_init():
    provider = LiteLLMProvider(model_name="openai/gpt-4o")
    assert provider.model_name == "openai/gpt-4o"

def test_litellm_provider_default():
    provider = LiteLLMProvider()
    # Default model from settings (openai/gpt-4o)
    assert provider.model_name == "openai/gpt-4o"

def test_litellm_router_init():
    router = LiteLLMRouter()
    assert router.model_map is not None

def test_litellm_router_routing():
    router = LiteLLMRouter()
    assert router.get_model_for_complexity(1) == "ollama/qwen3"
    assert router.get_model_for_complexity(5) == "gemini/gemini-1.5-flash"
    assert router.get_model_for_complexity(10) == "openai/gpt-4o"

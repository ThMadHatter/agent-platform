import pytest
from core.llm.providers.gemini import GeminiProvider
from core.llm.providers.openai import OpenAIProvider

def test_gemini_provider_init():
    provider = GeminiProvider(api_key="fake_key")
    assert provider.model is not None

def test_openai_provider_init():
    provider = OpenAIProvider(api_key="fake_key")
    assert provider.api_key == "fake_key"

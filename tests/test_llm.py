import pytest
from core.llm.litellm_client import LiteLLMProvider, LiteLLMRouter

def test_litellm_provider_init():
    provider = LiteLLMProvider(model_name="basic-profile")
    assert provider.model_name == "basic-profile"

def test_litellm_provider_invalid_init():
    with pytest.raises(ValueError, match="Invalid model"):
        LiteLLMProvider(model_name="invalid-alias")

def test_litellm_provider_default():
    provider = LiteLLMProvider()
    # Default model from settings (basic-profile)
    assert provider.model_name == "basic-profile"

def test_litellm_router_init():
    router = LiteLLMRouter()
    assert router.model_map is not None

def test_litellm_router_routing():
    router = LiteLLMRouter()
    # Based on our updated model_routing.yaml:
    # 1-6 -> basic -> basic-profile
    # 7-10 -> heavy -> heavy-profile
    assert router.get_model_for_complexity(1) == "basic-profile"
    assert router.get_model_for_complexity(5) == "basic-profile"
    assert router.get_model_for_complexity(7) == "heavy-profile"
    assert router.get_model_for_complexity(10) == "heavy-profile"

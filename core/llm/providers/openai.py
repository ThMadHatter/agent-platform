from typing import Any, Dict, Optional
from core.llm.base import LLMProvider, LLMResponse

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4-turbo"):
        self.api_key = api_key
        self.model_name = model_name

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        print(f"OpenAI generating: {prompt[:50]}...")
        return LLMResponse(content="OpenAI response", raw_response={})

    async def generate_structured(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        return LLMResponse(content='{"extracted": "data"}', raw_response={})

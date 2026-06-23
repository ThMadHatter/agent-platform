from typing import Any, Dict, Optional
from core.llm.base import LLMProvider, LLMResponse

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3"):
        self.base_url = base_url
        self.model_name = model_name

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        print(f"Ollama generating: {prompt[:50]}...")
        return LLMResponse(content="Ollama response", raw_response={})

    async def generate_structured(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        return LLMResponse(content='{"extracted": "data"}', raw_response={})

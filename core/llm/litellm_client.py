import logging
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from core.llm.base import LLMProvider, LLMResponse
from core.config import settings

logger = logging.getLogger(__name__)

class LiteLLMProvider(LLMProvider):
    def __init__(self, client: AsyncOpenAI, model_name: str = "ollama/qwen3"):
        self.client = client
        self.model_name = model_name

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs
        )

        content = response.choices[0].message.content
        usage = response.usage

        return LLMResponse(
            content=content,
            raw_response=response.model_dump(),
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens
        )

    async def generate_structured(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        prompt = f"{prompt}\n\nReturn the output in the following JSON format: {schema}"
        return await self.generate(prompt, system_prompt, **kwargs)

class LiteLLMRouter:
    def __init__(self, api_key: str = settings.litellm_api_key, base_url: str = settings.litellm_base_url):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def get_model_for_complexity(self, complexity_score: int) -> str:
        if complexity_score < 2:
            return "ollama/qwen3"
        elif complexity_score < 5:
            return "openrouter/deepseek"
        else:
            return "gemini/gemini-2.5-pro"

    async def route_and_execute(self, task_context: str, complexity_score: int, system_prompt: Optional[str] = None) -> LLMResponse:
        model_name = self.get_model_for_complexity(complexity_score)
        logger.info(f"Routing task with complexity {complexity_score} to model {model_name}")

        provider = LiteLLMProvider(client=self.client, model_name=model_name)
        return await provider.generate(task_context, system_prompt=system_prompt)

import logging
import litellm
from typing import Any, Dict, List, Optional, Union
from core.llm.base import LLMProvider, LLMResponse
from core.config import settings

# Configure LiteLLM
litellm.telemetry = False # Disable telemetry for privacy
litellm.drop_params = True # Drop params not supported by provider

logger = logging.getLogger(__name__)

class LiteLLMProvider(LLMProvider):
    """
    A unified LLM provider using LiteLLM.
    Supports any model string compatible with LiteLLM (e.g., 'openai/gpt-4o', 'gemini/gemini-1.5-pro').
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.default_model

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await litellm.acompletion(
                model=self.model_name,
                messages=messages,
                api_base=settings.litellm_base_url,
                api_key=settings.litellm_api_key,
                **kwargs
            )

            content = response.choices[0].message.content or ""
            usage = response.usage

            return LLMResponse(
                content=content,
                raw_response=response.model_dump(),
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                total_tokens=getattr(usage, "total_tokens", 0),
                cost=getattr(response, "_response_cost", 0.0)
            )
        except Exception as e:
            logger.error(f"LiteLLM completion error: {e}")
            raise

    async def generate_structured(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        Uses LiteLLM's structured output support if available, or fallbacks to prompting.
        """
        try:
            # Attempt to use response_format if supported
            response = await litellm.acompletion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                api_base=settings.litellm_base_url,
                api_key=settings.litellm_api_key,
                response_format={"type": "json_object", "schema": schema} if schema else {"type": "json_object"},
                **kwargs
            )

            content = response.choices[0].message.content or ""
            usage = response.usage

            return LLMResponse(
                content=content,
                raw_response=response.model_dump(),
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                total_tokens=getattr(usage, "total_tokens", 0),
                cost=getattr(response, "_response_cost", 0.0)
            )
        except Exception as e:
            logger.warning(f"LiteLLM structured output failed, falling back to manual: {e}")
            # Fallback to manual prompting
            enhanced_prompt = f"{prompt}\n\nReturn the output as a valid JSON object matching this schema: {schema}"
            return await self.generate(enhanced_prompt, system_prompt, **kwargs)

class LiteLLMRouter:
    """
    Routes tasks to different models based on complexity or other criteria using LiteLLM.
    """
    def __init__(self, model_map: Optional[Dict[int, str]] = None):
        self.model_map = model_map or {
            1: "ollama/qwen3",
            2: "ollama/qwen3",
            3: "openrouter/deepseek/deepseek-coder",
            4: "openrouter/deepseek/deepseek-coder",
            5: "gemini/gemini-1.5-flash",
            6: "gemini/gemini-1.5-flash",
            7: "gemini/gemini-1.5-pro",
            8: "gemini/gemini-1.5-pro",
            9: "openai/gpt-4o",
            10: "openai/gpt-4o"
        }

    def get_model_for_complexity(self, complexity_score: int) -> str:
        # Clamp score between 1 and 10
        score = max(1, min(10, complexity_score))
        return self.model_map.get(score, settings.default_model)

    async def route_and_execute(self, task_context: str, complexity_score: int, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        model_name = self.get_model_for_complexity(complexity_score)
        logger.info(f"Routing task (complexity {complexity_score}) to model {model_name}")

        provider = LiteLLMProvider(model_name=model_name)
        return await provider.generate(task_context, system_prompt=system_prompt, **kwargs)

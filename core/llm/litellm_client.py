import logging
import litellm
import yaml
import os
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
    Configuration is loaded from a YAML file.
    """
    def __init__(self, config_path: str = "config/model_routing.yaml"):
        self.config_path = config_path
        self.model_map = {}
        self.routing_map = {}
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.model_map = config.get('models', {})
                    self.routing_map = config.get('routing', {})
                logger.info(f"Loaded model routing configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load model routing config: {e}")
                self._load_defaults()
        else:
            logger.warning(f"Model routing config not found at {self.config_path}, using defaults.")
            self._load_defaults()

    def _load_defaults(self):
        self.model_map = {"default": settings.default_model}
        self.routing_map = {i: "default" for i in range(1, 11)}

    def get_model_for_complexity(self, complexity_score: int) -> str:
        # Clamp score between 1 and 10
        score = max(1, min(10, complexity_score))
        model_key = self.routing_map.get(score, "default")
        if isinstance(model_key, int): # Handle cases where YAML keys might be loaded as ints
             model_key = self.routing_map.get(score, "default")

        model_name = self.model_map.get(model_key, settings.default_model)
        return model_name

    async def route_and_execute(self, task_context: str, complexity_score: int, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        model_name = self.get_model_for_complexity(complexity_score)
        logger.info(f"Routing task (complexity {complexity_score}) to model {model_name}")

        provider = LiteLLMProvider(model_name=model_name)
        return await provider.generate(task_context, system_prompt=system_prompt, **kwargs)

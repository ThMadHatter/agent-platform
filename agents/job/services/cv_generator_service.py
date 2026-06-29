import logging
from typing import Dict, Any, List, Optional
from core.llm.base import LLMProvider
from core.llm.prompt_registry import PromptRegistry
from .typst_utils import TypstCVDataBuilder

logger = logging.getLogger(__name__)

class CVGeneratorService:
    def __init__(
        self,
        llm_provider: LLMProvider,
        prompt_registry: PromptRegistry
    ):
        self.llm_provider = llm_provider
        self.prompt_registry = prompt_registry

    async def generate_cv_data(
        self,
        profile_data: Dict[str, Any],
        parsed_job: Dict[str, Any],
        match_result: Dict[str, Any],
        template_id: str = "lavandula",
        language: str = "en",
        target_pages: int = 2
    ) -> Dict[str, Any]:
        strategy_prompt = self.prompt_registry.render(
            "cv_strategy.j2",
            profile=profile_data,
            job=parsed_job,
            match=match_result
        )

        strategy_schema = {
            "type": "object",
            "properties": {
                "positioning": {"type": "string"},
                "selected_experiences": {"type": "array", "items": {"type": "string"}},
                "selected_skills": {"type": "array", "items": {"type": "string"}},
                "selected_achievements": {"type": "array", "items": {"type": "string"}},
                "gaps_to_address": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["positioning", "selected_experiences"]
        }

        strategy_resp = await self.llm_provider.generate_structured(strategy_prompt, schema=strategy_schema)
        strategy = strategy_resp.content

        cv_prompt = self.prompt_registry.render(
            "cv_generator.j2",
            profile=profile_data,
            job=parsed_job,
            match=match_result,
            strategy=strategy,
            language=language,
            target_pages=target_pages
        )

        cv_resp = await self.llm_provider.generate_structured(cv_prompt, schema={})
        raw_cv_data = cv_resp.content

        raw_cv_data["personal"] = {
            "name": profile_data.get("name", "Matteo Zappia"),
            "title": raw_cv_data.get("personal", {}).get("title") or parsed_job.get("title", ""),
            "contacts": profile_data.get("contacts", [])
        }
        raw_cv_data["languages"] = profile_data.get("languages", [])

        sanitized_data = TypstCVDataBuilder.sanitize(raw_cv_data)

        return {
            "strategy": strategy,
            "typst_data": sanitized_data
        }

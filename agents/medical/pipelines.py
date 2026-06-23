from typing import Any, Dict
from core.llm.base import LLMProvider
from core.llm.prompt_registry import PromptRegistry
import json

class ExtractionPipeline:
    def __init__(self, llm_provider: LLMProvider, prompt_registry: PromptRegistry):
        self.llm_provider = llm_provider
        self.prompt_registry = prompt_registry

    async def run(self, ocr_text: str, patient_id: str, extraction_type: str) -> Dict[str, Any]:
        prompt = self.prompt_registry.render(
            "extraction.j2",
            ocr_text=ocr_text,
            patient_id=patient_id,
            extraction_type=extraction_type
        )
        response = await self.llm_provider.generate_structured(prompt, schema={})
        try:
            return json.loads(response.content)
        except:
            return {"raw_content": response.content}

class NormalizationPipeline:
    def __init__(self, llm_provider: LLMProvider, prompt_registry: PromptRegistry):
        self.llm_provider = llm_provider
        self.prompt_registry = prompt_registry

    async def run(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.prompt_registry.render(
            "normalization.j2",
            extracted_data=json.dumps(extracted_data)
        )
        response = await self.llm_provider.generate(prompt)
        return {"normalized": response.content}

from typing import Any, Dict, List, Optional
from pydantic import Field
import json
import logging
from agents.shared.base import BaseAgent, AgentInput, AgentOutput
from core.storage.utils import StorageUtils, OCRProvider
from core.services.context import ServiceContext
from .pipelines import ExtractionPipeline, NormalizationPipeline

logger = logging.getLogger(__name__)

class MedicalAgentInput(AgentInput):
    document_url: Optional[str] = None
    gdrive_file_id: Optional[str] = None
    patient_id: str
    extraction_type: str = Field(default="general")

class MedicalAgent(BaseAgent):
    def __init__(self, context: ServiceContext):
        super().__init__(name="medical", context=context)
        self.ocr_provider = OCRProvider()
        self.extraction_pipeline = ExtractionPipeline(context.llm_provider, context.prompt_registry)
        self.normalization_pipeline = NormalizationPipeline(context.llm_provider, context.prompt_registry)

    async def validate(self, input_data: Dict[str, Any]) -> MedicalAgentInput:
        return MedicalAgentInput(**input_data)

    async def retrieve_context(self, validated_input: MedicalAgentInput) -> Dict[str, Any]:
        context = {"input": validated_input}
        try:
            if validated_input.document_url:
                logger.info(f"Downloading document from URL: {validated_input.document_url}")
                file_content = await StorageUtils.download_file(validated_input.document_url)
                context["file_content"] = file_content
            elif validated_input.gdrive_file_id:
                logger.info(f"Downloading document from Google Drive: {validated_input.gdrive_file_id}")
                file_content = await self.context.document_store.download(validated_input.gdrive_file_id)
                context["file_content"] = file_content
            else:
                logger.warning("No document provided in input")
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            raise
        return context

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"step": "ocr", "action": "extract_text"},
            {"step": "extraction", "action": "extract_entities"},
            {"step": "normalization", "action": "normalize_data"}
        ]

    async def execute(self, plan: List[Dict[str, Any]], execution_id: str) -> Dict[str, Any]:
        results = {}
        ocr_text = "Patient: John Doe. BP: 120/80. Heart Rate: 72."
        results["ocr_text"] = ocr_text

        if hasattr(self.context.metadata_store, 'save_artifact'):
            await self.context.metadata_store.save_artifact(execution_id, "ocr_result", "text", {"text": ocr_text})

        patient_id = "P123"
        extraction_type = "general"
        extracted_data = await self.extraction_pipeline.run(ocr_text, patient_id, extraction_type)
        results["extracted_data"] = extracted_data

        if hasattr(self.context.metadata_store, 'save_artifact'):
            await self.context.metadata_store.save_artifact(execution_id, "extracted_json", "json", extracted_data)

        normalized_data = await self.normalization_pipeline.run(extracted_data)
        results["normalized_data"] = normalized_data

        return results

    async def validate_output(self, raw_output: Dict[str, Any]) -> AgentOutput:
        return AgentOutput(success=True, data=raw_output["normalized_data"])

    async def persist(self, output: AgentOutput, execution_id: str) -> None:
        await self.context.vector_store.upsert("medical_records", [{"id": execution_id, "data": output.data}])
        logger.info(f"Execution {execution_id} persisted successfully")

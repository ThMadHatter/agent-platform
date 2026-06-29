import logging
from typing import Any, Dict, List, Optional
from pydantic import Field

from agents.shared.base import BaseAgent, AgentInput, AgentOutput
from core.services.context import ServiceContext
from .services.job_services import (
    LinkedInJobIngestionService,
    JobDescriptionParser,
    ResumeOptimizer,
    ApplicationTracker
)

logger = logging.getLogger(__name__)

class JobAgentInput(AgentInput):
    workflow: str # linkedin_ingestion, resume_optimization, resume_ingestion
    job_url: Optional[str] = None
    resume_id: Optional[str] = None
    resume_content: Optional[str] = None

class JobAgent(BaseAgent):
    def __init__(self, context: ServiceContext):
        super().__init__(name="job", context=context)

        # Internal services
        self.ingestion_service = LinkedInJobIngestionService()
        self.parser_service = JobDescriptionParser(context.llm_provider, context.prompt_registry)
        self.optimizer_service = ResumeOptimizer(context.llm_provider, context.prompt_registry)
        self.tracker_service = ApplicationTracker()

    async def validate(self, input_data: Dict[str, Any]) -> JobAgentInput:
        return JobAgentInput(**input_data)

    async def retrieve_context(self, validated_input: JobAgentInput) -> Dict[str, Any]:
        context = {"input": validated_input}
        if validated_input.resume_id:
            resume_content = await self.context.document_store.download(validated_input.resume_id)
            context["resume_content"] = resume_content.read().decode('utf-8')
        elif validated_input.resume_content:
            context["resume_content"] = validated_input.resume_content
        return context

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        workflow = context["input"].workflow
        if workflow == "linkedin_ingestion":
            return [
                {"step": "scrape", "action": "ingestion_service.scrape_job"},
                {"step": "parse", "action": "parser_service.parse"},
                {"step": "store", "action": "vector_store.upsert"}
            ]
        elif workflow == "resume_optimization":
            return [
                {"step": "scrape", "action": "ingestion_service.scrape_job"},
                {"step": "parse", "action": "parser_service.parse"},
                {"step": "optimize", "action": "optimizer_service.optimize"},
                {"step": "track", "action": "tracker_service.track_application"}
            ]
        elif workflow == "resume_ingestion":
            return [
                {"step": "extract_experience", "action": "llm_provider.generate_structured"},
                {"step": "store_knowledge", "action": "vector_store.upsert"},
                {"step": "update_profile", "action": "metadata_store.save_artifact"}
            ]
        else:
            raise ValueError(f"Unknown workflow: {workflow}")

    async def execute(self, plan: List[Dict[str, Any]], execution_id: str) -> Dict[str, Any]:
        execution_info = await self.context.metadata_store.get_execution(execution_id)
        input_data = JobAgentInput(**execution_info["input_data"])
        context = await self.retrieve_context(input_data)

        results = {}
        workflow = input_data.workflow

        if workflow == "linkedin_ingestion":
            job_data = await self.ingestion_service.scrape_job(input_data.job_url)
            parsed_job = await self.parser_service.parse(job_data["description"])
            results["job_data"] = job_data
            results["parsed_job"] = parsed_job

            await self.context.vector_store.upsert("jobs", [{"id": execution_id, "data": {**job_data, **parsed_job}}])

        elif workflow == "resume_optimization":
            job_data = await self.ingestion_service.scrape_job(input_data.job_url)
            parsed_job = await self.parser_service.parse(job_data["description"])
            optimized_resume = await self.optimizer_service.optimize(context.get("resume_content", ""), parsed_job)
            results["optimized_resume"] = optimized_resume

            await self.tracker_service.track_application(job_data)

        elif workflow == "resume_ingestion":
            resume_content = context.get("resume_content", "")
            prompt = self.context.prompt_registry.render("resume_parser.j2", resume=resume_content)
            response = await self.context.llm_provider.generate_structured(prompt, schema={})
            import json
            try:
                experience = json.loads(response.content)
            except:
                experience = {"raw": response.content}

            results["experience"] = experience
            await self.context.vector_store.upsert("user_knowledge", [{"id": execution_id, "data": experience}])

        return results

    async def validate_output(self, raw_output: Dict[str, Any]) -> AgentOutput:
        return AgentOutput(success=True, data=raw_output)

    async def persist(self, output: AgentOutput, execution_id: str) -> None:
        await self.context.metadata_store.save_artifact(execution_id, "job_execution_result", "json", output.data)

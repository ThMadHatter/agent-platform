import logging
from typing import Any, Dict, List, Optional
from pydantic import Field

from agents.shared.base import BaseAgent, AgentInput, AgentOutput
from core.config import settings
from core.services.context import ServiceContext
from .services.job_services import (
    LinkedInJobIngestionService,
    JobDescriptionParser,
    ResumeOptimizer,
    ApplicationTracker
)
from .services.cv_knowledge_service import CVKnowledgeService
from .services.cv_matcher_service import CVMatcherService
from .services.cv_generator_service import CVGeneratorService
from .services.typst_renderer_service import TypstRendererService
from .repository import JobRepository

logger = logging.getLogger(__name__)

class JobAgentInput(AgentInput):
    workflow: str

    # Job source
    job_id: Optional[str] = None
    job_url: Optional[str] = None
    job_content: Optional[str] = None
    job_data: Optional[Dict[str, Any]] = None
    parsed_job: Optional[Dict[str, Any]] = None
    distilled_jd: Optional[Dict[str, Any]] = None

    # CV/profile source
    resume_profile_id: str = "matteo-default"
    resume_id: Optional[str] = None # Deprecated, use cv_version_id or resume_content
    cv_version_id: Optional[str] = None
    resume_content: Optional[str] = None
    source_text: Optional[str] = None
    source_type: Optional[str] = None

    # CV generation
    template_id: str = "lavandula"
    language: str = "en"
    target_pages: int = 2
    render_pdf: bool = False

    # Optional behavior
    allow_fetch: bool = False

    # Metadata
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class JobAgent(BaseAgent):
    def __init__(self, context: ServiceContext):
        super().__init__(name="job", context=context)

        # Internal services
        self.ingestion_service = LinkedInJobIngestionService()
        self.parser_service = JobDescriptionParser(context.llm_provider, context.prompt_registry)
        self.optimizer_service = ResumeOptimizer(context.llm_provider, context.prompt_registry)
        self.tracker_service = ApplicationTracker()
        self.cv_knowledge_service = CVKnowledgeService(
            context.vector_store,
            context.llm_provider,
            context.prompt_registry,
            collection_name=settings.qdrant_cv_collection
        )
        self.cv_matcher_service = CVMatcherService(
            self.cv_knowledge_service,
            context.llm_provider,
            context.prompt_registry
        )
        self.cv_generator_service = CVGeneratorService(
            context.llm_provider,
            context.prompt_registry
        )
        self.typst_renderer_service = TypstRendererService(
            enabled=getattr(settings, "typst_enabled", False)
        )

    async def validate(self, input_data: Dict[str, Any]) -> JobAgentInput:
        return JobAgentInput(**input_data)

    async def retrieve_context(self, validated_input: JobAgentInput) -> Dict[str, Any]:
        return {"input": validated_input}

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        workflow = context["input"].workflow
        # Map deprecated workflows
        if workflow == "linkedin_ingestion":
            workflow = "job_parse"
        elif workflow == "resume_optimization":
            workflow = "cv_generate"
        elif workflow == "resume_ingestion":
            workflow = "cv_ingest"

        if workflow == "job_parse":
            return [{"step": "resolve_and_parse_job", "action": "job_parse"}]
        elif workflow == "cv_ingest":
            return [{"step": "ingest_cv_knowledge", "action": "cv_ingest"}]
        elif workflow == "cv_match":
            return [{"step": "match_cv_to_job", "action": "cv_match"}]
        elif workflow == "cv_generate":
            return [{"step": "generate_cv_data", "action": "cv_generate"}]
        elif workflow == "cv_render":
            return [{"step": "render_cv_pdf", "action": "cv_render"}]
        else:
            raise ValueError(f"Unknown workflow: {workflow}")

    async def execute(self, plan: List[Dict[str, Any]], execution_id: str) -> Dict[str, Any]:
        execution_info = await self.context.metadata_store.get_execution(execution_id)
        input_data = JobAgentInput(**execution_info["input_data"])

        # Map deprecated workflows
        workflow = input_data.workflow
        if workflow == "linkedin_ingestion":
            workflow = "job_parse"
        elif workflow == "resume_optimization":
            workflow = "cv_generate"
        elif workflow == "resume_ingestion":
            workflow = "cv_ingest"

        results = {}

        # Get DB session and repository
        async with self.context.metadata_store.async_session() as session:
            repo = JobRepository(session)

            if workflow == "job_parse":
                results = await self._handle_job_parse(input_data, repo)
            elif workflow == "cv_ingest":
                results = await self._handle_cv_ingest(input_data, repo)
            elif workflow == "cv_match":
                results = await self._handle_cv_match(input_data, repo, execution_id)
            elif workflow == "cv_generate":
                results = await self._handle_cv_generate(input_data, repo, execution_id)
            elif workflow == "cv_render":
                results = await self._handle_cv_render(input_data, repo, execution_id)

        return results

    async def _handle_job_parse(self, input_data: JobAgentInput, repo: JobRepository) -> Dict[str, Any]:
        # 1. Resolve job content
        raw_content = None
        source_url = input_data.job_url

        if input_data.job_content:
            raw_content = input_data.job_content
        elif input_data.job_data and input_data.job_data.get("description"):
            raw_content = input_data.job_data["description"]
        elif input_data.distilled_jd:
            parsed_job = input_data.distilled_jd
            job = await repo.save_job({
                "title": parsed_job.get("title"),
                "company": parsed_job.get("company"),
                "parsed_data": parsed_job,
                "source_url": source_url
            })
            return {"job_id": job.id, "parsed_job": parsed_job}
        elif input_data.job_url and input_data.allow_fetch:
            job_data = await self.ingestion_service.scrape_job(input_data.job_url)
            raw_content = job_data.get("description")
            source_url = input_data.job_url
        elif input_data.job_url and not input_data.allow_fetch:
            return {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "job_url provided but allow_fetch=false. Please provide job_content or enable allow_fetch."
                }
            }
        else:
            return {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "No job content provided. Need job_content, job_data.description, distilled_jd, or job_url with allow_fetch=true."
                }
            }

        # 2. Parse job description
        parsed_job = await self.parser_service.parse(raw_content)

        # 3. Save to SQL
        job = await repo.save_job({
            "source": input_data.source or "manual",
            "source_url": source_url,
            "title": parsed_job.get("title"),
            "company": parsed_job.get("company"),
            "location": parsed_job.get("location"),
            "raw_content": raw_content,
            "parsed_data": parsed_job
        })

        return {
            "job_id": job.id,
            "parsed_job": parsed_job
        }

    async def _handle_cv_ingest(self, input_data: JobAgentInput, repo: JobRepository) -> Dict[str, Any]:
        source_text = input_data.resume_content or input_data.source_text
        if not source_text and input_data.resume_id:
            resume_content = await self.context.document_store.download(input_data.resume_id)
            source_text = resume_content.read().decode('utf-8')

        if not source_text:
            return {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "No CV content provided. Need resume_content, source_text, or resume_id."
                }
            }

        profile_id = input_data.resume_profile_id
        items = await self.cv_knowledge_service.ingest_cv_knowledge(
            profile_id=profile_id,
            source_text=source_text,
            source_type=input_data.source_type or "resume"
        )

        saved_items_count = 0
        for item in items:
            await repo.save_cv_knowledge_item({
                "resume_profile_id": profile_id,
                "type": item["type"],
                "title": item["title"],
                "canonical_text": item["content"],
                "item_metadata": item.get("metadata", {}),
                "qdrant_point_id": None
            })
            saved_items_count += 1

        return {
            "resume_profile_id": profile_id,
            "ingested_items_count": saved_items_count,
            "items": items
        }

    async def _handle_cv_match(self, input_data: JobAgentInput, repo: JobRepository, execution_id: str) -> Dict[str, Any]:
        parsed_job = None
        job_id = input_data.job_id

        if job_id:
            job = await repo.get_job(job_id)
            if job:
                parsed_job = job.parsed_data

        if not parsed_job:
            parsed_job = input_data.parsed_job or input_data.distilled_jd

        if not parsed_job and (input_data.job_content or input_data.job_url):
            parse_result = await self._handle_job_parse(input_data, repo)
            if "error" in parse_result:
                return parse_result
            job_id = parse_result["job_id"]
            parsed_job = parse_result["parsed_job"]

        if not parsed_job:
            return {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "cv_match requires job_id, parsed_job, distilled_jd, or job_content."
                }
            }

        profile_id = input_data.resume_profile_id
        match_result = await self.cv_matcher_service.match(profile_id, parsed_job)

        match_record = await repo.save_match_result({
            "job_id": job_id,
            "execution_id": execution_id,
            "resume_profile_id": profile_id,
            "score": match_result["score"],
            "match_data": {
                "strengths": match_result["strengths"],
                "gaps": match_result["gaps"],
                "justification": match_result["justification"],
                "evidence_map": match_result["evidence_map"]
            },
            "retrieved_evidence": match_result["retrieved_evidence"]
        })

        return {
            "match_id": match_record.id,
            "score": match_result["score"],
            "strengths": match_result["strengths"],
            "gaps": match_result["gaps"],
            "justification": match_result["justification"],
            "evidence_map": match_result["evidence_map"]
        }

    async def _handle_cv_generate(self, input_data: JobAgentInput, repo: JobRepository, execution_id: str) -> Dict[str, Any]:
        job_id = input_data.job_id
        profile_id = input_data.resume_profile_id

        match_data = await self._handle_cv_match(input_data, repo, execution_id)
        match_id = match_data["match_id"]

        profile = await repo.get_resume_profile(profile_id)
        if not profile:
            profile_data = {
                "name": "Matteo Zappia",
                "contacts": [
                    {"icon": "envelope", "icon_solid": True, "text": "matteo.zappia@gmail.com", "link": "mailto:matteo.zappia@gmail.com"},
                    {"icon": "linkedin", "icon_solid": False, "text": "LinkedIn", "link": "https://linkedin.com/in/matteo-zappia-0b8161114"}
                ],
                "languages": [
                    {"flag": "IT", "name": "Italian", "level": 1.0},
                    {"flag": "GB", "name": "English", "level": 0.8}
                ]
            }
        else:
            profile_data = {
                "name": profile.name,
                "contacts": profile.contacts,
                "languages": profile.languages,
                "summary": profile.summary
            }

        job = await repo.get_job(job_id)
        parsed_job = job.parsed_data if job else input_data.parsed_job

        # Check if enough CV knowledge exists
        items = await repo.list_cv_knowledge_items(profile_id)
        if not items:
            return {
                "error": {
                    "code": "CV_KNOWLEDGE_NOT_FOUND",
                    "message": f"Not enough CV knowledge found for resume_profile_id={profile_id}. Run cv_ingest first.",
                    "details": {"resume_profile_id": profile_id}
                }
            }

        gen_result = await self.cv_generator_service.generate_cv_data(
            profile_data=profile_data,
            parsed_job=parsed_job,
            match_result=match_data,
            template_id=input_data.template_id,
            language=input_data.language,
            target_pages=input_data.target_pages
        )

        run_record = await repo.save_cv_generation_run({
            "job_id": job_id,
            "execution_id": execution_id,
            "resume_profile_id": profile_id,
            "template_id": input_data.template_id,
            "language": input_data.language,
            "target_pages": input_data.target_pages,
            "match_id": match_id,
            "strategy_data": gen_result["strategy"],
            "typst_data": gen_result["typst_data"],
            "status": "completed"
        })

        return {
            "job_id": job_id,
            "cv_version_id": run_record.id,
            "match": match_data,
            "cv_strategy": gen_result["strategy"],
            "typst_data": gen_result["typst_data"]
        }

    async def _handle_cv_render(self, input_data: JobAgentInput, repo: JobRepository, execution_id: str) -> Dict[str, Any]:
        typst_data = None
        cv_version_id = input_data.resume_id

        if cv_version_id:
            from sqlalchemy import select
            from database.models import CVGenerationRun
            stmt = select(CVGenerationRun).where(CVGenerationRun.id == cv_version_id)
            result = await repo.session.execute(stmt)
            run = result.scalar_one_or_none()
            if run:
                typst_data = run.typst_data

        if not typst_data:
            typst_data = input_data.parsed_job

        if not typst_data:
            return {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "No Typst data found. Provide cv_version_id (via resume_id) or typst_data (via parsed_job)."
                }
            }

        if not self.typst_renderer_service.enabled:
            return {
                "error": {
                    "code": "TYPST_RENDERING_DISABLED",
                    "message": "Typst rendering requested but typst.enabled=false. Use cv_generate output in n8n or enable TypstRendererService."
                }
            }

        from .services.typst_utils import TypstCVDataBuilder
        filename = TypstCVDataBuilder.build_safe_filename(
            input_data.resume_profile_id,
            typst_data.get("experience", [{}])[0].get("company", "Unknown"),
            typst_data.get("personal", {}).get("title", "Role")
        )

        pdf_path = await self.typst_renderer_service.render(typst_data, filename)

        if not pdf_path:
            return {
                "status": "error",
                "message": "Typst compilation failed. Check logs."
            }

        artifact = await repo.save_artifact_reference({
            "execution_id": execution_id,
            "name": filename,
            "content_type": "application/pdf",
            "data": {"path": pdf_path}
        })

        return {
            "status": "success",
            "artifact_id": artifact.id,
            "pdf_path": pdf_path,
            "filename": filename
        }

    async def validate_output(self, raw_output: Dict[str, Any]) -> AgentOutput:
        return AgentOutput(success=True, data=raw_output)

    async def persist(self, output: AgentOutput, execution_id: str) -> None:
        await self.context.metadata_store.save_artifact(execution_id, "job_execution_result", "json", output.data)

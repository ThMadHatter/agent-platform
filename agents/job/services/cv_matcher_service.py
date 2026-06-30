import logging
from typing import Dict, Any, List, Optional
from core.llm.base import LLMProvider
from core.llm.prompt_registry import PromptRegistry
from .cv_knowledge_service import CVKnowledgeService

logger = logging.getLogger(__name__)

class CVMatcherService:
    def __init__(
        self,
        cv_knowledge_service: CVKnowledgeService,
        llm_provider: LLMProvider,
        prompt_registry: PromptRegistry
    ):
        self.cv_knowledge_service = cv_knowledge_service
        self.llm_provider = llm_provider
        self.prompt_registry = prompt_registry

    async def match(
        self,
        profile_id: str,
        parsed_job: Dict[str, Any]
    ) -> Dict[str, Any]:
        categories = [
            "mission_critical",
            "tech_stack",
            "soft_skills",
            "preferred_skills",
            "responsibilities"
        ]

        all_retrieved_evidence = []
        evidence_map = {}

        for category in categories:
            requirements = parsed_job.get(category, [])
            category_evidence = {}

            for req in requirements:
                evidence_items = await self.cv_knowledge_service.retrieve_relevant_evidence(
                    profile_id=profile_id,
                    query=req,
                    limit=3
                )

                category_evidence[req] = [
                    {
                        "title": item["payload"].get("title"),
                        "content": item["payload"].get("content"),
                        "type": item["payload"].get("type")
                    } for item in evidence_items
                ]

                all_retrieved_evidence.extend(evidence_items)

            evidence_map[category] = category_evidence

        prompt = self.prompt_registry.render(
            "cv_matcher.j2",
            parsed_job=parsed_job,
            evidence_map=evidence_map
        )

        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 100},
                "strengths": {"type": "array", "items": {"type": "string"}},
                "gaps": {"type": "array", "items": {"type": "string"}},
                "justification": {"type": "string"},
                "classification": {
                    "type": "object",
                    "properties": {
                        "tech_stack": {"type": "object"},
                        "soft_skills": {"type": "object"},
                        "mission_critical": {"type": "object"},
                        "preferred_skills": {"type": "object"},
                        "responsibilities": {"type": "object"}
                    }
                }
            },
            "required": ["score", "strengths", "gaps", "justification"]
        }

        try:
            response = await self.llm_provider.generate_structured(prompt, schema=schema)
            eval_result = response.content
        except Exception as e:
            logger.error(f"Error during CV matching classification: {e}")
            eval_result = {
                "score": 0,
                "strengths": [],
                "gaps": ["Error during matching"],
                "justification": f"Failed to match evidence: {str(e)}",
                "classification": {}
            }

        return {
            "score": eval_result.get("score", 0),
            "strengths": eval_result.get("strengths", []),
            "gaps": eval_result.get("gaps", []),
            "justification": eval_result.get("justification", ""),
            "evidence_map": eval_result.get("classification", evidence_map),
            "retrieved_evidence": [
                {
                    "title": item["payload"].get("title"),
                    "content": item["payload"].get("content"),
                    "type": item["payload"].get("type")
                } for item in all_retrieved_evidence
            ]
        }

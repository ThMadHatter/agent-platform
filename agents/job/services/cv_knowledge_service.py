import logging
from typing import Dict, Any, List, Optional
from core.storage.base import VectorStore
from core.llm.base import LLMProvider, EmbeddingProvider
from core.llm.prompt_registry import PromptRegistry

logger = logging.getLogger(__name__)

class CVKnowledgeService:
    def __init__(
        self,
        vector_store: VectorStore,
        llm_provider: LLMProvider,
        embedding_provider: EmbeddingProvider,
        prompt_registry: PromptRegistry,
        collection_name: str = "cv_knowledge"
    ):
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.embedding_provider = embedding_provider
        self.prompt_registry = prompt_registry
        self.collection_name = collection_name

    async def ingest_cv_knowledge(
        self,
        profile_id: str,
        source_text: str,
        source_type: str = "resume"
    ) -> List[Dict[str, Any]]:
        prompt = self.prompt_registry.render(
            "resume_parser.j2",
            resume=source_text
        )

        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["experience", "project", "skill", "achievement", "education"]},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "metadata": {"type": "object"}
                        },
                        "required": ["type", "title", "content"]
                    }
                }
            },
            "required": ["items"]
        }

        response = await self.llm_provider.generate_structured(prompt, schema=schema)
        items = response.content.get("items", [])

        points = []
        for i, item in enumerate(items):
            point_id = f"{profile_id}-{source_type}-{i}"

            payload = {
                "resume_profile_id": profile_id,
                "type": item["type"],
                "title": item["title"],
                "content": item["content"],
                "source_type": source_type,
                **item.get("metadata", {})
            }

            points.append({
                "id": point_id,
                "payload": payload,
                "content": f"{item['title']}: {item['content']}"
            })

        if points:
            # Add embeddings to points
            for point in points:
                point["vector"] = await self.embedding_provider.embed(point["content"])
            await self.vector_store.upsert(self.collection_name, points)

        return items

    async def retrieve_relevant_evidence(
        self,
        profile_id: str,
        query: str,
        limit: int = 10,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # 1. Generate embedding for the query
        vector = await self.embedding_provider.embed(query)

        # 2. Search in Qdrant
        results = await self.vector_store.search(
            collection=self.collection_name,
            vector=vector,
            limit=limit
        )

        relevant_results = [
            r for r in results
            if r.get("payload", {}).get("resume_profile_id") == profile_id
        ]

        if filter_type:
            relevant_results = [
                r for r in relevant_results
                if r.get("payload", {}).get("type") == filter_type
            ]

        return relevant_results

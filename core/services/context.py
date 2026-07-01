from dataclasses import dataclass
from typing import Optional
from core.storage.base import MetadataStore, DocumentStore, VectorStore
from core.llm.base import LLMProvider, EmbeddingProvider
from core.llm.prompt_registry import PromptRegistry

@dataclass
class ServiceContext:
    metadata_store: MetadataStore
    document_store: DocumentStore
    vector_store: VectorStore
    llm_provider: LLMProvider
    embedding_provider: EmbeddingProvider
    prompt_registry: PromptRegistry
    # You can add other services here as needed, e.g., ocr_provider, search_service

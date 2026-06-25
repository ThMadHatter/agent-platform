from core.storage.postgres import PostgreSQLMetadataStore
from core.storage.gdrive import GoogleDriveDocumentStore
from core.storage.qdrant import QdrantVectorStore
from core.execution.runner import AgentRunner
from core.llm.providers.gemini import GeminiProvider
from core.llm.prompt_registry import PromptRegistry
from core.config import settings

# Shared instances
metadata_store = PostgreSQLMetadataStore()
document_store = GoogleDriveDocumentStore(settings.google_drive_credentials_path)
vector_store = QdrantVectorStore()
llm_provider = GeminiProvider(api_key=settings.gemini_api_key)
prompt_registry = PromptRegistry(["agents/medical/prompts", "agents/coding/prompts", "core/llm/prompts"])

runner = AgentRunner(metadata_store)

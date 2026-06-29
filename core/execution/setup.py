from core.storage.postgres import PostgreSQLMetadataStore
from core.storage.gdrive import GoogleDriveDocumentStore
from core.storage.qdrant import QdrantVectorStore
from core.execution.runner import AgentRunner
from core.llm.litellm_client import LiteLLMProvider
from core.llm.prompt_registry import PromptRegistry
from core.config import settings
from core.execution.registry import agent_registry, AgentMetadata
from core.services.context import ServiceContext

from agents.medical.agent import MedicalAgent
from agents.coding.analyzer_agent import RepoAnalyzerAgent
from agents.simplechat.agent import SimpleChatAgent
from agents.job.agent import JobAgent

def setup_platform():
    # Shared instances
    metadata_store = PostgreSQLMetadataStore()
    document_store = GoogleDriveDocumentStore(settings.google_drive_credentials_path)
    vector_store = QdrantVectorStore()
    llm_provider = LiteLLMProvider(model_name=settings.default_model)
    prompt_registry = PromptRegistry([
        "agents/medical/prompts",
        "agents/coding/prompts",
        "core/llm/prompts",
        "agents/job/prompts"
    ])

    service_context = ServiceContext(
        metadata_store=metadata_store,
        document_store=document_store,
        vector_store=vector_store,
        llm_provider=llm_provider,
        prompt_registry=prompt_registry
    )

    runner = AgentRunner(metadata_store)

    # Initialize and register agents
    medical_agent = MedicalAgent(service_context)
    agent_registry.register(medical_agent, AgentMetadata(
        id="medical",
        name="Medical Agent",
        version="1.0.0",
        description="Medical document extraction and normalization agent",
        input_schema={"patient_id": "str", "document_url": "Optional[str]", "gdrive_file_id": "Optional[str]"},
        output_schema={"success": "bool", "data": "dict"},
        capabilities=["ocr", "entity_extraction", "normalization"],
        required_services=["OCRProvider"],
        tags=["medical", "extraction"],
        execution_modes=["sync", "async"]
    ))

    repo_analyzer = RepoAnalyzerAgent(service_context)
    agent_registry.register(repo_analyzer, AgentMetadata(
        id="repo_analyzer",
        name="Repo Analyzer Agent",
        version="1.0.0",
        description="Repository analysis and code improvement agent",
        input_schema={"repo_path": "str", "complexity_score": "Optional[int]"},
        output_schema={"issues_found": "list", "suggested_fixes": "list"},
        capabilities=["code_analysis", "vulnerability_detection"],
        required_services=[],
        tags=["coding", "analysis"],
        execution_modes=["sync", "async"]
    ))

    simple_chat = SimpleChatAgent(service_context)
    agent_registry.register(simple_chat, AgentMetadata(
        id="simple_chat",
        name="Simple Chat Agent",
        version="1.0.0",
        description="Simple conversational agent",
        input_schema={"message": "str"},
        output_schema={"response": "str"},
        capabilities=["conversation"],
        required_services=[],
        tags=["chat"],
        execution_modes=["sync", "async"]
    ))

    job_agent = JobAgent(service_context)
    agent_registry.register(job_agent, AgentMetadata(
        id="job",
        name="Job Agent",
        version="1.0.0",
        description="Job domain agent for ingestion, optimization and tracking",
        input_schema={"workflow": "str", "job_url": "Optional[str]", "resume_id": "Optional[str]"},
        output_schema={"success": "bool", "data": "dict"},
        capabilities=["job_scraping", "resume_parsing", "resume_optimization"],
        required_services=["LinkedInJobIngestionService", "JobDescriptionParser", "ResumeOptimizer"],
        tags=["job", "career"],
        execution_modes=["sync", "async"]
    ))

    return runner, service_context

# Global instances for simple dependency injection if needed
# but better to use the setup_platform or specific dependencies

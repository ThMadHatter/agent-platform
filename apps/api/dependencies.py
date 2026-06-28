from core.storage.postgres import PostgreSQLMetadataStore
from core.storage.gdrive import GoogleDriveDocumentStore
from core.storage.qdrant import QdrantVectorStore
from core.execution.runner import AgentRunner
from core.llm.litellm_client import LiteLLMProvider, LiteLLMRouter
from core.llm.prompt_registry import PromptRegistry
from core.config import settings
from core.execution.registry import agent_registry, AgentMetadata
from agents.medical.agent import MedicalAgent
from agents.coding.analyzer_agent import RepoAnalyzerAgent
from agents.simplechat.agent import SimpleChatAgent
from agents.job.agent import JobAgent

# Shared instances
metadata_store = PostgreSQLMetadataStore()
document_store = GoogleDriveDocumentStore(settings.google_drive_credentials_path)
vector_store = QdrantVectorStore()
llm_provider = LiteLLMProvider(model_name=settings.default_model)
prompt_registry = PromptRegistry(["agents/medical/prompts", "agents/coding/prompts", "core/llm/prompts", "agents/job/prompts"])

runner = AgentRunner(metadata_store)

# Initialize and register agents
medical_agent = MedicalAgent(metadata_store, document_store, vector_store, llm_provider, prompt_registry)
agent_registry.register(medical_agent, AgentMetadata(
    name="medical",
    version="1.0.0",
    description="Medical document extraction and normalization agent",
    input_schema={"patient_id": "str", "document_url": "Optional[str]", "gdrive_file_id": "Optional[str]"},
    output_schema={"success": "bool", "data": "dict"},
    capabilities=["ocr", "entity_extraction", "normalization"],
    required_services=["OCRProvider"]
))

repo_analyzer = RepoAnalyzerAgent(metadata_store, document_store, vector_store, LiteLLMRouter(), prompt_registry)
agent_registry.register(repo_analyzer, AgentMetadata(
    name="repo_analyzer",
    version="1.0.0",
    description="Repository analysis and code improvement agent",
    input_schema={"repo_path": "str", "complexity_score": "Optional[int]"},
    output_schema={"issues_found": "list", "suggested_fixes": "list"},
    capabilities=["code_analysis", "vulnerability_detection"],
    required_services=[]
))

simple_chat = SimpleChatAgent(metadata_store, document_store, vector_store, llm_provider, prompt_registry)
agent_registry.register(simple_chat, AgentMetadata(
    name="simple_chat",
    version="1.0.0",
    description="Simple conversational agent",
    input_schema={"message": "str"},
    output_schema={"response": "str"},
    capabilities=["conversation"],
    required_services=[]
))

job_agent = JobAgent(metadata_store, document_store, vector_store, llm_provider, prompt_registry)
agent_registry.register(job_agent, AgentMetadata(
    name="job",
    version="1.0.0",
    description="Job domain agent for ingestion, optimization and tracking",
    input_schema={"workflow": "str", "job_url": "Optional[str]", "resume_id": "Optional[str]"},
    output_schema={"success": "bool", "data": "dict"},
    capabilities=["job_scraping", "resume_parsing", "resume_optimization"],
    required_services=["LinkedInJobIngestionService", "JobDescriptionParser", "ResumeOptimizer"]
))

from core.execution.setup import setup_platform
from core.execution.registry import agent_registry

# Initialize platform and get shared instances
runner, service_context = setup_platform()

# Shortcuts for easy import
metadata_store = service_context.metadata_store
document_store = service_context.document_store
vector_store = service_context.vector_store
llm_provider = service_context.llm_provider
prompt_registry = service_context.prompt_registry

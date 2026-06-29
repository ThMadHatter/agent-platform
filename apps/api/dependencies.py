from core.execution.setup import setup_platform
from core.execution.registry import agent_registry
from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from core.config import settings

# Initialize platform and get shared instances
runner, service_context = setup_platform()

# Shortcuts for easy import
metadata_store = service_context.metadata_store

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if not settings.agent_platform_auth_enabled:
        return None

    if not settings.agent_platform_api_key:
        raise HTTPException(
            status_code=500,
            detail="AGENT_PLATFORM_API_KEY is not configured on the server."
        )

    if not api_key or not api_key.startswith("Bearer "):
         raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key. Use 'Bearer <key>'"
        )

    token = api_key.split("Bearer ")[-1]
    if token != settings.agent_platform_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key."
        )

    return token
document_store = service_context.document_store
vector_store = service_context.vector_store
llm_provider = service_context.llm_provider
prompt_registry = service_context.prompt_registry

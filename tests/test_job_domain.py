import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from agents.job.agent import JobAgent
from core.execution.runner import AgentRunner
from core.execution.registry import agent_registry

from apps.api.dependencies import agent_registry

@pytest.mark.asyncio
async def test_job_agent_registration():
    agent = agent_registry.get_agent("job")
    assert agent is not None
    assert agent.name == "job"

    metadata = agent_registry.get_metadata("job")
    assert metadata.name == "job"
    assert "job_scraping" in metadata.capabilities

@pytest.mark.asyncio
async def test_job_agent_workflow_selection():
    from core.services.context import ServiceContext
    metadata_store = MagicMock()
    document_store = MagicMock()
    vector_store = MagicMock()
    llm_provider = MagicMock()
    prompt_registry = MagicMock()

    context_obj = ServiceContext(
        metadata_store=metadata_store,
        document_store=document_store,
        vector_store=vector_store,
        llm_provider=llm_provider,
        prompt_registry=prompt_registry
    )

    agent = JobAgent(context_obj)

    # Test planning for different workflows (including deprecated ones)
    context = {"input": MagicMock(workflow="linkedin_ingestion")}
    plan = await agent.plan(context)
    assert any(step["step"] == "resolve_and_parse_job" for step in plan)

    context = {"input": MagicMock(workflow="resume_optimization")}
    plan = await agent.plan(context)
    assert any(step["step"] == "generate_cv_data" for step in plan)

    context = {"input": MagicMock(workflow="job_parse")}
    plan = await agent.plan(context)
    assert any(step["step"] == "resolve_and_parse_job" for step in plan)

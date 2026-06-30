import asyncio
import uuid
from agents.job.agent import JobAgent, JobAgentInput
from core.services.context import ServiceContext
from unittest.mock import MagicMock, AsyncMock

async def smoke_test_job_parse():
    # Setup mocks
    metadata_store = MagicMock()
    document_store = MagicMock()
    vector_store = MagicMock()
    llm_provider = MagicMock()
    prompt_registry = MagicMock()

    context = ServiceContext(
        metadata_store=metadata_store,
        document_store=document_store,
        vector_store=vector_store,
        llm_provider=llm_provider,
        prompt_registry=prompt_registry
    )

    # Mock LLM response
    mock_response = MagicMock()
    mock_response.content = {
        "title": "Software Engineer",
        "company": "Test Co",
        "location": "Remote",
        "tech_stack": ["Python", "SQL"],
        "responsibilities": ["Coding", "Testing"]
    }
    llm_provider.generate_structured = AsyncMock(return_value=mock_response)
    prompt_registry.render = MagicMock(return_value="Mocked prompt")

    agent = JobAgent(context)

    # Mock execution metadata
    execution_id = str(uuid.uuid4())
    input_data = {
        "workflow": "job_parse",
        "job_content": "We are looking for a Software Engineer at Test Co. You should know Python and SQL."
    }

    metadata_store.get_execution = AsyncMock(return_value={
        "id": execution_id,
        "input_data": input_data
    })

    mock_session = AsyncMock()
    metadata_store.async_session = MagicMock()
    metadata_store.async_session.return_value.__aenter__.return_value = mock_session

    mock_job = MagicMock()
    mock_job.id = "mock-job-id"
    mock_session.refresh = AsyncMock()

    from unittest.mock import patch
    with patch("agents.job.agent.JobRepository") as MockRepo:
        mock_repo_inst = MockRepo.return_value
        mock_repo_inst.save_job = AsyncMock(return_value=mock_job)

        # Manual check: agent.py imports JobRepository from .repository
        # So it should be available in agents.job.agent

        plan_context = {"input": JobAgentInput(**input_data)}
        plan = await agent.plan(plan_context)
        result = await agent.execute(plan, execution_id)

        print(f"Result job_parse: {result}")
        assert result["parsed_job"]["title"] == "Software Engineer"
        assert result["job_id"] == "mock-job-id"
        print("Smoke test job_parse passed!")

async def smoke_test_cv_ingest():
    # Setup mocks
    metadata_store = MagicMock()
    document_store = MagicMock()
    vector_store = MagicMock()
    llm_provider = MagicMock()
    prompt_registry = MagicMock()

    context = ServiceContext(
        metadata_store=metadata_store,
        document_store=document_store,
        vector_store=vector_store,
        llm_provider=llm_provider,
        prompt_registry=prompt_registry
    )

    # Mock LLM response for resume_parser.j2
    mock_response = MagicMock()
    mock_response.content = {
        "items": [
            {
                "type": "experience",
                "title": "Software Engineer at Google",
                "content": "Built scalable systems using Go and Kubernetes.",
                "metadata": {"company": "Google", "years": 3}
            }
        ]
    }
    llm_provider.generate_structured = AsyncMock(return_value=mock_response)
    llm_provider.embed = AsyncMock(return_value=[0.1]*1536)
    prompt_registry.render = MagicMock(return_value="Mocked resume prompt")
    vector_store.upsert = AsyncMock()

    agent = JobAgent(context)

    execution_id = str(uuid.uuid4())
    input_data = {
        "workflow": "cv_ingest",
        "resume_content": "I worked at Google as a Software Engineer."
    }

    metadata_store.get_execution = AsyncMock(return_value={"id": execution_id, "input_data": input_data})
    mock_session = AsyncMock()
    metadata_store.async_session = MagicMock()
    metadata_store.async_session.return_value.__aenter__.return_value = mock_session

    from unittest.mock import patch
    with patch("agents.job.agent.JobRepository") as MockRepo:
        mock_repo_inst = MockRepo.return_value
        mock_repo_inst.save_cv_knowledge_item = AsyncMock()

        plan_context = {"input": JobAgentInput(**input_data)}
        plan = await agent.plan(plan_context)
        result = await agent.execute(plan, execution_id)

        print(f"Result cv_ingest: {result}")
        assert result["ingested_items_count"] == 1
        print("Smoke test cv_ingest passed!")

async def smoke_test_cv_match():
    # Setup mocks
    metadata_store = MagicMock()
    document_store = MagicMock()
    vector_store = MagicMock()
    llm_provider = MagicMock()
    prompt_registry = MagicMock()

    context = ServiceContext(
        metadata_store=metadata_store,
        document_store=document_store,
        vector_store=vector_store,
        llm_provider=llm_provider,
        prompt_registry=prompt_registry
    )

    # Mock LLM response for cv_matcher.j2
    mock_response = MagicMock()
    mock_response.content = {
        "score": 85,
        "strengths": ["Strong Python skills"],
        "gaps": [],
        "justification": "Good match.",
        "classification": {}
    }
    llm_provider.generate_structured = AsyncMock(return_value=mock_response)
    llm_provider.embed = AsyncMock(return_value=[0.1]*1536)
    prompt_registry.render = MagicMock(return_value="Mocked match prompt")
    vector_store.search = AsyncMock(return_value=[])

    agent = JobAgent(context)

    execution_id = str(uuid.uuid4())
    input_data = {
        "workflow": "cv_match",
        "resume_profile_id": "matteo-default",
        "parsed_job": {"title": "Senior AI Engineer", "tech_stack": ["Python"]}
    }

    metadata_store.get_execution = AsyncMock(return_value={"id": execution_id, "input_data": input_data})
    mock_session = AsyncMock()
    metadata_store.async_session = MagicMock()
    metadata_store.async_session.return_value.__aenter__.return_value = mock_session

    from unittest.mock import patch
    with patch("agents.job.agent.JobRepository") as MockRepo:
        mock_repo_inst = MockRepo.return_value
        mock_repo_inst.save_match_result = AsyncMock(return_value=MagicMock(id="mock-match-id"))

        plan_context = {"input": JobAgentInput(**input_data)}
        plan = await agent.plan(plan_context)
        result = await agent.execute(plan, execution_id)

        print(f"Result cv_match: {result}")
        assert result["score"] == 85
        print("Smoke test cv_match passed!")

async def run_all():
    await smoke_test_job_parse()
    await smoke_test_cv_ingest()
    await smoke_test_cv_match()

if __name__ == "__main__":
    asyncio.run(run_all())

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.coding.analyzer_agent import RepoAnalyzerAgent, RepoAnalyzerInput
from core.llm.litellm_client import LiteLLMRouter
from core.llm.base import LLMResponse

@pytest.fixture
def mock_stores():
    metadata_store = MagicMock()
    metadata_store.record_usage = AsyncMock()
    metadata_store.save_artifact = AsyncMock()
    metadata_store.get_execution = AsyncMock()

    document_store = MagicMock()
    document_store.download = AsyncMock()

    vector_store = MagicMock()
    vector_store.upsert = AsyncMock()

    return metadata_store, document_store, vector_store

@pytest.fixture
def mock_router():
    router = MagicMock(spec=LiteLLMRouter)
    router.route_and_execute = AsyncMock(return_value=LLMResponse(
        content='{"issues_found": [{"file": "main.py", "issue": "test", "severity": "low"}], "suggested_fixes": []}',
        raw_response={"model": "ollama/qwen3"},
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20
    ))
    return router

@pytest.fixture
def mock_registry():
    return MagicMock()

@pytest.mark.asyncio
async def test_repo_analyzer_agent_lifecycle(mock_stores, mock_router, mock_registry):
    metadata_store, document_store, vector_store = mock_stores
    agent = RepoAnalyzerAgent(metadata_store, document_store, vector_store, mock_router, mock_registry)

    # 1. Validate
    input_data = {"repo_path": "test/repo", "complexity_score": 3}
    validated_input = await agent.validate(input_data)
    assert isinstance(validated_input, RepoAnalyzerInput)
    assert validated_input.repo_path == "test/repo"
    assert validated_input.complexity_score == 3

    # 2. Retrieve Context
    context = await agent.retrieve_context(validated_input)
    assert context["repo_path"] == "test/repo"
    assert "files" in context

    # 3. Plan
    plan = await agent.plan(context)
    assert len(plan) == 3

    # 4. Execute
    execution_id = "test-exec-id"
    metadata_store.get_execution.return_value = {"input_data": input_data}

    results = await agent.execute(plan, execution_id)

    assert "issues_found" in results
    assert "suggested_fixes" in results
    mock_router.route_and_execute.assert_called_once()
    metadata_store.record_usage.assert_called_once()
    metadata_store.save_artifact.assert_called_once()

    # 5. Validate Output
    output = await agent.validate_output(results)
    assert output.success is True
    assert output.data == results

    # 6. Persist
    await agent.persist(output, execution_id)
    vector_store.upsert.assert_called_once()

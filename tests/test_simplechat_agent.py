import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.simplechat.agent import SimpleChatAgent, SimpleChatInput
from core.llm.base import LLMResponse

@pytest.fixture
def mock_stores():
    metadata_store = MagicMock()
    metadata_store.record_usage = AsyncMock()
    metadata_store.save_artifact = AsyncMock()
    metadata_store.get_execution = AsyncMock()

    document_store = MagicMock()
    vector_store = MagicMock()
    vector_store.upsert = AsyncMock()

    return metadata_store, document_store, vector_store

@pytest.fixture
def mock_llm():
    provider = MagicMock()
    provider.generate = AsyncMock(return_value=LLMResponse(
        content="Hello! I am a helpful assistant.",
        raw_response={"model": "mock-model"},
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20
    ))
    return provider

@pytest.mark.asyncio
async def test_simple_chat_agent_lifecycle(mock_stores, mock_llm):
    metadata_store, document_store, vector_store = mock_stores
    agent = SimpleChatAgent(metadata_store, document_store, vector_store, mock_llm, MagicMock())

    # 1. Validate
    input_data = {"message": "Hi there!"}
    validated_input = await agent.validate(input_data)
    assert isinstance(validated_input, SimpleChatInput)
    assert validated_input.message == "Hi there!"

    # 2. Retrieve Context
    context = await agent.retrieve_context(validated_input)
    assert context["message"] == "Hi there!"

    # 3. Plan
    plan = await agent.plan(context)
    assert len(plan) == 1

    # 4. Execute
    execution_id = "test-exec-id"
    metadata_store.get_execution.return_value = {"input_data": input_data}

    results = await agent.execute(plan, execution_id)

    assert "response" in results
    assert results["response"] == "Hello! I am a helpful assistant."
    mock_llm.generate.assert_called_once()
    metadata_store.record_usage.assert_called_once()

    # 5. Validate Output
    output = await agent.validate_output(results)
    assert output.success is True
    assert output.data == results

    # 6. Persist
    await agent.persist(output, execution_id)
    vector_store.upsert.assert_called_once()

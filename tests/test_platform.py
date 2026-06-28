import pytest
import asyncio
from core.execution.retry import RetryEngine
from core.execution.registry import AgentRegistry, AgentMetadata
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_retry_engine_success():
    engine = RetryEngine(max_retries=2, base_delay=0.1)
    mock_func = MagicMock(side_effect=[Exception("Fail"), "Success"])

    # We need to wrap mock_func in an async function if RetryEngine expects coroutines
    async def async_mock_func():
        return mock_func()

    result = await engine.execute_with_retry(async_mock_func)
    assert result == "Success"
    assert mock_func.call_count == 2

@pytest.mark.asyncio
async def test_retry_engine_max_retries():
    engine = RetryEngine(max_retries=1, base_delay=0.1)
    async def failing_func():
        raise Exception("Permanent Fail")

    with pytest.raises(Exception, match="Permanent Fail"):
        await engine.execute_with_retry(failing_func)

def test_agent_registry():
    registry = AgentRegistry()
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    metadata = AgentMetadata(
        name="test_agent",
        version="1.0",
        description="test",
        input_schema={},
        output_schema={},
        capabilities=[],
        required_services=[]
    )

    registry.register(mock_agent, metadata)
    assert registry.get_agent("test_agent") == mock_agent
    assert registry.get_metadata("test_agent").version == "1.0"
    assert len(registry.list_agents()) == 1

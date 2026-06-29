import pytest
from unittest.mock import AsyncMock, MagicMock
from core.execution.runner import AgentRunner
from agents.shared.base import BaseAgent, AgentOutput, AgentInput

class MockAgentInput(AgentInput):
    message: str

class MockAgent(BaseAgent):
    async def validate(self, input_data):
        return MockAgentInput(**input_data)

    async def retrieve_context(self, validated_input):
        return {"ctx": "data"}

    async def plan(self, context):
        return [{"step": "test"}]

    async def execute(self, plan, execution_id):
        return {"result": "ok"}

    async def validate_output(self, raw_output):
        return AgentOutput(success=True, data=raw_output)

    async def persist(self, output, execution_id):
        pass

@pytest.mark.asyncio
async def test_runner_sync_execution():
    metadata_store = AsyncMock()
    metadata_store.save_execution = AsyncMock()
    metadata_store.update_execution = AsyncMock()
    metadata_store.add_step = AsyncMock()
    metadata_store.update_step = AsyncMock()
    metadata_store.get_execution = AsyncMock(return_value={"start_time": "2023-01-01T00:00:00"})

    runner = AgentRunner(metadata_store)
    agent = MockAgent(name="test_agent", context=MagicMock())

    execution_id = await runner.run(agent, {"message": "hello"})

    assert execution_id is not None
    assert metadata_store.save_execution.called
    assert metadata_store.update_execution.call_count >= 2

    # Check if final status was succeeded
    # update_execution(execution_id, update_data)
    last_call = metadata_store.update_execution.call_args_list[-1]
    update_data = last_call[0][1] # second positional argument
    assert update_data["status"] == "succeeded"

@pytest.mark.asyncio
async def test_runner_failure():
    metadata_store = AsyncMock()
    metadata_store.save_execution = AsyncMock()
    metadata_store.update_execution = AsyncMock()
    metadata_store.add_step = AsyncMock()
    metadata_store.update_step = AsyncMock()

    runner = AgentRunner(metadata_store)
    agent = MockAgent(name="fail_agent", context=MagicMock())
    agent.execute = AsyncMock(side_effect=ValueError("Test Error"))

    execution_id = await runner.run(agent, {"message": "hello"})

    # Check if final status was failed
    last_call = metadata_store.update_execution.call_args_list[-1]
    update_data = last_call[0][1] # second positional argument
    assert update_data["status"] == "failed"
    assert "Test Error" in update_data["error_message"]

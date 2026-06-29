import pytest
from core.execution.registry import agent_registry
from core.execution.setup import setup_platform

def test_registry_initialization():
    # setup_platform registers agents
    setup_platform()
    agents = agent_registry.list_agents()

    agent_ids = [a.id for a in agents]
    assert "medical" in agent_ids
    assert "repo_analyzer" in agent_ids
    assert "simple_chat" in agent_ids
    assert "job" in agent_ids

def test_get_agent_metadata():
    setup_platform()
    metadata = agent_registry.get_metadata("simple_chat")
    assert metadata is not None
    assert metadata.id == "simple_chat"
    assert "conversation" in metadata.capabilities

def test_unknown_agent():
    setup_platform()
    assert agent_registry.get_agent("non_existent") is None
    assert agent_registry.get_metadata("non_existent") is None

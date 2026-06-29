import pytest
from core.execution.registry import agent_registry
from core.execution.setup import setup_platform

def test_registry_initialization():
    # setup_platform registers agents
    setup_platform()
    agents = agent_registry.list_agents()

    agent_names = [a.name for a in agents]
    assert "medical" in agent_names
    assert "repo_analyzer" in agent_names
    assert "simple_chat" in agent_names
    assert "job" in agent_names

def test_get_agent_metadata():
    setup_platform()
    metadata = agent_registry.get_metadata("simple_chat")
    assert metadata is not None
    assert metadata.name == "simple_chat"
    assert "conversation" in metadata.capabilities

def test_unknown_agent():
    setup_platform()
    assert agent_registry.get_agent("non_existent") is None
    assert agent_registry.get_metadata("non_existent") is None

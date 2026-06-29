from typing import Any, Dict, List, Type, Optional, Literal
from pydantic import BaseModel
from agents.shared.base import BaseAgent

class AgentMetadata(BaseModel):
    id: str
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    capabilities: List[str]
    required_services: List[str]
    execution_modes: List[Literal["sync", "async"]] = ["sync", "async"]
    tags: List[str] = []
    backend_type: Literal["litellm", "openhands", "custom"] = "litellm"

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._metadata: Dict[str, AgentMetadata] = {}

    def register(self, agent: BaseAgent, metadata: AgentMetadata):
        self._agents[metadata.id] = agent
        self._metadata[metadata.id] = metadata

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        return self._metadata.get(agent_id)

    def list_agents(self) -> List[AgentMetadata]:
        return list(self._metadata.values())

agent_registry = AgentRegistry()

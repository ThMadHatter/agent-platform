from typing import Any, Dict, List, Type, Optional
from pydantic import BaseModel
from agents.shared.base import BaseAgent

class AgentMetadata(BaseModel):
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    capabilities: List[str]
    required_services: List[str]

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._metadata: Dict[str, AgentMetadata] = {}

    def register(self, agent: BaseAgent, metadata: AgentMetadata):
        self._agents[agent.name] = agent
        self._metadata[agent.name] = metadata

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def get_metadata(self, name: str) -> Optional[AgentMetadata]:
        return self._metadata.get(name)

    def list_agents(self) -> List[AgentMetadata]:
        return list(self._metadata.values())

agent_registry = AgentRegistry()

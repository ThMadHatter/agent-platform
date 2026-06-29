from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from core.services.context import ServiceContext

class AgentInput(BaseModel):
    pass

class AgentOutput(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None

class BaseAgent(ABC):
    def __init__(self, name: str, context: ServiceContext):
        self.name = name
        self.context = context

    @abstractmethod
    async def validate(self, input_data: Dict[str, Any]) -> AgentInput:
        pass

    @abstractmethod
    async def retrieve_context(self, validated_input: AgentInput) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def execute(self, plan: List[Dict[str, Any]], execution_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def validate_output(self, raw_output: Dict[str, Any]) -> AgentOutput:
        pass

    @abstractmethod
    async def persist(self, output: AgentOutput, execution_id: str) -> None:
        pass

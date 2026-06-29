import logging
from typing import Any, Dict, List, Optional
from pydantic import Field

from agents.shared.base import BaseAgent, AgentInput, AgentOutput
from core.services.context import ServiceContext

logger = logging.getLogger(__name__)

class SimpleChatInput(AgentInput):
    message: str
    complexity_score: Optional[int] = Field(default=3, description="Task complexity (1-10)")

class SimpleChatAgent(BaseAgent):
    def __init__(self, context: ServiceContext):
        super().__init__(name="simple_chat", context=context)

    async def validate(self, input_data: Dict[str, Any]) -> SimpleChatInput:
        return SimpleChatInput(**input_data)

    async def retrieve_context(self, validated_input: SimpleChatInput) -> Dict[str, Any]:
        return {"message": validated_input.message}

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"step": "chat", "action": "generate_response"}]

    async def execute(self, plan: List[Dict[str, Any]], execution_id: str) -> Dict[str, Any]:
        execution_info = await self.context.metadata_store.get_execution(execution_id)
        input_data = SimpleChatInput(**execution_info["input_data"])

        system_prompt = "You are a helpful assistant. Keep your answers concise and clear."

        llm_response = await self.context.llm_provider.generate(
            prompt=input_data.message,
            system_prompt=system_prompt
        )

        await self.context.metadata_store.record_usage({
            "execution_id": execution_id,
            "provider": "litellm",
            "model": llm_response.raw_response.get("model", "unknown"),
            "prompt_tokens": llm_response.prompt_tokens,
            "completion_tokens": llm_response.completion_tokens,
            "total_tokens": llm_response.total_tokens,
            "cost": llm_response.cost
        })

        return {"response": llm_response.content}

    async def validate_output(self, raw_output: Dict[str, Any]) -> AgentOutput:
        return AgentOutput(success=True, data=raw_output)

    async def persist(self, output: AgentOutput, execution_id: str) -> None:
        await self.context.vector_store.upsert(
            collection="chat_history",
            points=[{"id": execution_id, "data": output.data}]
        )
        logger.info(f"Persisted chat response for execution {execution_id}")

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from core.storage.base import MetadataStore
from database.models import AgentExecution, AgentStep, Artifact, LLMUsage
from core.config import settings

class PostgreSQLMetadataStore(MetadataStore):
    def __init__(self, database_url: str = settings.database_url):
        self.engine = create_async_engine(database_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def save_execution(self, execution_data: Dict[str, Any]) -> str:
        async with self.async_session() as session:
            execution = AgentExecution(**execution_data)
            session.add(execution)
            await session.commit()
            return execution.id

    async def update_execution(self, execution_id: str, update_data: Dict[str, Any]) -> None:
        async with self.async_session() as session:
            stmt = update(AgentExecution).where(AgentExecution.id == execution_id).values(**update_data)
            await session.execute(stmt)
            await session.commit()

    async def add_step(self, execution_id: str, step_data: Dict[str, Any]) -> str:
        async with self.async_session() as session:
            step = AgentStep(execution_id=execution_id, **step_data)
            session.add(step)
            await session.commit()
            return step.id

    async def update_step(self, step_id: str, update_data: Dict[str, Any]) -> None:
        async with self.async_session() as session:
            stmt = update(AgentStep).where(AgentStep.id == step_id).values(**update_data)
            await session.execute(stmt)
            await session.commit()

    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        async with self.async_session() as session:
            stmt = select(AgentExecution).where(AgentExecution.id == execution_id)
            result = await session.execute(stmt)
            execution = result.scalar_one_or_none()
            if execution:
                return {
                    "id": execution.id,
                    "agent_name": execution.agent_name,
                    "status": execution.status,
                    "input_data": execution.input_data,
                    "output_data": execution.output_data,
                    "error_message": execution.error_message,
                "client_request_id": execution.client_request_id,
                "callback_url": execution.callback_url,
                    "start_time": execution.start_time,
                    "end_time": execution.end_time,
                    "duration_seconds": execution.duration_seconds
                }
            return None

    async def list_executions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            stmt = select(AgentExecution).order_by(AgentExecution.start_time.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            executions = result.scalars().all()
            return [
                {
                    "id": e.id,
                    "agent_name": e.agent_name,
                    "status": e.status,
                    "client_request_id": e.client_request_id,
                    "start_time": e.start_time,
                    "duration_seconds": e.duration_seconds
                } for e in executions
            ]

    async def get_execution_by_client_request_id(self, agent_id: str, client_request_id: str) -> Optional[Dict[str, Any]]:
        async with self.async_session() as session:
            stmt = select(AgentExecution).where(
                AgentExecution.agent_name == agent_id,
                AgentExecution.client_request_id == client_request_id
            )
            result = await session.execute(stmt)
            execution = result.scalar_one_or_none()
            if execution:
                return {
                    "id": execution.id,
                    "agent_name": execution.agent_name,
                    "status": execution.status,
                    "input_data": execution.input_data,
                    "output_data": execution.output_data,
                    "error_message": execution.error_message,
                    "client_request_id": execution.client_request_id,
                    "callback_url": execution.callback_url,
                    "start_time": execution.start_time,
                    "end_time": execution.end_time,
                    "duration_seconds": execution.duration_seconds
                }
            return None

    async def save_artifact(self, execution_id: str, name: str, content_type: str, data: Dict[str, Any]) -> str:
        async with self.async_session() as session:
            artifact = Artifact(execution_id=execution_id, name=name, content_type=content_type, data=data)
            session.add(artifact)
            await session.commit()
            return artifact.id

    async def record_usage(self, usage_data: Dict[str, Any]) -> None:
        async with self.async_session() as session:
            usage = LLMUsage(**usage_data)
            session.add(usage)
            await session.commit()

from datetime import datetime
from typing import List, Optional, Any, Dict
from sqlalchemy import String, DateTime, ForeignKey, JSON, Float, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid

class Base(DeclarativeBase):
    pass

class AgentConfig(Base):
    __tablename__ = "agent_configs"

    agent_name: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String) # gemini, openai, etc.
    model_name: Mapped[str] = mapped_column(String)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    system_prompt: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String) # pending, running, retrying, completed, failed, cancelled
    input_data: Mapped[dict] = mapped_column(JSON)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    client_request_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    callback_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    steps: Mapped[List["AgentStep"]] = relationship(back_populates="execution", cascade="all, delete-orphan")
    artifacts: Mapped[List["Artifact"]] = relationship(back_populates="execution", cascade="all, delete-orphan")
    usage: Mapped[List["LLMUsage"]] = relationship(back_populates="execution", cascade="all, delete-orphan")

class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(ForeignKey("agent_executions.id"))
    step_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    input_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    execution: Mapped["AgentExecution"] = relationship(back_populates="steps")

class LLMUsage(Base):
    __tablename__ = "llm_usage"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(ForeignKey("agent_executions.id"))
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    execution: Mapped["AgentExecution"] = relationship(back_populates="usage")

class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(ForeignKey("agent_executions.id"))
    name: Mapped[str] = mapped_column(String) # ocr_result, summary, extracted_json
    content_type: Mapped[str] = mapped_column(String) # text, json, html
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    execution: Mapped["AgentExecution"] = relationship(back_populates="artifacts")

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


class ResumeProfile(Base):
    __tablename__ = "resume_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g., "matteo-default"
    name: Mapped[str] = mapped_column(String)
    contacts: Mapped[dict] = mapped_column(JSON, default=list)  # list of contact objects
    languages: Mapped[dict] = mapped_column(JSON, default=list)  # list of language objects
    summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    normalized_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class JobMatch(Base):
    __tablename__ = "job_matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("agent_executions.id"))
    resume_profile_id: Mapped[str] = mapped_column(ForeignKey("resume_profiles.id"), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    match_data: Mapped[dict] = mapped_column(JSON, default=dict)
    retrieved_evidence: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CVGenerationRun(Base):
    __tablename__ = "cv_generation_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("agent_executions.id"), index=True)
    resume_profile_id: Mapped[str] = mapped_column(ForeignKey("resume_profiles.id"))
    template_id: Mapped[str] = mapped_column(String, default="lavandula")
    language: Mapped[str] = mapped_column(String, default="en")
    target_pages: Mapped[int] = mapped_column(Integer, default=2)
    match_id: Mapped[Optional[str]] = mapped_column(ForeignKey("job_matches.id"), nullable=True)
    strategy_data: Mapped[dict] = mapped_column(JSON, default=dict)
    typst_data: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="pending")
    artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CVKnowledgeItem(Base):
    __tablename__ = "cv_knowledge_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_profile_id: Mapped[str] = mapped_column(ForeignKey("resume_profiles.id"), index=True)
    type: Mapped[str] = mapped_column(String, index=True)  # experience|project|skill|achievement|education
    title: Mapped[str] = mapped_column(String)
    canonical_text: Mapped[str] = mapped_column(String)
    item_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class ErrorResponse(BaseModel):
    error: ErrorDetail

class ExecutionResponse(BaseModel):
    execution_id: str
    agent_id: str
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    result: Optional[Dict[str, Any]] = None
    error: Optional[ErrorDetail] = None
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AsyncExecutionResponse(BaseModel):
    execution_id: str
    agent_id: str
    status: Literal["queued"]
    poll_url: str

class AgentResponse(BaseModel):
    id: str
    name: str
    version: str
    description: str
    capabilities: List[str]
    execution_modes: List[Literal["sync", "async"]]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_services: List[str]

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]

class AgentRunInput(BaseModel):
    input_data: Dict[str, Any]
    client_request_id: Optional[str] = None
    callback_url: Optional[str] = None

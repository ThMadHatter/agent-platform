from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Header
from typing import Any, Dict, List, Optional
from core.execution.registry import agent_registry
from apps.api.dependencies import runner, metadata_store
from apps.api.schemas import (
    AgentResponse,
    ExecutionResponse,
    AsyncExecutionResponse,
    ErrorResponse,
    ErrorDetail,
    AgentRunInput
)
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

@router.get("", response_model=List[AgentResponse])
async def list_agents():
    agents = agent_registry.list_agents()
    return [
        AgentResponse(
            id=a.id,
            name=a.name,
            version=a.version,
            description=a.description,
            capabilities=a.capabilities,
            execution_modes=a.execution_modes,
            input_schema=a.input_schema,
            output_schema=a.output_schema,
            required_services=a.required_services
        ) for a in agents
    ]

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    metadata = agent_registry.get_metadata(agent_id)
    if not metadata:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "UNKNOWN_AGENT",
                    "message": f"Agent with ID '{agent_id}' not found.",
                    "details": {"agent_id": agent_id}
                }
            }
        )
    return AgentResponse(
        id=metadata.id,
        name=metadata.name,
        version=metadata.version,
        description=metadata.description,
        capabilities=metadata.capabilities,
        execution_modes=metadata.execution_modes,
        input_schema=metadata.input_schema,
        output_schema=metadata.output_schema,
        required_services=metadata.required_services
    )

async def _get_idempotent_execution(agent_id: str, run_input: AgentRunInput, idempotency_key: Optional[str] = None):
    client_request_id = run_input.client_request_id or idempotency_key
    if not client_request_id:
        return None

    existing = await metadata_store.get_execution_by_client_request_id(agent_id, client_request_id)
    if existing:
        # Check if payload matches
        if existing["input_data"] != run_input.input_data:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": {
                        "code": "IDEMPOTENCY_CONFLICT",
                        "message": "This idempotency key was already used with a different payload.",
                        "details": {"idempotency_key": client_request_id}
                    }
                }
            )
        return existing
    return None

def _map_status(status: str) -> str:
    # Map internal statuses to standard API statuses
    mapping = {
        "pending": "queued",
        "queued": "queued",
        "running": "running",
        "retrying": "running",
        "completed": "succeeded",
        "succeeded": "succeeded",
        "failed": "failed",
        "cancelled": "cancelled"
    }
    return mapping.get(status, "queued")

@router.post("/{agent_id}/run", response_model=ExecutionResponse)
async def run_agent_sync(
    agent_id: str,
    run_input: AgentRunInput,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail={"error": {"code": "UNKNOWN_AGENT", "message": f"Agent {agent_id} not found"}})

    # Check idempotency
    existing = await _get_idempotent_execution(agent_id, run_input, idempotency_key)
    if existing:
        return ExecutionResponse(
            execution_id=existing["id"],
            agent_id=agent_id,
            status=_map_status(existing["status"]),
            result=existing.get("output_data"),
            error=ErrorDetail(code="AGENT_EXECUTION_FAILED", message=existing.get("error_message"), details={}) if existing.get("status") == "failed" else None,
            duration_seconds=existing.get("duration_seconds"),
            started_at=existing.get("start_time"),
            completed_at=existing.get("end_time")
        )

    try:
        execution_id = str(uuid.uuid4())
        client_request_id = run_input.client_request_id or idempotency_key

        # Save initial state
        await metadata_store.save_execution({
            "id": execution_id,
            "agent_name": agent_id,
            "status": "queued",
            "input_data": run_input.input_data,
            "client_request_id": client_request_id,
            "callback_url": run_input.callback_url,
            "start_time": datetime.utcnow()
        })

        await runner.run(agent, run_input.input_data, execution_id)
        execution = await metadata_store.get_execution(execution_id)

        return ExecutionResponse(
            execution_id=execution_id,
            agent_id=agent_id,
            status=_map_status(execution.get("status")),
            result=execution.get("output_data"),
            error=ErrorDetail(code="AGENT_EXECUTION_FAILED", message=execution.get("error_message"), details={}) if execution.get("status") == "failed" else None,
            duration_seconds=execution.get("duration_seconds"),
            started_at=execution.get("start_time"),
            completed_at=execution.get("end_time")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}})

@router.post("/{agent_id}/run-async", response_model=AsyncExecutionResponse)
async def run_agent_async(
    agent_id: str,
    run_input: AgentRunInput,
    background_tasks: BackgroundTasks,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail={"error": {"code": "UNKNOWN_AGENT", "message": f"Agent {agent_id} not found"}})

    # Check idempotency
    existing = await _get_idempotent_execution(agent_id, run_input, idempotency_key)
    if existing:
        return AsyncExecutionResponse(
            execution_id=existing["id"],
            agent_id=agent_id,
            status="queued", # Even if it's already running/succeeded, we return the same initiation response
            poll_url=f"/api/v1/executions/{existing['id']}"
        )

    execution_id = str(uuid.uuid4())
    client_request_id = run_input.client_request_id or idempotency_key

    # Pre-register execution
    await metadata_store.save_execution({
        "id": execution_id,
        "agent_name": agent_id,
        "status": "queued",
        "input_data": run_input.input_data,
        "client_request_id": client_request_id,
        "callback_url": run_input.callback_url,
        "start_time": datetime.utcnow()
    })

    background_tasks.add_task(runner.run, agent, run_input.input_data, execution_id)

    return AsyncExecutionResponse(
        execution_id=execution_id,
        agent_id=agent_id,
        status="queued",
        poll_url=f"/api/v1/executions/{execution_id}"
    )

# Backward compatibility
@router.post("/{agent_id}/execute")
async def execute_alias(agent_id: str, input_data: Dict[str, Any], background_tasks: BackgroundTasks, request: Request):
    return await run_agent_async(agent_id, AgentRunInput(input_data=input_data), background_tasks, request)

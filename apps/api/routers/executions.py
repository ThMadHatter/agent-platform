from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from apps.api.dependencies import metadata_store
from apps.api.schemas import ExecutionResponse, ErrorDetail

router = APIRouter(prefix="/api/v1/executions", tags=["executions"])

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

@router.get("", response_model=List[Dict[str, Any]])
async def list_executions(limit: int = 100, offset: int = 0):
    return await metadata_store.list_executions(limit, offset)

@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str):
    execution = await metadata_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "EXECUTION_NOT_FOUND",
                    "message": f"Execution with ID '{execution_id}' not found.",
                    "details": {"execution_id": execution_id}
                }
            }
        )

    # Standardize output format
    return ExecutionResponse(
        execution_id=execution.get("id"),
        agent_id=execution.get("agent_name"),
        status=_map_status(execution.get("status")),
        result=execution.get("output_data"),
        error=ErrorDetail(
            code="AGENT_EXECUTION_FAILED",
            message=execution.get("error_message") or "Execution failed without specific error message.",
            details={}
        ) if execution.get("status") == "failed" else None,
        duration_seconds=execution.get("duration_seconds"),
        started_at=execution.get("start_time"),
        completed_at=execution.get("end_time")
    )

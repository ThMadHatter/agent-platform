from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from apps.api.dependencies import metadata_store

router = APIRouter(prefix="/api/v1/executions", tags=["executions"])

@router.get("")
async def list_executions(limit: int = 100, offset: int = 0):
    return await metadata_store.list_executions(limit, offset)

@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    execution = await metadata_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Standardize output format
    return {
        "execution_id": execution.get("id"),
        "agent_id": execution.get("agent_name"),
        "status": execution.get("status"),
        "result": execution.get("output_data"),
        "error": {
            "code": "AGENT_EXECUTION_FAILED",
            "message": execution.get("error_message"),
            "details": {}
        } if execution.get("status") == "failed" else None,
        "timestamps": {
            "started": execution.get("start_time"),
            "completed": execution.get("end_time")
        }
    }

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Any, Dict, List
from core.execution.registry import agent_registry, AgentMetadata
from apps.api.dependencies import runner, metadata_store

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

@router.get("", response_model=List[AgentMetadata])
async def list_agents():
    return agent_registry.list_agents()

@router.get("/{agent_id}", response_model=AgentMetadata)
async def get_agent(agent_id: str):
    metadata = agent_registry.get_metadata(agent_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Agent not found")
    return metadata

@router.post("/{agent_id}/run")
async def run_agent_sync(agent_id: str, input_data: Dict[str, Any]):
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        execution_id = await runner.run(agent, input_data)
        execution = await metadata_store.get_execution(execution_id)

        return {
            "execution_id": execution_id,
            "agent_id": agent_id,
            "status": execution.get("status"),
            "result": execution.get("output_data"),
            "error": {
                "code": "AGENT_EXECUTION_FAILED",
                "message": execution.get("error_message")
            } if execution.get("status") == "failed" else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent_id}/run-async")
async def run_agent_async(agent_id: str, input_data: Dict[str, Any], background_tasks: BackgroundTasks):
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # In a real async system, this would go to a task queue (Celery, etc.)
    # For now, we use FastAPI BackgroundTasks and the runner's internal state management

    import uuid
    from datetime import datetime
    execution_id = str(uuid.uuid4())

    # Pre-register execution so it's visible in GET /executions/{id} immediately
    await metadata_store.save_execution({
        "id": execution_id,
        "agent_name": agent_id,
        "status": "queued",
        "input_data": input_data,
        "start_time": datetime.utcnow()
    })

    background_tasks.add_task(runner.run, agent, input_data, execution_id)

    return {
        "execution_id": execution_id,
        "agent_id": agent_id,
        "status": "queued"
    }

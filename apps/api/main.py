from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Any, Dict, List
import os

from core.config import settings
from core.telemetry.logging import setup_logging
from core.telemetry.tracing import setup_tracing
from apps.api.dependencies import (
    runner,
    metadata_store,
    service_context,
    document_store,
    vector_store,
    llm_provider,
    prompt_registry
)
from core.execution.registry import agent_registry

# Initialize app
app = FastAPI(title=settings.app_name)
setup_logging()
setup_tracing()

templates = Jinja2Templates(directory="apps/api/templates")

# Import and include routers
from apps.api.routers import n8n_webhook, agents, executions
app.include_router(n8n_webhook.router)
app.include_router(agents.router)
app.include_router(executions.router)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/health/db")
async def health_db():
    try:
        from sqlalchemy import text
        async with metadata_store.async_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

@app.get("/health/litellm")
async def health_litellm():
    if not settings.litellm_api_key or not settings.litellm_base_url:
        return {"status": "degraded", "litellm": "config_missing"}
    return {"status": "healthy", "litellm": "configured"}

# Dashboard Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    executions_list = await metadata_store.list_executions(limit=20)
    total = len(executions_list)
    failures = sum(1 for e in executions_list if e["status"] == "failed")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "executions": executions_list,
        "stats": {
            "total": total,
            "failures": failures,
            "success_rate": f"{(total-failures)/total*100:.1f}%" if total > 0 else "0%"
        }
    })

@app.get("/dashboard/executions/{execution_id}", response_class=HTMLResponse)
async def execution_detail(request: Request, execution_id: str):
    execution = await metadata_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return templates.TemplateResponse("execution_detail.html", {
        "request": request,
        "execution": execution
    })

@app.get("/playground", response_class=HTMLResponse)
async def playground(request: Request):
    return templates.TemplateResponse("playground.html", {
        "request": request,
        "agents": [a.name for a in agent_registry.list_agents()]
    })

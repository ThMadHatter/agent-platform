from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Any, Dict, List
import os

from core.config import settings
from core.telemetry.logging import setup_logging
from core.telemetry.tracing import setup_tracing
from apps.api.dependencies import runner, metadata_store, document_store, vector_store, llm_provider, prompt_registry
from agents.medical.agent import MedicalAgent
from agents.coding.analyzer_agent import RepoAnalyzerAgent
from agents.simplechat.agent import SimpleChatAgent
from core.llm.litellm_client import LiteLLMRouter

# Initialize app
app = FastAPI(title=settings.app_name)
setup_logging()
setup_tracing()

templates = Jinja2Templates(directory="apps/api/templates")

# Agent mapping
agents = {
    "medical": MedicalAgent(metadata_store, document_store, vector_store, llm_provider, prompt_registry),
    "repo_analyzer": RepoAnalyzerAgent(metadata_store, document_store, vector_store, LiteLLMRouter(), prompt_registry),
    "simple_chat": SimpleChatAgent(metadata_store, document_store, vector_store, llm_provider, prompt_registry)
}

# Import and include routers
from apps.api.routers import n8n_webhook
app.include_router(n8n_webhook.router)

# API Routes
@app.post("/api/v1/agents/{agent_name}/execute")
async def execute_agent(agent_name: str, input_data: Dict[str, Any]):
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = agents[agent_name]
    execution_id = await runner.run(agent, input_data)
    return {"execution_id": execution_id}

@app.get("/api/v1/executions")
async def list_executions(limit: int = 100, offset: int = 0):
    return await metadata_store.list_executions(limit, offset)

@app.get("/api/v1/executions/{execution_id}")
async def get_execution(execution_id: str):
    execution = await metadata_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

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
    executions = await metadata_store.list_executions(limit=20)
    total = len(executions)
    failures = sum(1 for e in executions if e["status"] == "failed")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "executions": executions,
        "stats": {
            "total": total,
            "failures": failures,
            "success_rate": f"{(total-failures)/total*100:.1f}%" if total > 0 else "0%"
        }
    })

@app.get("/executions/{execution_id}", response_class=HTMLResponse)
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
        "agents": list(agents.keys())
    })

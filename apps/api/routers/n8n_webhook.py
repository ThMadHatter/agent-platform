from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict
import logging

from core.execution.runner import AgentRunner
from core.execution.registry import agent_registry
from apps.api.dependencies import runner, metadata_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks/n8n", tags=["webhooks"])

@router.post("/analyze-repo")
async def analyze_repo_webhook(payload: Dict[str, Any]):
    """
    Webhook endpoint for n8n to trigger RepoAnalyzerAgent.
    Expected payload:
    {
        "repo_path": "https://github.com/user/repo",
        "complexity_score": 5
    }
    """
    logger.info(f"Received n8n webhook for repo analysis: {payload}")

    if "repo_path" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'repo_path' in payload")

    # Get the agent from registry
    agent = agent_registry.get_agent("repo_analyzer")
    if not agent:
        raise HTTPException(status_code=500, detail="RepoAnalyzerAgent not registered")

    try:
        # Run the agent using the platform runner
        execution_id = await runner.run(agent, payload)

        # Wait for completion and return results
        execution_info = await metadata_store.get_execution(execution_id)

        return {
            "status": "success",
            "execution_id": execution_id,
            "results": execution_info.get("output_data")
        }
    except Exception as e:
        logger.error(f"Error executing RepoAnalyzerAgent via webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

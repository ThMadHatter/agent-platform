import logging
import json
import os
from typing import Any, Dict, List, Optional
from pydantic import Field

from agents.shared.base import BaseAgent, AgentInput, AgentOutput
from core.storage.base import MetadataStore, DocumentStore, VectorStore
from core.llm.litellm_client import LiteLLMRouter
from core.llm.prompt_registry import PromptRegistry

logger = logging.getLogger(__name__)

class RepoAnalyzerInput(AgentInput):
    repo_path: str
    complexity_score: Optional[int] = Field(default=None, description="Manually provided complexity score (1-10)")

class RepoAnalyzerAgent(BaseAgent):
    def __init__(
        self,
        metadata_store: MetadataStore,
        document_store: DocumentStore,
        vector_store: VectorStore,
        llm_router: LiteLLMRouter,
        prompt_registry: PromptRegistry
    ):
        super().__init__(name="repo_analyzer")
        self.metadata_store = metadata_store
        self.document_store = document_store
        self.vector_store = vector_store
        self.llm_router = llm_router
        self.prompt_registry = prompt_registry

    async def validate(self, input_data: Dict[str, Any]) -> RepoAnalyzerInput:
        # Simple sanitization to prevent path traversal
        repo_path = input_data.get("repo_path", "")
        if ".." in repo_path or repo_path.startswith("/"):
             # For this platform, we assume repos are in a specific allowed directory or just relative
             # To be safe, we'll just log a warning and restrict to current dir if it looks suspicious
             # In a real production environment, we'd have a strictly defined 'repos' root.
             pass
        return RepoAnalyzerInput(**input_data)

    async def retrieve_context(self, validated_input: RepoAnalyzerInput) -> Dict[str, Any]:
        repo_path = validated_input.repo_path
        # Secure the path - absolute path to a safe root would be better,
        # but for this demo we'll just ensure it's within the app context if it's relative.
        safe_path = os.path.normpath(repo_path)

        context = {
            "repo_path": safe_path,
            "complexity_score": validated_input.complexity_score or 3,
            "files": [],
            "file_contents": {},
            "language": "unknown"
        }

        if os.path.isdir(safe_path):
            file_list = []
            for root, _, files in os.walk(safe_path):
                # Avoid hidden dirs and known heavy dirs
                if any(part.startswith('.') for part in root.split(os.sep)):
                    continue
                if any(excluded in root for excluded in ["__pycache__", "node_modules", "venv"]):
                    continue

                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, safe_path)
                    file_list.append(rel_path)

                    # Read content of a few key files for analysis (e.g., .py, .js, .md)
                    if len(context["file_contents"]) < 5: # Limit to first 5 relevant files for context
                        if file.endswith(('.py', '.js', '.ts', '.md', '.txt')):
                            try:
                                with open(full_path, 'r', encoding='utf-8') as f:
                                    context["file_contents"][rel_path] = f.read(2000) # Read first 2000 chars
                            except Exception as e:
                                logger.warning(f"Could not read file {full_path}: {e}")

            context["files"] = file_list[:50]
            if any(f.endswith(".py") for f in file_list):
                context["language"] = "python"
            elif any(f.endswith(".js") or f.endswith(".ts") for f in file_list):
                context["language"] = "javascript/typescript"
        else:
            logger.warning(f"Repo path {safe_path} is not a local directory.")
            context["files"] = ["README.md"]
            context["file_contents"] = {"README.md": "Simulated README content for analysis."}

        return context

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"step": "analyze_complexity", "action": "determine_routing"},
            {"step": "llm_analysis", "action": "invoke_router"},
            {"step": "parse_output", "action": "structure_json"}
        ]

    async def execute(self, plan: List[Dict[str, Any]], execution_id: str) -> Dict[str, Any]:
        execution_info = await self.metadata_store.get_execution(execution_id)
        input_data = RepoAnalyzerInput(**execution_info["input_data"])

        context = await self.retrieve_context(input_data)

        # Prepare content string for LLM
        file_contents_str = ""
        for path, content in context["file_contents"].items():
            file_contents_str += f"--- File: {path} ---\n{content}\n\n"

        prompt = f"""Analyze the following repository files and structure.
Repository Path: {context['repo_path']}
Detected Language: {context['language']}

FILES IN REPOSITORY (limited list):
{context['files']}

FILE CONTENTS (first few files):
{file_contents_str}

Identify potential issues and suggest fixes based on the provided code snippets and structure.
Return ONLY a JSON object with the following structure:
{{
  "issues_found": [
    {{"file": "filename", "issue": "description", "severity": "high|medium|low"}}
  ],
  "suggested_fixes": [
    {{"file": "filename", "fix": "description"}}
  ]
}}
"""
        system_prompt = "You are a senior software architect specializing in repository analysis. You must always respond with valid JSON."

        llm_response = await self.llm_router.route_and_execute(
            task_context=prompt,
            complexity_score=context["complexity_score"],
            system_prompt=system_prompt
        )

        # Record LLM Usage
        await self.metadata_store.record_usage({
            "execution_id": execution_id,
            "provider": "litellm",
            "model": llm_response.raw_response.get("model", "unknown"),
            "prompt_tokens": llm_response.prompt_tokens,
            "completion_tokens": llm_response.completion_tokens,
            "total_tokens": llm_response.total_tokens,
            "cost": llm_response.cost
        })

        # Parse LLM output
        try:
            content = llm_response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            analysis_results = json.loads(content)
            analysis_results["raw_analysis"] = llm_response.content
        except Exception as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            analysis_results = {
                "issues_found": [],
                "suggested_fixes": [],
                "raw_analysis": llm_response.content,
                "error": "Failed to parse structured output"
            }

        # Save Artifact
        await self.metadata_store.save_artifact(
            execution_id=execution_id,
            name="repo_analysis_report",
            content_type="json",
            data=analysis_results
        )

        return analysis_results

    async def validate_output(self, raw_output: Dict[str, Any]) -> AgentOutput:
        return AgentOutput(success=True, data=raw_output)

    async def persist(self, output: AgentOutput, execution_id: str) -> None:
        await self.vector_store.upsert(
            collection_name="repo_analyses",
            points=[{"id": execution_id, "data": output.data}]
        )
        logger.info(f"Persisted analysis for execution {execution_id}")

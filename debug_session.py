import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from agents.coding.analyzer_agent import RepoAnalyzerAgent
from core.llm.litellm_client import LiteLLMRouter
from core.llm.base import LLMResponse
from core.llm.prompt_registry import PromptRegistry

async def main():
    # Mock Stores
    metadata_store = MagicMock()
    metadata_store.record_usage = AsyncMock()
    metadata_store.save_artifact = AsyncMock()
    metadata_store.get_execution = AsyncMock(return_value={
        "input_data": {"repo_path": "examples/repo_analyzer", "complexity_score": 1}
    })

    document_store = MagicMock()
    vector_store = MagicMock()
    vector_store.upsert = AsyncMock()

    # Mock Router with a dummy LLM answer
    mock_router = MagicMock(spec=LiteLLMRouter)
    mock_router.route_and_execute = AsyncMock(return_value=LLMResponse(
        content=json.dumps({
            "issues_found": [
                {"file": "main.py", "issue": "Missing docstrings", "severity": "low"}
            ],
            "suggested_fixes": [
                {"file": "main.py", "fix": "Add docstrings to functions"}
            ]
        }),
        raw_response={"model": "mock-model"},
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost=0.001
    ))

    # Mock Registry
    prompt_registry = MagicMock(spec=PromptRegistry)

    # Initialize Agent
    agent = RepoAnalyzerAgent(
        metadata_store=metadata_store,
        document_store=document_store,
        vector_store=vector_store,
        llm_router=mock_router,
        prompt_registry=prompt_registry
    )

    # Run the agent steps manually to demonstrate working example
    print("--- 1. Validating Input ---")
    input_data = {"repo_path": "examples/repo_analyzer", "complexity_score": 1}
    validated_input = await agent.validate(input_data)
    print(f"Validated Input: {validated_input}")

    print("\n--- 2. Retrieving Context ---")
    context = await agent.retrieve_context(validated_input)
    print(f"Detected Language: {context['language']}")
    print(f"Files found: {context['files']}")

    print("\n--- 3. Planning ---")
    plan = await agent.plan(context)
    print(f"Plan: {plan}")

    print("\n--- 4. Executing ---")
    execution_id = "demo-execution-id"
    results = await agent.execute(plan, execution_id)
    print(f"Analysis Results:\n{json.dumps(results, indent=2)}")

    print("\n--- 5. Validating Output ---")
    output = await agent.validate_output(results)
    print(f"Output Validated: {output.success}")

    print("\n--- 6. Persisting Results ---")
    await agent.persist(output, execution_id)
    print("Results persisted to vector store.")

if __name__ == "__main__":
    asyncio.run(main())

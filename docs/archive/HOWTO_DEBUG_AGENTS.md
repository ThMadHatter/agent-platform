# HOWTO: Debugging Agents

This guide explains how to start a debugging session for agents in the Agent Platform, using a "fire and discard" approach where external dependencies are mocked while the core agent logic remains intact.

## Prerequisites

- Python 3.12+
- Project dependencies installed:
  ```bash
  pip install -e ".[dev,test]"
  ```

## Debugging Approach

The core idea is to instantiate the agent with `MagicMock` for its storage and routing dependencies. This allows you to test the agent's logic (validation, context retrieval, planning, etc.) without needing a running database, Qdrant instance, or active LLM API keys.

### 1. Create a Sample Environment

If your agent interacts with the file system (like `RepoAnalyzerAgent`), create a small sample directory with representative files.

```bash
mkdir -p examples/repo_analyzer
touch examples/repo_analyzer/main.py
```

### 2. The Debugging Script (`debug_session.py`)

Create a script that manually walks through the agent's lifecycle.

```python
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from agents.coding.analyzer_agent import RepoAnalyzerAgent
from core.llm.litellm_client import LiteLLMRouter
from core.llm.base import LLMResponse

async def debug_agent():
    # 1. Mock External Dependencies
    metadata_store = MagicMock()
    metadata_store.get_execution = AsyncMock(return_value={
        "input_data": {"repo_path": "examples/repo_analyzer", "complexity_score": 1}
    })

    document_store = MagicMock()
    vector_store = MagicMock()

    # 2. Mock LLM Router with a Dummy Answer
    mock_router = MagicMock(spec=LiteLLMRouter)
    mock_router.route_and_execute = AsyncMock(return_value=LLMResponse(
        content='{"issues_found": [], "suggested_fixes": []}',
        raw_response={"model": "debug-model"},
        prompt_tokens=0, completion_tokens=0, total_tokens=0
    ))

    # 3. Initialize Agent
    agent = RepoAnalyzerAgent(
        metadata_store=metadata_store,
        document_store=document_store,
        vector_store=vector_store,
        llm_router=mock_router,
        prompt_registry=MagicMock()
    )

    # 4. Step-by-Step Execution
    print("Validating...")
    validated_input = await agent.validate({"repo_path": "examples/repo_analyzer"})

    print("Retrieving Context...")
    context = await agent.retrieve_context(validated_input)

    print("Executing...")
    results = await agent.execute([], "debug-id")
    print(f"Results: {results}")

if __name__ == "__main__":
    asyncio.run(debug_agent())
```

### 3. Running the Session

Simply run the script with `PYTHONPATH=.` to ensure modules are found.

```bash
PYTHONPATH=. python3 debug_session.py
```

## Benefits

- **Isolated Logic:** Test your Python code without infrastructure overhead.
- **Fast Feedback:** No waiting for real LLM responses or network calls.
- **Deterministic:** Easily test edge cases by changing the dummy LLM response.

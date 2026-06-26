# RepoAnalyzerAgent Documentation

## 1. Objective & Architecture
The `RepoAnalyzerAgent` is designed to analyze code repositories, determine task complexity, and route requests to the most appropriate LLM using a local LiteLLM proxy. This enables a cost-effective and performance-optimized pipeline for repository analysis.

### Execution Pipeline:
`Telegram -> n8n -> Agent Platform (FastAPI) -> LiteLLM -> Target Model`

---

## 2. Codebase Structure Breakdown

### Agents Logic (`agents/coding/`)
- `analyzer_agent.py`: Contains the `RepoAnalyzerAgent` class. It implements the platform's `BaseAgent` contract, handling the lifecycle from validation to persistence.

### LLM & Routing (`core/llm/`)
- `litellm_client.py`:
    - `LiteLLMProvider`: A provider that communicates with the LiteLLM proxy using the OpenAI SDK.
    - `LiteLLMRouter`: Logic for dynamic model routing based on complexity scores.

### Webhook Integration (`apps/api/routers/`)
- `n8n_webhook.py`: FastAPI router providing the `/api/v1/webhooks/n8n/analyze-repo` endpoint for integration with n8n.

---

## 3. Component Mapping & Data Flow

### Storage Abstractions
- **MetadataStore (PostgreSQL)**:
    - `agent_executions`: Stores the overall execution state (pending, running, completed).
    - `agent_steps`: Tracks individual steps of the agent (`analyze_complexity`, `llm_analysis`, `format_results`).
    - `llm_usage`: Records token usage and cost for every LLM call made via the LiteLLM router.
    - `artifacts`: Stores the final JSON analysis report (`repo_analysis_report`).
- **VectorStore (Qdrant)**:
    - `repo_analyses` collection: Stores the structured results for semantic search and historical comparison.
- **DocumentStore (Google Drive)**:
    - Used if repository files need to be archived or if large codebases are processed and stored as documents.

### Data Flow
1. **Trigger**: n8n sends a POST request to `/api/v1/webhooks/n8n/analyze-repo`.
2. **Initialization**: The webhook instantiates `RepoAnalyzerAgent` and calls `runner.run()`.
3. **Validation**: `validate()` checks the repository path and complexity score.
4. **Context**: `retrieve_context()` prepares the repository information.
5. **Planning**: `plan()` defines the analysis steps.
6. **Execution**:
    - `execute()` calls `LiteLLMRouter.route_and_execute()`.
    - Router selects model:
        - Complexity < 2: `ollama/qwen3`
        - Complexity < 5: `openrouter/deepseek`
        - Complexity >= 5: `gemini/gemini-2.5-pro`
    - LiteLLM Provider calls the proxy at `http://litellm:4000`.
7. **Persistence**: Results are saved to PostgreSQL (Artifacts) and Qdrant (VectorStore).

---

## 4. How-To Guides

### Quick-Start Guide
1. **Configure Environment Variables**:
   Update your `.env` file based on `.env.example`:
   ```env
   LITELLM_BASE_URL=http://your-litellm-host:4000
   LITELLM_API_KEY=your_key
   ```
2. **Run the Platform**:
   ```bash
   make install
   make migrate
   make up
   ```
3. **Trigger Analysis**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/webhooks/n8n/analyze-repo \
   -H "Content-Type: application/json" \
   -d '{"repo_path": "my-org/my-repo", "complexity_score": 4}'
   ```

### Scenario 1: Local-Only Inference Setup
For strict offline environments, configure LiteLLM to point only to Ollama:
1. **LiteLLM Config**:
   Map all routing targets to local Ollama models in your LiteLLM configuration.
2. **Platform Config**:
   ```env
   LITELLM_BASE_URL=http://localhost:11434/v1 # Directly to Ollama if proxy is skipped
   LITELLM_API_KEY=not-needed
   ```
3. **Custom Routing**: Modify `get_model_for_complexity` in `litellm_client.py` to only return local model identifiers like `ollama/qwen3` or `ollama/deepseek-r1`.

### Scenario 2: Hybrid Smart Routing Configuration
Optimized for production:
- **Low Complexity (0-2)**: `ollama/qwen3` (Running on-prem for cost savings).
- **Medium Complexity (3-4)**: `openrouter/deepseek` (Balanced cost/performance).
- **High Complexity (5+)**: `gemini/gemini-2.5-pro` (Maximum reasoning capability).

Ensure LiteLLM has these models configured in its `config.yaml`.

### Scenario 3: Multi-Agent Isolation & Parallel Testing
The platform ensures isolation through:
- **Namespaced Vector Collections**: `medical_records` for MedicalAgent and `repo_analyses` for RepoAnalyzerAgent.
- **Execution Metadata**: Each run has a unique `execution_id` and is tagged with the `agent_name` in PostgreSQL.
- **Independent Storage Paths**: Google Drive folder structures can be partitioned by agent name if required in `DocumentStore` implementations.
- **Parallel Runs**: The `AgentRunner` is asynchronous, allowing multiple agents to process requests concurrently without context bleed.

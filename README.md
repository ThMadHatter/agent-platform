# Agent Platform

A thin API/router layer designed to connect **n8n** with specialized AI agents.

## Architecture

The platform acts as a bridge between orchestration tools (like n8n) and underlying agent implementations.

- **API Layer**: FastAPI-based REST API providing standardized endpoints for agent discovery and execution.
- **Agent Registry**: Centralized registry for agent metadata, capabilities, and schemas.
- **Service Layer**: Common interfaces for external integrations (PostgreSQL, Qdrant, Google Drive, LiteLLM).
- **Runner**: Robust execution engine with support for sync/async patterns and retries.

## Quick Start

### Local Setup

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment**:
   Copy `.env.example` to `.env` and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
4. **Run the API**:
   ```bash
   uvicorn apps.api.main:app --reload
   ```

### External Services

The platform requires the following external services, configured via environment variables:
- **PostgreSQL**: Used for metadata and execution history storage.
- **Qdrant**: Vector database for semantic search and agent memory.
- **LiteLLM**: Unified interface for multiple LLM providers (OpenAI, Anthropic, Gemini, etc.).
- **Google Drive**: Optional document storage for agents.

## API Documentation

### Agent Discovery
- `GET /api/v1/agents`: List all registered agents.
- `GET /api/v1/agents/{agent_id}`: Get metadata for a specific agent.

### Agent Execution
- `POST /api/v1/agents/{agent_id}/run`: Run an agent synchronously.
- `POST /api/v1/agents/{agent_id}/run-async`: Start an async agent execution.
- `GET /api/v1/executions/{execution_id}`: Check the status and result of an execution.

## n8n Integration

### Sync Execution Example
In n8n, use the **HTTP Request** node:
- **Method**: POST
- **URL**: `http://platform-url/api/v1/agents/simple_chat/run`
- **Body**:
  ```json
  {
    "message": "Analyze this data: {{ $json.data }}"
  }
  ```

### Async Execution Pattern
1. **POST** to `/run-async` to get an `execution_id`.
2. **Wait** (using a Wait node).
3. **GET** from `/api/v1/executions/{execution_id}` until status is `succeeded` or `failed`.

## Adding a New Agent

1. Create a new directory in `agents/`.
2. Implement your agent by inheriting from `BaseAgent`.
3. Define your input/output schemas using Pydantic.
4. Register your agent in `core/execution/setup.py`.

## Model Routing

Model routing is configurable via `config/model_routing.yaml`. You can map complexity scores (1-10) to specific models or aliases.

```yaml
models:
  default: "openai/gpt-4o"
  cheap: "openai/gpt-4o-mini"
routing:
  1: "cheap"
  5: "default"
```

## Documentation
- [Architecture Overview](docs/ARCHITECTURE.md)
- [N8N Integration Guide](docs/N8N_INTEGRATION.md)
- [Database Migrations](docs/MIGRATIONS.md)
- [Agent Reference](docs/agents/)

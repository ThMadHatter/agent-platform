# Agent Platform Architecture

## Core Philosophy
The Agent Platform is a domain-agnostic, production-grade AI execution engine. It is designed to be "thin" and high-performance, delegating workflow orchestration to n8n while providing a robust environment for agent execution.

## System Components

### 1. API Layer (`apps/api/`)
- **FastAPI**: Provides REST endpoints for agent discovery and execution.
- **Dynamic Registry**: Discovers agents and their capabilities without hardcoding.
- **n8n Webhooks**: Specialized endpoints for seamless external integration.

### 2. Execution Engine (`core/execution/`)
- **AgentRunner**: Manages the lifecycle of an agent execution (Validate, Context, Plan, Execute, Persist).
- **Retry Engine**: Implements exponential backoff for transient failures during execution steps.
- **AgentRegistry**: Centralizes agent discovery and metadata.

### 3. LLM Layer (`core/llm/`)
- **LiteLLM Integration**: Unified entry point for all LLM providers (Gemini, OpenAI, Anthropic, etc.).
- **Complexity-based Router**: Automatically selects the most appropriate model based on task complexity.
- **Prompt Registry**: Jinja2-based template management for structured prompts.

### 4. Storage Layer (`core/storage/`)
- **Metadata Store (PostgreSQL)**: Tracks execution history, steps, artifacts, and token usage.
- **Document Store (Google Drive)**: Manages binary files and long-term document storage.
- **Vector Store (Qdrant)**: Enables semantic search and RAG capabilities for agents.

### 5. Agent Layer (`agents/`)
- **Shared Base**: Defines the contract for all agents (`BaseAgent`).
- **Domain Agents**: Specialized agents (Medical, Job, Coding) that orchestrate internal services.
- **Internal Services**: Reusable business logic components within a domain.

## Execution Lifecycle
1. **Request**: n8n calls POST `/execute`.
2. **Validation**: Runner validates input against the agent's Pydantic schema.
3. **Context Retrieval**: Agent gathers necessary data (e.g., downloads files, searches vector store).
4. **Planning**: Agent determines the sequence of actions.
5. **Execution**: Agent executes steps, using the **Retry Engine** for LLM calls.
6. **Persistence**: Results are stored in the Metadata Store and Vector Store.
7. **Polling**: n8n polls GET `/executions/{id}` until completion.

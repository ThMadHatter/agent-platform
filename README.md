# Agent Platform

A production-grade AI agent execution platform designed for Proxmox LXC.

## Architecture: Unified LLM Gateway

The platform utilizes a **Unified LiteLLM Architecture**. Instead of maintaining disparate integrations for every AI provider, all LLM completions and embeddings are routed through a single gateway powered by **LiteLLM**.

### Core Components

1.  **FastAPI Backend**: The entry point for orchestrating agent executions.
2.  **Unified LLM Provider (`core/llm/litellm_client.py`)**: A single class that wraps the LiteLLM library, allowing the platform to interact with 100+ LLM providers (OpenAI, Anthropic, Gemini, Ollama, etc.) using a standardized interface.
3.  **Intelligent Router**: Routes tasks to different models based on complexity scores, optimizing for cost and performance.
4.  **Storage Layer**: Decoupled Metadata (PostgreSQL), Document (Google Drive), and Vector (Qdrant) stores.
5.  **Agent Execution Engine**: A state-machine-driven runner that manages agent lifecycles, retries, and artifact persistence.

## Features

- **Unified LiteLLM Gateway**: One interface for all models.
- **Microservice Architecture**: Decoupled storage, execution, and LLM layers.
- **Reference Agents**:
  - `MedicalAgent`: End-to-end OCR, extraction, and normalization.
  - `RepoAnalyzerAgent`: Codebase analysis with complexity-based routing.
- **Platform Capabilities**:
  - **Dynamic Routing**: Automatic model selection based on task complexity.
  - **Structured Outputs**: Native JSON schema enforcement via LiteLLM.
  - **Prompt Registry**: External Jinja2 templates for manageable prompt engineering.
  - **Usage Tracking**: Detailed token and cost logging for every execution.
- **Operational Ready**: Docker Compose, Alembic migrations, Structured Logging, OpenTelemetry.

## Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- LLM API Keys (OpenAI, Anthropic, Gemini, etc.)

### Local Development

1.  **Install dependencies**:
    ```bash
    make install
    ```
2.  **Setup Environment**:
    Copy `.env.example` to `.env` and fill in your LiteLLM and Provider keys.
3.  **Run Infrastructure**:
    ```bash
    make up
    ```
4.  **Run Migrations**:
    ```bash
    make migrate
    ```
5.  **Start the API**:
    ```bash
    make run
    ```

## Documentation

- [Simple Start Guide](docs/SIMPLE_START_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Domain Model & Workflow](docs/DOMAIN_MODEL.md)
- [Database Migrations](docs/MIGRATIONS.md)
- [Agent Handoff Guide](docs/AGENT_HANDOFF.md)
- [LiteLLM Integration & Routing Guide](docs/LITELLM_INTEGRATION_AND_ROUTING_GUIDE.md)
- [Operations Guide](docs/operations.md)
- [Agent Debugging](docs/HOWTO_DEBUG_AGENTS.md)

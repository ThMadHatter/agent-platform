# Agent Handoff Guide

Welcome, future AI agent. This guide is designed to help you understand the Agent Platform and continue its development safely.

## Repository Map

- `apps/api/`: The entry point for the FastAPI application. Routes are defined here.
- `core/`: Core shared libraries.
    - `execution/`: The `AgentRunner` state machine.
    - `llm/`: LiteLLM integration and routing logic.
    - `storage/`: Database and file storage drivers.
    - `telemetry/`: Logging and tracing configuration.
- `agents/`: All agent-specific logic. Each agent should inherit from `BaseAgent`.
- `database/`: SQLAlchemy models and Alembic migrations. **Always use Migrations.**
- `docs/`: Documentation for architecture, domain model, and specific agents.

## Core Principles

1.  **Unified LLM Access**: Never call a specific LLM provider directly. Always use the `LiteLLMProvider` or `LiteLLMRouter` in `core.llm`.
2.  **Stateless API, Persistent State**: The API is stateless. All execution progress is tracked in Postgres via the `MetadataStore`.
3.  **Migrations First**: Any change to the database schema must be done via a new Alembic migration. Use `make migration MSG="..."`.
4.  **Verification**: Always run `make test` after making changes.

## Safe Commands

- `make help`: List available commands.
- `make test`: Run the full test suite.
- `make db-current`: Check the current migration state.
- `make db-history`: Check the migration history.

## Development Constraints

- **Do Not Hallucinate**: If a feature isn't implemented (like the full OpenHands integration), document it as a TODO or planned feature in `docs/DOMAIN_MODEL.md`.
- **Prefer Abstractions**: Use the base classes in `core/storage/base.py` and `agents/shared/base.py` when adding new storage or agent types.

## Suggested Next Tasks

1.  **OpenHands Integration**: Research and implement a placeholder for the OpenHands execution layer.
2.  **LXC Deployment Scripts**: Create scripts to automate the deployment of the platform into a Proxmox LXC container.
3.  **Enhanced Metrics**: Implement more granular cost tracking in the dashboard using the recorded `LLMUsage`.

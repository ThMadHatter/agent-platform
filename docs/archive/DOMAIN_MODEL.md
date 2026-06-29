# Core Domain Model

This document describes the core entities and workflow of the Agent Platform.

## Entities

### Task
A high-level objective assigned to the platform (e.g., "Analyze this repository for security vulnerabilities").
Currently represented implicitly as `AgentInput` in the execution flow.

### Agent
A specialized unit of logic designed to perform specific tasks.
- `MedicalAgent`: Handles medical document OCR, extraction, and normalization.
- `RepoAnalyzerAgent`: Performs static analysis and code review suggestions.

### Execution (Run)
A single instance of an agent performing a task.
- **Status**: PENDING, RUNNING, RETRYING, COMPLETED, FAILED, CANCELLED.
- Tracks start/end time, duration, and overall success.

### Step
A granular action within an execution (e.g., "OCR", "LLM Analysis").
- Allows for detailed tracking and debugging of complex agent flows.

### Artifact
A tangible output from an execution or step (e.g., a JSON report, an OCRed text file).
- Stored in the metadata database for traceability.

### Usage
Tracking of LLM token consumption and cost associated with an execution.
- Routes through LiteLLM to capture standardized metrics across 100+ providers.

## Target Workflow: Task-to-Production

The platform is designed to support the following automated development lifecycle:

1. **Task**: Received via API or n8n webhook.
2. **Analysis**: AI (RepoAnalyzerAgent) evaluates the task and current codebase.
3. **Execution**: Platform triggers a coding agent (e.g., OpenHands integration - TODO).
4. **Test Environment**: Platform deploys a temporary test environment (LXC-based - TODO).
5. **Verification**: Automated tests are run.
6. **Iteration**: If tests fail, the platform loops back to "Fix" (TODO).
7. **Production**: Upon successful verification, the change is deployed to production.

## Current Implementation Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| FastAPI Backend | Functional | Core API and agent orchestration. |
| Postgres Metadata | Functional | Fully implemented with Alembic migrations. |
| Qdrant Vector Store | Functional | Client implemented, used for persisting results. |
| LiteLLM Gateway | Functional | Unified routing layer for all LLMs. |
| Agent Execution Engine | Functional | State-machine based runner. |
| OpenHands Integration | Planned | Expected for the coding/execution layer. |
| n8n Webhooks | Functional | Dedicated endpoint for n8n orchestration. |
| LXC Deployment | Planned | Part of the broader target architecture. |

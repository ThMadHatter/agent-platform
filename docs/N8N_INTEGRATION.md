# n8n Integration Guide - Agent Platform

## Overview
The Agent Platform is designed to be orchestrated by n8n. It provides deterministic, machine-readable REST APIs for agent execution, status polling, and callback support.

## Base URL
All API requests should be made to:
`http://<your-platform-domain>/api/v1`

## Authentication
The platform uses Bearer Token authentication.

**Header**: `Authorization: Bearer <AGENT_PLATFORM_API_KEY>`

## 1. Health Check
Verify the platform and its backend services (Postgres, Qdrant, GDrive) are healthy.

**Endpoint**: `GET /api/v1/health`

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "services": {
    "postgres": "configured",
    "qdrant": "not_configured",
    "gdrive": "configured"
  }
}
```

## 2. Agent Discovery
To get a list of all available agents and their capabilities:

**Endpoint**: `GET /api/v1/agents`

**Response**:
```json
[
  {
    "id": "job",
    "name": "Job Agent",
    "version": "1.0.0",
    "description": "Job domain agent for ingestion, optimization and tracking",
    "capabilities": ["job_scraping", "resume_parsing", "resume_optimization"],
    "execution_modes": ["sync", "async"],
    "input_schema": {
      "workflow": "str",
      "job_url": "Optional[str]",
      "resume_id": "Optional[str]"
    },
    "output_schema": {
      "success": "bool",
      "data": "dict"
    },
    "required_services": ["LinkedInJobIngestionService", "JobDescriptionParser", "ResumeOptimizer"]
  }
]
```

## 3. Agent Execution

### Synchronous Execution (Run and Wait)
Runs the agent and waits for the result. Best for fast agents (under 30s).

**Endpoint**: `POST /api/v1/agents/{agent_id}/run`

**Request Body**:
```json
{
  "input_data": {
    "message": "Hello"
  }
}
```

### Asynchronous Execution (Fire and Forget/Poll)
Starts the agent and returns an execution ID immediately. Recommended for n8n.

**Endpoint**: `POST /api/v1/agents/{agent_id}/run-async`

**Response**:
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "job",
  "status": "queued",
  "poll_url": "/api/v1/executions/550e8400-e29b-41d4-a716-446655440000"
}
```

## 4. Execution Status & Polling
Poll this endpoint using the `execution_id` until `status` is `succeeded` or `failed`.

**Endpoint**: `GET /api/v1/executions/{execution_id}`

**Final Success Response**:
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "job",
  "status": "succeeded",
  "result": {
    "optimized_resume": "..."
  },
  "error": null,
  "duration_seconds": 12.5,
  "started_at": "2026-06-29T10:00:00Z",
  "completed_at": "2026-06-29T10:00:12Z"
}
```

## 5. Callback Mode (Webhooks)
Instead of polling, you can provide a `callback_url`. The platform will POST the final result to this URL when finished.

**Request**:
```json
{
  "input_data": { ... },
  "callback_url": "https://n8n.your-domain.com/webhook/agent-results"
}
```

## 6. Idempotency
To prevent duplicate executions (e.g., if n8n retries an HTTP request), use an idempotency key.

**Option A (Header)**: `Idempotency-Key: your-unique-id`
**Option B (Body)**: `"client_request_id": "your-unique-id"`

If the same key is sent again with the same payload, the platform returns the existing execution instead of starting a new one.

## 7. n8n Example Configuration

### HTTP Request Node (Async Run)
- **Method**: POST
- **URL**: `http://platform/api/v1/agents/job/run-async`
- **Authentication**: Header `Authorization` = `Bearer {{ $env.AGENT_PLATFORM_API_KEY }}`
- **Body**:
  ```json
  {
    "input_data": {
      "workflow": "resume_optimization",
      "job_url": "{{ $json.url }}"
    },
    "client_request_id": "n8n-{{ $execution.id }}"
  }
  ```

### Polling Logic in n8n
1. **Initial Wait**: 2 seconds.
2. **HTTP Request**: `GET /api/v1/executions/{{ $json.execution_id }}`.
3. **If Node**: `{{ $json.status }}` matches `succeeded` or `failed`.
4. **Loop**: If not finished, wait 5 seconds and repeat.
5. **Max Attempts**: 60 (total 5 minutes).

### Error Handling Retries
- Retry **429, 500, 502, 503, 504** with exponential backoff.
- Do **not** retry **400, 401, 404, 409, 422**.

## 8. Future: Custom n8n Node
A dedicated n8n node is planned. It will provide:
- Dropdown for **Agent Selection** (via `GET /agents`).
- Simplified **Input Mapping** based on `input_schema`.
- Built-in **Polling** for "Run and Wait" operations.
- Automatic **Idempotency** using n8n execution IDs.

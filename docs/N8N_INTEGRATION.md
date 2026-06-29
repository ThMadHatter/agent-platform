# n8n Integration Guide - Agent Platform

## Overview
The Agent Platform is designed to be orchestrated by n8n. It provides deterministic, machine-readable REST APIs for agent execution, status polling, and history retrieval.

## 1. Agent Discovery
To get a list of all available agents and their capabilities:

**Endpoint**: `GET /api/v1/agents`

**Response**:
```json
[
  {
    "name": "job",
    "version": "1.0.0",
    "description": "Job domain agent for ingestion, optimization and tracking",
    "input_schema": {
      "workflow": "str",
      "job_url": "Optional[str]",
      "resume_id": "Optional[str]"
    },
    "output_schema": {
      "success": "bool",
      "data": "dict"
    },
    "capabilities": ["job_scraping", "resume_parsing", "resume_optimization"],
    "required_services": ["LinkedInJobIngestionService", "JobDescriptionParser", "ResumeOptimizer"]
  }
]
```

## 2. Agent Execution
Agents can be executed by sending a POST request to their specific execution endpoint.

**Endpoint**: `POST /api/v1/agents/{agent_name}/execute`

**Request Example (Job Agent)**:
```json
{
  "workflow": "resume_optimization",
  "job_url": "https://www.linkedin.com/jobs/view/123456",
  "resume_content": "I am a software engineer with 10 years of experience..."
}
```

**Response**:
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 3. Execution Polling & Results
Since some executions may take time, n8n should poll the execution status until it reaches a final state (`completed`, `failed`).

**Endpoint**: `GET /api/v1/executions/{execution_id}`

**Response (In Progress)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "start_time": "2023-10-27T10:00:00Z"
}
```

**Response (Completed)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "output_data": {
    "optimized_resume": "Optimized content here..."
  },
  "duration_seconds": 12.5
}
```

## 4. Recommended Workflow Patterns in n8n
1. **Trigger**: Telegram, Schedule, or Webhook.
2. **HTTP Request**: POST to `/execute`.
3. **Wait Node**: Wait for 2-5 seconds.
4. **HTTP Request**: GET `/executions/{execution_id}`.
5. **If Node**: Check if status is `completed` or `failed`.
6. **Loop**: If not finished, return to step 3.
7. **Process**: Use `output_data` for subsequent steps (e.g., sending a Telegram message).

## 5. Error Handling & Retries
- The platform has an internal **Retry Engine** for transient failures (e.g., LLM timeouts).
- For platform-level errors, n8n should implement its own retry logic with exponential backoff.
- Always check the `status` field in the execution response.

## 6. Idempotency Guidelines
- Currently, idempotency is not strictly enforced at the API level.
- It is recommended to generate a unique `execution_id` or `client_key` in n8n if future deduplication is required.

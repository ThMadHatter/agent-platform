# Job Agent

## Purpose
Orchestrates career-related workflows including job ingestion, resume parsing, and optimization.

## Input Schema
```json
{
  "workflow": "string (linkedin_ingestion | resume_optimization | resume_ingestion)",
  "job_url": "string (optional)",
  "resume_id": "string (optional)",
  "resume_content": "string (optional)"
}
```

## Output Schema
```json
{
  "success": "boolean",
  "data": "object"
}
```

## Example Request
`POST /api/v1/agents/job/run`
```json
{
  "workflow": "linkedin_ingestion",
  "job_url": "https://www.linkedin.com/jobs/view/123456"
}
```

## Example Response
```json
{
  "execution_id": "exec_012",
  "agent_id": "job",
  "status": "succeeded",
  "result": {
    "job_data": {...},
    "parsed_job": {...}
  },
  "error": null
}
```

## Required Services
- PostgreSQL (Metadata)
- Vector Store (Qdrant)
- Document Store (Google Drive)
- LiteLLM
- Job Ingestion Service

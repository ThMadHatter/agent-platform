# Simple Chat Agent

## Purpose
A basic conversational agent for general queries.

## Input Schema
```json
{
  "message": "string"
}
```

## Output Schema
```json
{
  "response": "string"
}
```

## Example Request
`POST /api/v1/agents/simple_chat/run`
```json
{
  "message": "Hello, how can you help me today?"
}
```

## Example Response
```json
{
  "execution_id": "exec_789",
  "agent_id": "simple_chat",
  "status": "succeeded",
  "result": {
    "response": "I can assist you with repository analysis, medical document processing, and job application tracking."
  },
  "error": null
}
```

## Required Services
- PostgreSQL (Metadata)
- Vector Store (Qdrant)
- LiteLLM

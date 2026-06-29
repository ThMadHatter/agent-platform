# Repo Analyzer Agent

## Purpose
Analyzes a local repository directory to identify code issues and suggest fixes using LLM routing based on complexity.

## Input Schema
```json
{
  "repo_path": "string",
  "complexity_score": "number (optional, 1-10)"
}
```

## Output Schema
```json
{
  "issues_found": [
    {"file": "string", "issue": "string", "severity": "string"}
  ],
  "suggested_fixes": [
    {"file": "string", "fix": "string"}
  ]
}
```

## Example Request
`POST /api/v1/agents/repo_analyzer/run`
```json
{
  "repo_path": "./core",
  "complexity_score": 5
}
```

## Example Response
```json
{
  "execution_id": "exec_456",
  "agent_id": "repo_analyzer",
  "status": "succeeded",
  "result": {
    "issues_found": [...],
    "suggested_fixes": [...]
  },
  "error": null
}
```

## Required Services
- PostgreSQL (Metadata)
- Vector Store (Qdrant)
- LiteLLM (with Router)

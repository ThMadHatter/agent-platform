# Simple Start Guide

This guide will help you get started with the Agent Platform by using a simple chat agent.

## Prerequisites

- Python 3.12+
- PostgreSQL (for metadata)
- (Optional) LiteLLM for real LLM responses

## Quick Start

### 1. Install Dependencies

```bash
make install
```

### 2. Configure Environment

Copy the example environment file and update it with your settings.

```bash
cp .env.example .env
```

If you are running the database via Docker but executing the agent script on your host machine, ensure `.env` contains:
`DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/agent_platform`

If you are running everything inside Docker, use:
`DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/agent_platform`

### 3. Run Database Migrations

```bash
make migrate
```

### 4. Use the Chat CLI

You can interact with the `SimpleChatAgent` using the provided CLI tool.

```bash
PYTHONPATH=. python3 scripts/chat_cli.py "Hello, how are you?"
```

> **Note:** If you get a `socket.gaierror`, it means your `DATABASE_URL` host is incorrect. If you are running locally without Docker, ensure your `.env` has `DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/agent_platform`.

## Troubleshooting

If you encounter issues, use the environment check tool:

```bash
PYTHONPATH=. python3 scripts/check_env.py
```

This will show you which configuration files are loaded and where the platform is trying to connect.

### "socket.gaierror: [Errno -2] Name or service not known"
This means the hostname in your `DATABASE_URL` cannot be resolved.
- If you see `Host: db` but you are not running inside a Docker container, change it to `127.0.0.1` in your `.env`.

This command will:
1. Initialize the `SimpleChatAgent`.
2. Send your message to the agent.
3. Use the `AgentRunner` to orchestrate the execution.
4. Display the response from the agent.

## API Integration

The `SimpleChatAgent` is also exposed via the FastAPI backend.

### Start the API

```bash
make run
```

### Execute Agent via API

```bash
curl -X POST http://localhost:8000/api/v1/agents/simple_chat/execute \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the capital of France?"}'
```

## Creating Your Own Agent

To create a new agent:
1. Inherit from `BaseAgent` in `agents/shared/base.py`.
2. Implement the required methods: `validate`, `retrieve_context`, `plan`, `execute`, `validate_output`, and `persist`.
3. Register your agent in `apps/api/main.py`.

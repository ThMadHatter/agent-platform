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

### 3. Run Database Migrations

```bash
make migrate
```

### 4. Use the Chat CLI

You can interact with the `SimpleChatAgent` using the provided CLI tool.

```bash
PYTHONPATH=. python3 scripts/chat_cli.py "Hello, how are you?"
```

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

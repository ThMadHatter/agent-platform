# Agent Platform

A production-grade AI agent execution platform designed for Proxmox LXC.

## Features

- **FastAPI Backend**: High-performance REST API for agent execution and monitoring.
- **Microservice Architecture**: Decoupled storage, execution, and LLM layers.
- **Reference Agent**: `MedicalAgent` demonstrating end-to-end OCR, extraction, and normalization.
- **Platform Capabilities**:
  - Multi-LLM provider support (Gemini, OpenAI, etc.)
  - Prompt Registry (Jinja2)
  - Artifact Persistence
  - Usage Tracking
  - Event Bus & Retries
- **Operational Ready**: Docker Compose, Alembic migrations, Structured Logging, OpenTelemetry.

## Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Google Gemini API Key
- Google Drive Service Account Credentials

### Local Development

1. Install dependencies:
   ```bash
   make install
   ```
2. Setup `.env` and `credentials.json`.
3. Run infrastructure:
   ```bash
   make up
   ```
4. Run migrations:
   ```bash
   make migrate
   ```
5. Start the API:
   ```bash
   make run
   ```

## Documentation

- [Architecture](architecture.md)
- [Operations Guide](docs/operations.md)

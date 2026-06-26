from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "Agent Platform"
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_platform"

    # LiteLLM / LLM Gateway
    litellm_base_url: Optional[str] = None
    litellm_api_key: Optional[str] = None
    default_model: str = "openai/gpt-4o"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None

    # Google Drive
    google_drive_credentials_path: str = "credentials.json"

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

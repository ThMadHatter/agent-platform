from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "Agent Platform"
    environment: str = "development"

    # Database (External Service)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_platform"

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("asyncpg", "psycopg2")

    # LiteLLM / LLM Gateway
    litellm_base_url: Optional[str] = None
    litellm_api_key: Optional[str] = None
    default_chat_model: str = "basic-profile"
    default_embedding_model: str = "embedding-default"
    allowed_models: list[str] = ["basic-profile", "heavy-profile", "embedding-default"]

    # Embeddings
    embedding_dimension: int = 1024

    # Agent Platform Auth
    agent_platform_api_key: str = "your-secret-key"
    agent_platform_auth_enabled: bool = False

    # Qdrant (External Service)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_cv_collection: str = "work_collection"
    qdrant_distance: str = "cosine"

    # Google Drive
    google_drive_credentials_path: str = "credentials.json"

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

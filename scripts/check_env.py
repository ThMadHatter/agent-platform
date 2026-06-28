import os
import sys
from pydantic_settings import BaseSettings

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import settings
from sqlalchemy.engine import make_url

def check_env():
    print("--- Agent Platform Environment Check ---")

    # 1. Check for .env file
    env_exists = os.path.exists(".env")
    print(f".env file found: {env_exists}")
    if not env_exists:
        print("  Recommendation: Copy .env.example to .env and configure it.")

    # 2. Database Configuration
    try:
        url = make_url(settings.database_url)
        print(f"Database:")
        print(f"  URL: {url.render_as_string(hide_password=True)}")
        print(f"  Host: {url.host}")
        print(f"  Port: {url.port or 5432}")
        print(f"  User: {url.username}")
        print(f"  DB: {url.database}")
    except Exception as e:
        print(f"Database Configuration Error: {e}")

    # 3. LiteLLM Configuration
    print(f"LiteLLM:")
    print(f"  Base URL: {settings.litellm_base_url or 'Not configured (using defaults)'}")
    print(f"  API Key: {'Set' if settings.litellm_api_key else 'Not set'}")
    print(f"  Default Model: {settings.default_model}")

    # 4. Other services
    print(f"Qdrant URL: {settings.qdrant_url}")
    print(f"Environment: {settings.environment}")

    print("----------------------------------------")

if __name__ == "__main__":
    check_env()

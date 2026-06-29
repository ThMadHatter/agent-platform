import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app
from core.config import settings

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_health_litellm_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health/litellm")
    assert response.status_code == 200
    # Assuming local test environment might have them missing or default
    assert "status" in response.json()

def test_settings_load():
    assert settings.app_name == "Agent Platform"
    assert settings.database_url is not None

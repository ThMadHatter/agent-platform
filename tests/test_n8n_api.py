import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from core.config import settings
import uuid

@pytest.fixture
def api_key():
    settings.agent_platform_api_key = "test-key"
    settings.agent_platform_auth_enabled = True
    return "test-key"

@pytest.mark.asyncio
async def test_health_check(api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "postgres" in data["services"]

@pytest.mark.asyncio
async def test_list_agents(api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/agents", headers={"Authorization": f"Bearer {api_key}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(a["id"] == "simple_chat" for a in data)

@pytest.mark.asyncio
async def test_async_execution_and_polling(api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Start async execution
        run_resp = await ac.post(
            "/api/v1/agents/simple_chat/run-async",
            json={"input_data": {"message": "hi"}},
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        execution_id = run_data["execution_id"]
        assert run_data["status"] == "queued"
        assert "poll_url" in run_data

        # 2. Poll status
        poll_resp = await ac.get(
            f"/api/v1/executions/{execution_id}",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert poll_resp.status_code == 200
        poll_data = poll_resp.json()
        assert poll_data["execution_id"] == execution_id
        assert poll_data["status"] in ["queued", "running", "succeeded", "failed"]

@pytest.mark.asyncio
async def test_idempotency(api_key):
    client_request_id = str(uuid.uuid4())
    payload = {"input_data": {"message": "hi"}, "client_request_id": client_request_id}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First request
        resp1 = await ac.post(
            "/api/v1/agents/simple_chat/run-async",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert resp1.status_code == 200
        id1 = resp1.json()["execution_id"]

        # Second request with same ID
        resp2 = await ac.post(
            "/api/v1/agents/simple_chat/run-async",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert resp2.status_code == 200
        id2 = resp2.json()["execution_id"]

        assert id1 == id2

        # Third request with same ID but different payload
        payload_diff = {"input_data": {"message": "different"}, "client_request_id": client_request_id}
        resp3 = await ac.post(
            "/api/v1/agents/simple_chat/run-async",
            json=payload_diff,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert resp3.status_code == 409
        data = resp3.json()
        assert "error" in data or ("detail" in data and "error" in data["detail"])
        error = data["detail"]["error"] if "detail" in data else data["error"]
        assert error["code"] == "IDEMPOTENCY_CONFLICT"

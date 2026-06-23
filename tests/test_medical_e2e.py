import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_medical_agent_execution_path():
    # Patch everything BEFORE importing apps.api.main
    with patch("core.storage.postgres.create_async_engine"), \
         patch("core.storage.gdrive.GoogleDriveDocumentStore"), \
         patch("core.storage.qdrant.QdrantVectorStore"), \
         patch("core.llm.providers.gemini.GeminiProvider"), \
         patch("core.telemetry.tracing.setup_tracing"), \
         patch("core.telemetry.logging.setup_logging"):

        from apps.api.main import app, metadata_store, llm_provider, document_store, vector_store

        # Patch the store instances created in main.py
        with patch.object(metadata_store, 'save_execution', new_callable=AsyncMock) as mock_save, \
             patch.object(metadata_store, 'update_execution', new_callable=AsyncMock) as mock_update, \
             patch.object(metadata_store, 'add_step', new_callable=AsyncMock) as mock_add_step, \
             patch.object(metadata_store, 'update_step', new_callable=AsyncMock) as mock_update_step, \
             patch.object(metadata_store, 'get_execution', new_callable=AsyncMock) as mock_get_exec, \
             patch.object(metadata_store, 'save_artifact', new_callable=AsyncMock) as mock_save_art, \
             patch.object(llm_provider, 'generate_structured', new_callable=AsyncMock) as mock_gen_struct, \
             patch.object(llm_provider, 'generate', new_callable=AsyncMock) as mock_gen, \
             patch.object(vector_store, 'upsert', new_callable=AsyncMock) as mock_upsert:

            mock_save.return_value = "test_id"
            mock_add_step.return_value = "step_id"
            mock_get_exec.return_value = {
                "id": "test_id",
                "agent_name": "medical",
                "status": "completed",
                "start_time": None
            }

            from core.llm.base import LLMResponse
            mock_gen_struct.return_value = LLMResponse(content='{"entities": ["BP 120/80"]}', raw_response={})
            mock_gen.return_value = LLMResponse(content='Normalized BP 120/80', raw_response={})

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                input_data = {
                    "patient_id": "P123",
                    "extraction_type": "general",
                    "document_url": "https://example.com/medical_record.pdf"
                }
                response = await ac.post("/api/v1/agents/medical/execute", json=input_data)

            assert response.status_code == 200
            execution_id = response.json()["execution_id"]
            assert execution_id is not None

            # Verify execution status
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                status_response = await ac.get(f"/api/v1/executions/{execution_id}")

            assert status_response.status_code == 200
            assert status_response.json()["agent_name"] == "medical"

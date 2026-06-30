import pytest
from unittest.mock import MagicMock, AsyncMock
from agents.medical.agent import MedicalAgent

@pytest.fixture
def mock_deps():
    return {
        "metadata": MagicMock(),
        "document": MagicMock(),
        "vector": AsyncMock(),
        "llm": AsyncMock(),
        "prompts": MagicMock()
    }

@pytest.mark.asyncio
async def test_medical_agent_validation(mock_deps):
    from core.services.context import ServiceContext
    context = ServiceContext(
        metadata_store=mock_deps["metadata"],
        document_store=mock_deps["document"],
        vector_store=mock_deps["vector"],
        llm_provider=mock_deps["llm"],
        prompt_registry=mock_deps["prompts"]
    )
    agent = MedicalAgent(context)

    input_data = {"patient_id": "P123", "extraction_type": "labs"}
    validated = await agent.validate(input_data)

    assert validated.patient_id == "P123"
    assert validated.extraction_type == "labs"

@pytest.mark.asyncio
async def test_medical_agent_plan(mock_deps):
    from core.services.context import ServiceContext
    context = ServiceContext(
        metadata_store=mock_deps["metadata"],
        document_store=mock_deps["document"],
        vector_store=mock_deps["vector"],
        llm_provider=mock_deps["llm"],
        prompt_registry=mock_deps["prompts"]
    )
    agent = MedicalAgent(context)

    plan = await agent.plan({})
    assert len(plan) == 3
    assert plan[0]["step"] == "ocr"

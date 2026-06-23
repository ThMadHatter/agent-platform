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
    agent = MedicalAgent(
        mock_deps["metadata"],
        mock_deps["document"],
        mock_deps["vector"],
        mock_deps["llm"],
        mock_deps["prompts"]
    )

    input_data = {"patient_id": "P123", "extraction_type": "labs"}
    validated = await agent.validate(input_data)

    assert validated.patient_id == "P123"
    assert validated.extraction_type == "labs"

@pytest.mark.asyncio
async def test_medical_agent_plan(mock_deps):
    agent = MedicalAgent(
        mock_deps["metadata"],
        mock_deps["document"],
        mock_deps["vector"],
        mock_deps["llm"],
        mock_deps["prompts"]
    )

    plan = await agent.plan({})
    assert len(plan) == 3
    assert plan[0]["step"] == "ocr"

from unittest.mock import MagicMock, patch

import pytest

from app.services.openai_client import chat, list_models, resolve_model
from app.services.prompt_router import classify_prompt


@pytest.fixture(autouse=True)
def enable_llm(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_classify_prompt_falls_back_to_llm_chat():
    assert classify_prompt("What should treasury focus on this quarter?") == "llm_chat"


def test_classify_prompt_still_routes_forecast():
    assert classify_prompt("Generate the 2026 cashflow forecast") == "base_forecast"


def test_resolve_model_returns_configured():
    assert resolve_model() == "gpt-4o-mini"


def test_list_models_returns_configured_model():
    assert list_models() == ["gpt-4o-mini"]


@patch("app.services.openai_client._get_client")
def test_chat_returns_narrative(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        model="gpt-4o-mini",
        choices=[MagicMock(message=MagicMock(content="Accelerate collections and defer discretionary spend."))],
    )

    result = chat("Summarize liquidity risk.", context={"avg_monthly_cash_flow": 12000})

    assert result["available"] is True
    assert "Accelerate collections" in result["narrative"]

from unittest.mock import patch

from app.services.insights_engine import generate_insights
from app.services.llm_service import _parse_llm_insight_cards, generate_llm_insight_cards
from tests.factories import make_monthly_records


def test_insights_returns_summary_only_without_rule_cards():
    records = make_monthly_records()
    insights = generate_insights(records)

    assert insights.historical_summary["total_months"] == len(records)
    assert insights.llm_insights == []
    assert insights.seasonal_patterns


def test_parse_llm_insight_cards_json():
    raw = """[
      {"category": "Liquidity", "title": "Build buffer", "description": "Hold 2 months expenses.", "impact": "high"}
    ]"""
    cards = _parse_llm_insight_cards(raw)
    assert len(cards) == 1
    assert cards[0].source == "llm"
    assert cards[0].impact == "high"


@patch("app.services.llm_service.chat")
def test_generate_llm_insight_cards(mock_chat):
    mock_chat.return_value = {
        "narrative": '[{"category": "Collections", "title": "Tighten terms", "description": "Reduce lag.", "impact": "medium"}]',
        "model": "gpt-4o-mini",
        "available": True,
        "error": None,
    }
    records = make_monthly_records()
    base = generate_insights(records)
    payload = generate_llm_insight_cards(records, insights=base)
    assert len(payload["llm_insights"]) == 1
    assert payload["llm_insights"][0].source == "llm"

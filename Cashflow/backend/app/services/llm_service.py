from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.services.currency_format import INR_OUTPUT_RULES, normalize_inr_in_narrative
from app.config import get_settings
from app.services.advisory_engine import generate_cashflow_advisory
from app.services.insights_engine import generate_insights
from app.services.llm_context import build_treasury_context
from app.services.openai_client import chat, is_available, list_models, resolve_model
from app.models.schemas import ForecastMonth, InsightItem, InsightsResponse, MonthlyRecord

TASK_PROMPTS = {
    "risk_insights": (
        "Write a liquidity risk assessment for the treasury team. Cover:\n"
        "1. Current cashflow position and seasonal vulnerabilities\n"
        "2. The top 3 liquidity risks visible in the data\n"
        "3. Concrete actions to mitigate those risks before weak months\n"
        "Keep the response under 400 words. "
        f"{INR_OUTPUT_RULES}"
    ),
    "cashflow_advisory": (
        "The user wants to improve cashflow. Based on the treasury context, write an actionable advisory:\n"
        "1. Executive summary of the cash position\n"
        "2. Highest-impact levers to increase cashflow (with numbers)\n"
        "3. A prioritized 30-day action plan\n"
        f"Keep the response under 450 words. {INR_OUTPUT_RULES}"
    ),
    "freeform": (
        "Answer the user's treasury question using the provided data. "
        "If they ask for a forecast, cite the forecast summary in the context. "
        "If they ask about risk, cite seasonal patterns and scenario stress tests. "
        f"Keep the response focused and under 400 words. {INR_OUTPUT_RULES}"
    ),
    "trajectory": (
        "Explain the projected cashflow trajectory for a treasury executive. Cover:\n"
        "1. Overall direction of revenue, expenditure, and net cashflow across the period\n"
        "2. Strongest and weakest months, month-over-month momentum, and any inflection points\n"
        "3. What the gap between revenue and spend means for liquidity\n"
        "4. One practical takeaway for the coming quarter\n"
        f"Use only figures from the context. Write in clear prose under 350 words. {INR_OUTPUT_RULES}"
    ),
}


def llm_meta(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "llm_narrative": result.get("narrative"),
        "llm_model": result.get("model"),
        "llm_available": bool(result.get("available")),
        "llm_error": result.get("error"),
    }


INSIGHT_CARDS_PROMPT = """Based on the treasury JSON context, return ONLY a JSON array of 4 to 6 insight objects.
Each object must use this schema:
{"category": string, "title": string, "description": string, "impact": "high"|"medium"|"low"}

Rules:
- Use ONLY numbers and facts from the context; do not invent figures.
- {INR_OUTPUT_RULES}
- Cover a mix of liquidity risks and actionable treasury recommendations.
- Reference specific months, ratios, or amounts from the context when available.
- Descriptions must be 1-2 sentences.
- Return valid JSON only — no markdown fences or commentary."""


def _parse_llm_insight_cards(raw: Optional[str]) -> List[InsightItem]:
    if not raw:
        return []
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []

    cards: List[InsightItem] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        category = str(entry.get("category", "")).strip()
        title = str(entry.get("title", "")).strip()
        description = str(entry.get("description", "")).strip()
        impact = str(entry.get("impact", "medium")).strip().lower()
        if impact not in {"high", "medium", "low"}:
            impact = "medium"
        if not category or not title or not description:
            continue
        cards.append(
            InsightItem(
                category=category,
                title=title,
                description=normalize_inr_in_narrative(description) or description,
                impact=impact,
                source="llm",
            )
        )
    return cards


def generate_llm_insight_cards(
    records: List[MonthlyRecord],
    *,
    insights: InsightsResponse,
    advisory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = build_treasury_context(records, insights=insights, advisory=advisory)
    result = chat(INSIGHT_CARDS_PROMPT, context=context)
    cards = _parse_llm_insight_cards(result.get("narrative"))
    return {"llm_insights": cards}


def enrich_insights_with_llm(
    records: List[MonthlyRecord],
    insights: InsightsResponse,
    *,
    advisory: Optional[Dict[str, Any]] = None,
) -> InsightsResponse:
    if not is_available():
        return insights
    payload = generate_llm_insight_cards(records, insights=insights, advisory=advisory)
    insights.llm_insights = payload.get("llm_insights", [])
    return insights


def generate_risk_narrative(
    records: List[MonthlyRecord],
    *,
    insights: Optional[InsightsResponse] = None,
    advisory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = build_treasury_context(records, insights=insights, advisory=advisory)
    result = chat(TASK_PROMPTS["risk_insights"], context=context)
    return llm_meta(result)


def generate_advisory_narrative(
    records: List[MonthlyRecord],
    user_prompt: str,
    *,
    task: str = "cashflow_advisory",
    advisory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = build_treasury_context(records, advisory=advisory)
    base = TASK_PROMPTS.get(task, TASK_PROMPTS["freeform"])
    prompt = f"User question: {user_prompt}\n\n{base}"
    result = chat(prompt, context=context)
    return llm_meta(result)


def generate_trajectory_narrative(
    records: List[MonthlyRecord],
    forecast: List[ForecastMonth],
    summary: Dict[str, float],
) -> Dict[str, Any]:
    if not is_available():
        return llm_meta(
            {
                "narrative": None,
                "model": None,
                "available": False,
                "error": "AI service is not available.",
            }
        )

    context = {
        "forecast_summary": summary,
        "monthly_projection": [row.model_dump(mode="json") for row in forecast],
        "historical_summary": generate_insights(records).historical_summary,
    }
    result = chat(TASK_PROMPTS["trajectory"], context=context)
    return llm_meta(result)


def build_insights_response(records: List[MonthlyRecord]) -> InsightsResponse:
    insights_obj = generate_insights(records)
    if not get_settings().llm_enabled:
        return insights_obj
    advisory = generate_cashflow_advisory(records)
    insights_obj = enrich_insights_with_llm(records, insights_obj, advisory=advisory)
    payload = {**insights_obj.model_dump(), **generate_risk_narrative(records, insights=insights_obj, advisory=advisory)}
    return InsightsResponse(**payload)


def llm_status() -> Dict[str, Any]:
    settings = get_settings()
    available = is_available()
    model = resolve_model()
    return {
        "enabled": available,
        "provider": "openai",
        "base_url": settings.openai_base_url or "https://api.openai.com/v1",
        "configured_model": settings.openai_model,
        "resolved_model": model if available else None,
        "models": list_models() if available else [],
    }

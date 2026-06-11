from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from datetime import date

from app.models.schemas import (
    ForecastAssumptions,
    MonthlyRecord,
    PromptRequest,
    ScenarioStressParams,
)
import pandas as pd

from app.config import get_settings
from app.services.advisory_engine import generate_cashflow_advisory
from app.services.forecast_engine import (
    default_forecast_range,
    generate_base_forecast,
    generate_scenario_forecasts,
    generate_trend_forecast,
    scenario_df_summary,
    scenario_label,
)
from app.services.insights_engine import generate_insights
from app.services.llm_service import build_insights_response, generate_advisory_narrative


PROMPT_PATTERNS = [
    (r"how\s+(can|do|to|should).*(cash\s*flow|cashflow|liquidity)", "cashflow_advisory"),
    (r"ways?\s+to\s+.*(cash\s*flow|cashflow|liquidity)", "cashflow_advisory"),
    (r"next\s+(\d+)\s+months?", "trend"),
    (r"historical\s+trends?", "trend"),
    (r"scenario", "scenarios"),
    (r"delayed\s+receivable", "scenarios"),
    (r"supplier\s+payout", "scenarios"),
    (r"20\d{2}|forecast\s+for\s+the\s+year|fiscal\s+year", "base_forecast"),
    (r"5\s*%|5%\s+increase|prompt\s*3", "base_forecast"),
    (r"low\s+season|key\s+factors|positive\s+cash\s+flow", "insights"),
    (r"analyse|analyze", "insights"),
]


def classify_prompt(text: str) -> str:
    lowered = text.lower().strip()
    if re.search(r"cash\s*flow|cashflow|liquidity", lowered):
        if re.search(
            r"increase|improve|boost|raise|enhance|grow|maximize|strengthen|how\s+(can|do|to)|ways?\s+to",
            lowered,
        ):
            return "cashflow_advisory"
    for pattern, intent in PROMPT_PATTERNS:
        if re.search(pattern, lowered):
            return intent
    if get_settings().llm_enabled:
        return "llm_chat"
    return "base_forecast"


def _extract_months(text: str) -> int:
    match = re.search(r"next\s+(\d+)\s+months?", text.lower())
    if match:
        return min(int(match.group(1)), 24)
    return 5


def _extract_year(text: str) -> Optional[int]:
    match = re.search(r"(20\d{2})", text)
    return int(match.group(1)) if match else None


def _extract_forecast_months(text: str) -> Optional[int]:
    match = re.search(r"(\d+)\s*months?", text.lower())
    if match:
        return min(int(match.group(1)), 24)
    if re.search(r"\b(?:a\s+)?year\b|\b12\s*mo", text.lower()):
        return 12
    return None


def _forecast_assumptions_from_prompt(text: str, records: List[MonthlyRecord]) -> ForecastAssumptions:
    year = _extract_year(text)
    months = _extract_forecast_months(text)
    history = pd.DataFrame([r.model_dump() for r in records]).sort_values("month")
    if year is not None:
        return ForecastAssumptions(
            forecast_start=date(year, 1, 1),
            forecast_end=date(year, 12, 1),
        )
    if months is not None:
        start, end = default_forecast_range(history, months)
        return ForecastAssumptions(forecast_start=start, forecast_end=end)
    return ForecastAssumptions()


def route_prompt(records: List[MonthlyRecord], request: PromptRequest) -> Dict[str, Any]:
    intent = classify_prompt(request.prompt)

    if intent == "trend":
        months = _extract_months(request.prompt)
        forecast, model_info = generate_trend_forecast(records, months_ahead=months)
        return {
            "intent": intent,
            "prompt": request.prompt,
            "months_ahead": months,
            "forecast": [f.model_dump() for f in forecast],
            "model_metadata": model_info,
        }

    if intent == "scenarios":
        assumptions = _forecast_assumptions_from_prompt(request.prompt, records)
        stress_params = ScenarioStressParams()
        _, ratios, assumptions, scenario_dfs, model_info = generate_scenario_forecasts(
            records, assumptions, stress_params=stress_params
        )
        scenarios = []
        for stype, df in scenario_dfs.items():
            scenarios.append(
                {
                    "scenario": stype.value,
                    "label": scenario_label(stype, stress_params),
                    "forecast": df.to_dict(orient="records"),
                    "summary": scenario_df_summary(df),
                }
            )
        return {
            "intent": intent,
            "prompt": request.prompt,
            "assumptions": assumptions.model_dump(),
            "derived_ratios": ratios.model_dump(),
            "model_metadata": model_info,
            "scenarios": scenarios,
        }

    if intent == "cashflow_advisory":
        advisory = generate_cashflow_advisory(records)
        response: Dict[str, Any] = {
            "intent": intent,
            "prompt": request.prompt,
            "advisory": advisory,
        }
        if get_settings().llm_enabled:
            response.update(generate_advisory_narrative(records, request.prompt, advisory=advisory))
        return response

    if intent == "insights":
        if get_settings().llm_enabled:
            payload = build_insights_response(records).model_dump()
        else:
            payload = generate_insights(records).model_dump()
        return {
            "intent": intent,
            "prompt": request.prompt,
            "insights": payload,
        }

    if intent == "llm_chat":
        llm = generate_advisory_narrative(records, request.prompt, task="freeform")
        return {
            "intent": intent,
            "prompt": request.prompt,
            **llm,
        }

    assumptions = _forecast_assumptions_from_prompt(request.prompt, records)
    forecast, ratios, summary, issues, model_info = generate_base_forecast(records, assumptions)
    return {
        "intent": "base_forecast",
        "prompt": request.prompt,
        "assumptions": assumptions.model_dump(),
        "derived_ratios": ratios.model_dump(),
        "forecast": [f.model_dump() for f in forecast],
        "summary": summary,
        "model_metadata": model_info,
        "validation_warnings": [i.model_dump() for i in issues],
    }

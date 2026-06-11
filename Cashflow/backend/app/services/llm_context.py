from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.schemas import InsightsResponse, MonthlyRecord
from app.services.advisory_engine import generate_cashflow_advisory
from app.services.cashflow_engine import calculate_historical_cashflow
from app.services.insights_engine import generate_insights


def build_treasury_context(
    records: List[MonthlyRecord],
    *,
    insights: Optional[InsightsResponse] = None,
    advisory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    insights_obj = insights or generate_insights(records)
    _, ratios = calculate_historical_cashflow(records)
    advisory_obj = advisory or generate_cashflow_advisory(records)

    weak_months = sorted(
        insights_obj.seasonal_patterns,
        key=lambda row: float(row.get("avg_cash_flow", 0)),
    )[:3]

    return {
        "historical_summary": insights_obj.historical_summary,
        "derived_ratios": ratios.model_dump(),
        "weak_seasonal_months": weak_months,
        "ai_insights": [item.model_dump() for item in insights_obj.llm_insights],
        "advisory": {
            "executive_summary": advisory_obj["executive_summary"],
            "current_position": advisory_obj["current_position"],
            "priority_actions": advisory_obj["priority_actions"],
            "levers": [
                {"category": lever["category"], "title": lever["title"], "impact": lever["impact"]}
                for lever in advisory_obj["levers"]
            ],
            "scenario_context": advisory_obj["scenario_context"],
        },
    }

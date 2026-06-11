from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from app.models.schemas import InsightsResponse, MonthlyRecord
from app.services.cashflow_engine import calculate_historical_cashflow


def _month_name(month) -> str:
    return pd.Timestamp(month).strftime("%B")


def generate_insights(records: List[MonthlyRecord]) -> InsightsResponse:
    """Build summary context for the insights view. Insight cards come from OpenAI only."""
    cashflow_records, _ = calculate_historical_cashflow(records)
    df = pd.DataFrame([r.model_dump() for r in cashflow_records])
    df["month_num"] = pd.to_datetime(df["month"]).dt.month

    seasonal = (
        df.groupby("month_num")
        .agg(
            avg_sales=("total_sales", "mean"),
            avg_cash_flow=("cash_flow", "mean"),
            avg_expenses=("total_expenses", "mean"),
        )
        .reset_index()
    )
    seasonal["month_name"] = seasonal["month_num"].apply(lambda m: pd.Timestamp(2024, m, 1).strftime("%B"))
    seasonal_patterns = seasonal.to_dict(orient="records")

    historical_summary: Dict[str, Any] = {
        "total_months": len(df),
        "avg_monthly_sales": round(float(df["total_sales"].mean()), 2),
        "avg_monthly_cash_flow": round(float(df["cash_flow"].mean()), 2),
        "negative_cash_flow_months": int((df["cash_flow"] < 0).sum()),
        "best_month": _month_name(df.loc[df["cash_flow"].idxmax(), "month"]),
        "worst_month": _month_name(df.loc[df["cash_flow"].idxmin(), "month"]),
    }

    return InsightsResponse(
        seasonal_patterns=seasonal_patterns,
        llm_insights=[],
        historical_summary=historical_summary,
    )

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

import pandas as pd

from app.guardrails.validators import validate_forecast_output
from app.models.schemas import (
    DerivedRatios,
    ForecastAssumptions,
    ForecastMonth,
    MonthlyRecord,
    ScenarioStressParams,
    ScenarioType,
    ValidationIssue,
)
from app.services.arima_model import forecast_at_months, forecast_n_months_ahead
from app.services.cashflow_engine import calculate_cashflow_from_forecast_row, compute_derived_ratios

FORECAST_COLUMNS = [
    "total_sales",
    "total_credit_sales",
    "total_cash_sales",
    "collections",
    "total_expenses",
    "total_cash_expenses",
    "total_credit_expenses",
    "cash_paid_credit_expenses",
]


def _month_range(start: date, end: date) -> List[date]:
    dates: List[date] = []
    current = pd.Timestamp(start).replace(day=1)
    end_ts = pd.Timestamp(end).replace(day=1)
    while current <= end_ts:
        dates.append(current.date())
        current = current + pd.DateOffset(months=1)
    return dates


def default_forecast_range(history: pd.DataFrame, months: int = 12) -> Tuple[date, date]:
    last_month = pd.Timestamp(history["month"].max())
    start = (last_month + pd.DateOffset(months=1)).date().replace(day=1)
    end = (last_month + pd.DateOffset(months=months)).date().replace(day=1)
    return start, end


def _resolve_forecast_dates(history: pd.DataFrame, assumptions: ForecastAssumptions) -> List[date]:
    if assumptions.forecast_start and assumptions.forecast_end:
        return _month_range(assumptions.forecast_start, assumptions.forecast_end)
    start, end = default_forecast_range(history)
    return _month_range(start, end)


def _apply_lag(series: List[float], lag_months: int) -> List[float]:
    if lag_months <= 0:
        return series
    padded = [0.0] * lag_months + series
    return padded[lag_months : lag_months + len(series)]


def _annotate_model_mom_change_pct(
    forecast_df: pd.DataFrame,
    history: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Month-over-month % change in model cashflow vs prior period (last actual for month 1)."""
    baseline: Optional[float] = None
    if history is not None and len(history):
        baseline = float(calculate_cashflow_from_forecast_row(history.iloc[-1]))

    pcts: List[Optional[float]] = []
    prev = baseline
    for cf in forecast_df["cash_flow"]:
        if prev is None or abs(prev) < 1e-9:
            pcts.append(None)
        else:
            pcts.append(round((float(cf) - prev) / abs(prev) * 100, 2))
        prev = float(cf)

    out = forecast_df.copy()
    out["model_mom_change_pct"] = pcts
    return out


def _reconcile_pair(
    total: List[float],
    a: List[float],
    b: List[float],
) -> Tuple[List[float], List[float]]:
    """Scale components so a + b matches total each month."""
    new_a, new_b = [], []
    for t, va, vb in zip(total, a, b):
        s = va + vb
        if s <= 0 or t <= 0:
            new_a.append(max(va, 0))
            new_b.append(max(vb, 0))
            continue
        scale = t / s
        new_a.append(round(va * scale, 2))
        new_b.append(round(vb * scale, 2))
    return new_a, new_b


def _reconcile_forecast_components(forecasts: Dict[str, List[float]]) -> None:
    credit, cash = _reconcile_pair(
        forecasts["total_sales"],
        forecasts["total_credit_sales"],
        forecasts["total_cash_sales"],
    )
    forecasts["total_credit_sales"] = credit
    forecasts["total_cash_sales"] = cash

    cash_exp, credit_exp = _reconcile_pair(
        forecasts["total_expenses"],
        forecasts["total_cash_expenses"],
        forecasts["total_credit_expenses"],
    )
    forecasts["total_cash_expenses"] = cash_exp
    forecasts["total_credit_expenses"] = credit_exp


def _dataframe_from_forecasts(
    forecasts: Dict[str, List[float]],
    month_dates: List[date],
    history: pd.DataFrame,
) -> pd.DataFrame:
    _reconcile_forecast_components(forecasts)
    rows = []
    for i, month in enumerate(month_dates):
        row = {"month": month}
        for col in FORECAST_COLUMNS:
            row[col] = forecasts[col][i]
        rows.append(row)
    forecast_df = pd.DataFrame(rows)
    forecast_df["cash_flow"] = forecast_df.apply(calculate_cashflow_from_forecast_row, axis=1)
    return _annotate_model_mom_change_pct(forecast_df, history)


def _build_arima_forecast(
    history: pd.DataFrame,
    assumptions: ForecastAssumptions,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    month_dates = _resolve_forecast_dates(history, assumptions)
    target_dates = [pd.Timestamp(m) for m in month_dates]
    model_info: Dict[str, object] = {"method": "ARIMA", "series": {}}

    forecasts: Dict[str, List[float]] = {}
    for col in FORECAST_COLUMNS:
        values, meta = forecast_at_months(history, col, target_dates)
        forecasts[col] = [round(v, 2) for v in values]
        model_info["series"][col] = meta

    forecast_df = _dataframe_from_forecasts(forecasts, month_dates, history)
    return forecast_df, model_info


def _preset_stress_params(scenario: ScenarioType) -> ScenarioStressParams:
    if scenario == ScenarioType.DELAYED_RECEIVABLES:
        return ScenarioStressParams(
            stress_receivables=True,
            stress_supplier_payout=False,
            stress_expenses=False,
        )
    if scenario == ScenarioType.INCREASED_SUPPLIER_PAYOUT:
        return ScenarioStressParams(
            stress_receivables=False,
            stress_supplier_payout=True,
            stress_expenses=False,
        )
    if scenario == ScenarioType.DELAYED_AND_SPENDING:
        return ScenarioStressParams(
            stress_receivables=True,
            stress_supplier_payout=True,
            stress_expenses=True,
        )
    return ScenarioStressParams()


SCENARIO_LABELS = {
    ScenarioType.BASE: "Base Forecast",
    ScenarioType.DELAYED_RECEIVABLES: "Delayed Receivables (+30 days)",
    ScenarioType.INCREASED_SUPPLIER_PAYOUT: "Increased Supplier Payout (+20%)",
    ScenarioType.DELAYED_AND_SPENDING: "Delayed Receivables + Additional Spending (+20%)",
}


def scenario_label(stype: ScenarioType, stress_params: Optional[ScenarioStressParams] = None) -> str:
    if stype == ScenarioType.CUSTOM_STRESS:
        return format_stress_label(stress_params or ScenarioStressParams())
    return SCENARIO_LABELS.get(stype, stype.value)


def scenario_df_summary(df: pd.DataFrame) -> Dict[str, float]:
    return {
        "net_cash_flow": round(float(df["cash_flow"].sum()), 2),
        "avg_monthly_cash_flow": round(float(df["cash_flow"].mean()), 2),
    }


def format_stress_label(params: ScenarioStressParams) -> str:
    parts: List[str] = []
    if params.stress_receivables:
        parts.append(
            f"{params.receivables_delay_months}mo delay, "
            f"{round(params.receivables_collection_factor * 100)}% collections"
        )
    if params.stress_supplier_payout:
        parts.append(f"+{round(params.supplier_payout_increase_pct * 100)}% supplier payout")
    if params.stress_expenses:
        parts.append(f"+{round(params.expense_increase_pct * 100)}% expenses")
    if not parts:
        return "Custom Stress (no adjustments)"
    return f"Custom Stress ({'; '.join(parts)})"


def _apply_stress(base_df: pd.DataFrame, params: ScenarioStressParams) -> pd.DataFrame:
    df = base_df.copy()

    if params.stress_receivables:
        coll = df["total_credit_sales"].tolist()
        df["collections"] = [
            round(v * params.receivables_collection_factor, 2)
            for v in _apply_lag(coll, params.receivables_delay_months)
        ]

    if params.stress_supplier_payout:
        payout_mult = 1 + params.supplier_payout_increase_pct
        df["cash_paid_credit_expenses"] = (df["cash_paid_credit_expenses"] * payout_mult).round(2)

    if params.stress_expenses:
        expense_mult = 1 + params.expense_increase_pct
        for col in [
            "total_expenses",
            "total_cash_expenses",
            "total_credit_expenses",
            "cash_paid_credit_expenses",
        ]:
            df[col] = (df[col] * expense_mult).round(2)

    df["cash_flow"] = df.apply(calculate_cashflow_from_forecast_row, axis=1)
    return df


def _apply_scenario(
    base_df: pd.DataFrame,
    scenario: ScenarioType,
    stress_params: Optional[ScenarioStressParams] = None,
) -> pd.DataFrame:
    if scenario == ScenarioType.BASE:
        return base_df.copy()
    if scenario == ScenarioType.CUSTOM_STRESS:
        return _apply_stress(base_df, stress_params or ScenarioStressParams())
    return _apply_stress(base_df, _preset_stress_params(scenario))


def _summary(df: pd.DataFrame) -> Dict[str, float]:
    return {
        "total_sales": round(float(df["total_sales"].sum()), 2),
        "total_expenses": round(float(df["total_expenses"].sum()), 2),
        "net_cash_flow": round(float(df["cash_flow"].sum()), 2),
        "avg_monthly_cash_flow": round(float(df["cash_flow"].mean()), 2),
        "min_monthly_cash_flow": round(float(df["cash_flow"].min()), 2),
        "max_monthly_cash_flow": round(float(df["cash_flow"].max()), 2),
    }


def _to_forecast_months(df: pd.DataFrame) -> List[ForecastMonth]:
    return [ForecastMonth(**row) for row in df.to_dict(orient="records")]


def generate_base_forecast(
    records: List[MonthlyRecord],
    assumptions: Optional[ForecastAssumptions] = None,
) -> Tuple[List[ForecastMonth], DerivedRatios, Dict[str, float], List[ValidationIssue], Dict[str, object]]:
    assumptions = assumptions or ForecastAssumptions()
    history = pd.DataFrame([r.model_dump() for r in records]).sort_values("month")
    ratios = compute_derived_ratios(history)
    forecast_df, model_info = _build_arima_forecast(history, assumptions)
    issues = validate_forecast_output(forecast_df)
    return _to_forecast_months(forecast_df), ratios, _summary(forecast_df), issues, model_info


def generate_scenario_forecasts(
    records: List[MonthlyRecord],
    assumptions: Optional[ForecastAssumptions] = None,
    scenarios: Optional[List[ScenarioType]] = None,
    stress_params: Optional[ScenarioStressParams] = None,
) -> Tuple[pd.DataFrame, DerivedRatios, ForecastAssumptions, Dict[ScenarioType, pd.DataFrame], Dict[str, object]]:
    assumptions = assumptions or ForecastAssumptions()
    stress_params = stress_params or ScenarioStressParams()
    scenarios = scenarios or [ScenarioType.BASE, ScenarioType.CUSTOM_STRESS]
    history = pd.DataFrame([r.model_dump() for r in records]).sort_values("month")
    ratios = compute_derived_ratios(history)
    base_df, model_info = _build_arima_forecast(history, assumptions)

    results: Dict[ScenarioType, pd.DataFrame] = {}
    for scenario in scenarios:
        if scenario == ScenarioType.BASE:
            results[scenario] = _annotate_model_mom_change_pct(base_df.copy(), history)
        else:
            stressed = _apply_scenario(base_df, scenario, stress_params)
            results[scenario] = _annotate_model_mom_change_pct(stressed, history)
    return base_df, ratios, assumptions, results, model_info


def generate_trend_forecast(
    records: List[MonthlyRecord],
    months_ahead: int = 5,
) -> Tuple[List[ForecastMonth], Dict[str, object]]:
    history = pd.DataFrame([r.model_dump() for r in records]).sort_values("month")
    model_info: Dict[str, object] = {"method": "ARIMA", "series": {}}

    series_forecasts: Dict[str, List[float]] = {}
    month_dates: List[pd.Timestamp] = []

    for col in FORECAST_COLUMNS:
        values, months, meta = forecast_n_months_ahead(history, col, months_ahead)
        series_forecasts[col] = [round(v, 2) for v in values]
        model_info["series"][col] = meta
        if not month_dates:
            month_dates = months

    trend_months = [month_dates[i].date().replace(day=1) for i in range(months_ahead)]
    trend_df = _dataframe_from_forecasts(series_forecasts, trend_months, history)
    return _to_forecast_months(trend_df), model_info

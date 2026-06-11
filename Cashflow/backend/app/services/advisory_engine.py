from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from app.models.schemas import InsightItem, MonthlyRecord, ScenarioType
from app.services.cashflow_engine import calculate_historical_cashflow
from app.services.forecast_engine import generate_scenario_forecasts

from app.services.currency_format import format_inr


def generate_cashflow_advisory(records: List[MonthlyRecord]) -> Dict[str, Any]:
    cashflow_records, ratios = calculate_historical_cashflow(records)
    df = pd.DataFrame([r.model_dump() for r in cashflow_records])
    history = pd.DataFrame([r.model_dump() for r in records]).sort_values("month")

    avg_cf = float(df["cash_flow"].mean())
    avg_sales = float(df["total_sales"].mean())
    avg_expenses = float(df["total_expenses"].mean())
    avg_collections = float(df["collections"].mean())
    avg_cash_in = float((df["total_cash_sales"] + df["collections"]).mean())
    avg_cash_out = float((df["total_cash_expenses"] + df["cash_paid_credit_expenses"]).mean())

    worst_month = pd.Timestamp(df.loc[df["cash_flow"].idxmin(), "month"]).strftime("%B")
    best_month = pd.Timestamp(df.loc[df["cash_flow"].idxmax(), "month"]).strftime("%B")

    # Scenario uplift: base vs improved collections (inverse of delayed receivables pain)
    _, _, _, scenario_dfs, _ = generate_scenario_forecasts(
        records,
        scenarios=[ScenarioType.BASE, ScenarioType.DELAYED_RECEIVABLES],
    )
    base_cf = float(scenario_dfs[ScenarioType.BASE]["cash_flow"].sum())
    delayed_cf = float(scenario_dfs[ScenarioType.DELAYED_RECEIVABLES]["cash_flow"].sum())
    collection_risk = base_cf - delayed_cf

    levers: List[InsightItem] = []

    if ratios.avg_collection_lag_days > 20:
        days_saved = 14
        monthly_credit = float(history["total_credit_sales"].mean())
        est_monthly_uplift = monthly_credit * (days_saved / max(ratios.avg_collection_lag_days, 1)) * 0.7
        levers.append(
            InsightItem(
                category="Receivables",
                title="Accelerate collection cycle by 14 days",
                description=(
                    f"Your average collection lag is {ratios.avg_collection_lag_days:.0f} days. "
                    f"Invoicing earlier, offering small discounts for early payment, and tightening "
                    f"credit terms could release approximately {format_inr(est_monthly_uplift)} per month in cash. "
                    f"Stress testing shows delayed receivables alone could reduce annual cashflow by "
                    f"{format_inr(collection_risk)}."
                ),
                impact="high",
            )
        )

    cash_exp_share = ratios.cash_expense_ratio
    if cash_exp_share > 0.4:
        reducible = avg_expenses * cash_exp_share * 0.1
        levers.append(
            InsightItem(
                category="Expenditure",
                title="Reduce immediate cash disbursements by 10%",
                description=(
                    f"{cash_exp_share:.0%} of expenses are paid in cash each month (avg {format_inr(avg_expenses * cash_exp_share)}). "
                    f"Deferring non-essential cash purchases and renegotiating payment schedules could "
                    f"preserve roughly {format_inr(reducible)} in monthly liquidity."
                ),
                impact="high",
            )
        )

    if ratios.credit_sales_ratio > 0.4:
        shift_pct = 0.05
        monthly_uplift = avg_sales * shift_pct * (ratios.avg_collection_lag_days / 30)
        levers.append(
            InsightItem(
                category="Revenue Mix",
                title="Shift 5% of credit sales to cash settlement",
                description=(
                    f"Credit sales are {ratios.credit_sales_ratio:.0%} of revenue. Incentivizing upfront payment "
                    f"(early-payment discounts, preferred pricing for wire transfer) accelerates cash without "
                    f"reducing volume — potentially improving monthly cashflow by {format_inr(monthly_uplift)}."
                ),
                impact="medium",
            )
        )

    if ratios.avg_payment_lag_days < 45:
        payable_buffer = float(history["total_credit_expenses"].mean()) * 0.15
        levers.append(
            InsightItem(
                category="Payables",
                title="Extend supplier payment terms by 15 days",
                description=(
                    f"Average supplier payment cycle is ~{ratios.avg_payment_lag_days:.0f} days. "
                    f"Negotiating extended terms on your top vendors could retain {format_inr(payable_buffer)} "
                    f"in working capital per month without reducing procurement."
                ),
                impact="medium",
            )
        )

    levers.append(
        InsightItem(
            category="Working Capital",
            title=f"Build liquidity buffer before {worst_month}",
            description=(
                f"Historical analysis shows {worst_month} as the weakest cashflow month "
                f"(best: {best_month}). Maintain a reserve of at least {format_inr(avg_expenses * 2)} "
                f"(2× average monthly expenses) entering low-season periods."
            ),
            impact="high",
        )
    )

    executive_summary = (
        f"Based on {len(df)} months of data, your average monthly cashflow is {format_inr(avg_cf)} "
        f"(cash in {format_inr(avg_cash_in)} vs cash out {format_inr(avg_cash_out)}). "
        f"To increase cashflow, prioritize receivables acceleration and cash expense discipline — "
        f"these two levers address the largest timing gaps in your current operating cycle. "
        f"Scenario analysis indicates receivables delays pose the greatest single risk to liquidity."
    )

    formula_reminder = (
        "Cashflow = (Cash Sales + Collections) − (Cash Expenses + Cash Paid to Suppliers). "
        "Improving cashflow requires increasing inflows, reducing outflows, or shifting timing "
        "of when cash moves — not just increasing revenue."
    )

    return {
        "executive_summary": executive_summary,
        "formula": formula_reminder,
        "current_position": {
            "avg_monthly_cashflow": round(avg_cf, 2),
            "avg_monthly_cash_in": round(avg_cash_in, 2),
            "avg_monthly_cash_out": round(avg_cash_out, 2),
            "avg_monthly_sales": round(avg_sales, 2),
            "avg_monthly_collections": round(avg_collections, 2),
            "best_month": best_month,
            "weakest_month": worst_month,
            "collection_lag_days": round(ratios.avg_collection_lag_days, 1),
            "payment_lag_days": round(ratios.avg_payment_lag_days, 1),
        },
        "levers": [item.model_dump() for item in levers],
        "priority_actions": [
            "Tighten credit terms and follow up on overdue receivables within 7 days of due date.",
            "Review discretionary cash expenses and defer non-critical purchases to high-cash months.",
            "Incentivize cash/upfront payment for new sales during weak liquidity periods.",
            "Negotiate 15–30 day payment extensions with key suppliers.",
            "Monitor ARIMA forecast monthly and adjust working capital before seasonal dips.",
        ],
        "scenario_context": {
            "annual_base_cashflow": round(base_cf, 2),
            "impact_if_receivables_delayed": round(collection_risk, 2),
            "message": (
                f"Delaying collections by 30 days could reduce annual net cashflow by "
                f"{format_inr(collection_risk)} — highlighting collections as the highest-impact lever."
            ),
        },
    }

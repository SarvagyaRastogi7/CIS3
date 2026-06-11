from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

from app.models.schemas import CashflowRecord, DerivedRatios, MonthlyRecord


def compute_derived_ratios(df: pd.DataFrame) -> DerivedRatios:
    sales = df["total_sales"].replace(0, np.nan)
    expenses = df["total_expenses"].replace(0, np.nan)
    credit_exp = df["total_credit_expenses"].replace(0, np.nan)

    collection_lags = []
    payment_lags = []
    for _, row in df.iterrows():
        if row["total_credit_sales"] > 0 and row["collections"] > 0:
            implied_rate = min(row["collections"] / row["total_credit_sales"], 1.0)
            collection_lags.append(30 * (1 - implied_rate) + 14 * implied_rate)
        if row["total_credit_expenses"] > 0 and row["cash_paid_credit_expenses"] > 0:
            pay_rate = min(row["cash_paid_credit_expenses"] / row["total_credit_expenses"], 1.0)
            payment_lags.append(45 * (1 - pay_rate) + 15 * pay_rate)

    return DerivedRatios(
        cash_sale_percent=float((df["total_cash_sales"] / sales).mean()),
        expense_ratio=float((df["total_expenses"] / sales).mean()),
        cash_expense_ratio=float((df["total_cash_expenses"] / expenses).mean()),
        credit_expenses_paid_ratio=float((df["cash_paid_credit_expenses"] / credit_exp).mean()),
        credit_sales_ratio=float((df["total_credit_sales"] / sales).mean()),
        avg_collection_lag_days=float(np.mean(collection_lags) if collection_lags else 30),
        avg_payment_lag_days=float(np.mean(payment_lags) if payment_lags else 45),
    )


def calculate_cashflow_row(row: pd.Series, ratios: DerivedRatios) -> Tuple[float, float, float]:
    credit_sales_days = max((ratios.credit_sales_ratio * 30), 1)
    cash_collected_credit = row["total_credit_sales"] / credit_sales_days * 30
    cash_inflows = row["total_cash_sales"] + cash_collected_credit
    cash_outflows = row["total_cash_expenses"] + (
        row["total_credit_expenses"] * ratios.credit_expenses_paid_ratio
    )
    return cash_inflows - cash_outflows, cash_inflows, cash_outflows


def calculate_historical_cashflow(
    records: List[MonthlyRecord],
) -> Tuple[List[CashflowRecord], DerivedRatios]:
    df = pd.DataFrame([r.model_dump() for r in records]).sort_values("month")
    ratios = compute_derived_ratios(df)

    results: List[CashflowRecord] = []
    for _, row in df.iterrows():
        cash_flow, inflows, outflows = calculate_cashflow_row(row, ratios)
        payload = row.to_dict()
        payload.update(
            {
                "cash_flow": round(cash_flow, 2),
                "cash_inflows": round(inflows, 2),
                "cash_outflows": round(outflows, 2),
            }
        )
        results.append(CashflowRecord(**payload))
    return results, ratios


def calculate_cashflow_from_forecast_row(row: pd.Series) -> float:
    inflows = row["total_cash_sales"] + row["collections"]
    outflows = row["total_cash_expenses"] + row["cash_paid_credit_expenses"]
    return round(float(inflows - outflows), 2)

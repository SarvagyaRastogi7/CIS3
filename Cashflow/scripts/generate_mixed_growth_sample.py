"""Generate sample data through May 2026 with mixed positive and negative growth phases."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

OUTPUT = Path(__file__).resolve().parents[1] / "sample_data" / "sample_data_mixed_growth_may26.xlsx"

COLUMNS = [
    "Month",
    "Total Sales",
    "Total Credit Sales",
    "Total Cash Sales",
    "Collections",
    "Total Expenses",
    "Total Cash Expenses",
    "Total Credit Expenses",
    "Cash Paid for Credit Expenses",
]

# (months, monthly growth rate) — 41 months: Jan-23 through May-26
GROWTH_PHASES: list[tuple[int, float]] = [
    (6, 0.07),    # Jan–Jun 23: strong expansion
    (6, -0.025),  # Jul–Dec 23: mild contraction
    (8, 0.055),   # Jan–Aug 24: recovery rally
    (6, -0.04),   # Sep 24–Feb 25: downturn
    (10, 0.038),  # Mar 25–Dec 25: rebound
    (5, 0.015),   # Jan–May 26: steady growth
]

# Small month-to-month noise so ARIMA sees realistic volatility (fixed seed).
NOISE = [
    0.01, -0.005, 0.008, -0.012, 0.006, 0.003,
    -0.008, 0.004, -0.006, 0.002, -0.01, 0.005,
    0.012, -0.004, 0.007, 0.0, -0.009, 0.011, 0.005, -0.007,
    -0.013, 0.006, -0.004, 0.008, -0.011, 0.003,
    0.014, -0.005, 0.009, 0.002, -0.008, 0.006, 0.01, -0.003, 0.007,
    0.004, -0.006, 0.008, 0.0, -0.005, 0.006,
]


def _round_step(value: float, step: int = 5_000) -> int:
    return int(round(value / step) * step)


def _monthly_growth_rates() -> list[float]:
    rates: list[float] = []
    noise_i = 0
    for months, base_rate in GROWTH_PHASES:
        for _ in range(months):
            jitter = NOISE[noise_i] if noise_i < len(NOISE) else 0.0
            rates.append(base_rate + jitter)
            noise_i += 1
    return rates


def _build_sales_series(start: float, rates: list[float]) -> list[int]:
    values = [start]
    for rate in rates[:-1]:
        values.append(values[-1] * (1 + rate))
    return [_round_step(v, 5_000) for v in values]


def _derive_row(sales: int, prior_credit_sales: int) -> dict[str, int]:
    credit_ratio = 0.43
    credit_sales = _round_step(sales * credit_ratio, 5_000)
    cash_sales = sales - credit_sales

    # Collections lag prior-month credit slightly.
    collections = _round_step(0.72 * prior_credit_sales + 0.18 * credit_sales, 5_000)

    expense_ratio = 0.46
    expenses = _round_step(sales * expense_ratio, 5_000)
    cash_expenses = _round_step(expenses * 0.52, 5_000)
    credit_expenses = expenses - cash_expenses
    cash_paid = _round_step(credit_expenses * 0.9, 5_000)

    return {
        "Total Sales": sales,
        "Total Credit Sales": credit_sales,
        "Total Cash Sales": cash_sales,
        "Collections": min(collections, credit_sales),
        "Total Expenses": expenses,
        "Total Cash Expenses": cash_expenses,
        "Total Credit Expenses": credit_expenses,
        "Cash Paid for Credit Expenses": min(cash_paid, credit_expenses),
    }


def generate() -> pd.DataFrame:
    rates = _monthly_growth_rates()
    assert len(rates) == 41, f"Expected 41 months, got {len(rates)}"

    sales_series = _build_sales_series(380_000, rates)
    start = date(2023, 1, 1)
    rows: list[dict[str, object]] = []
    prior_credit = int(sales_series[0] * 0.43)

    for i, sales in enumerate(sales_series):
        month = pd.Timestamp(start) + pd.DateOffset(months=i)
        metrics = _derive_row(sales, prior_credit)
        prior_credit = metrics["Total Credit Sales"]
        rows.append({"Month": month.strftime("%b-%y"), **metrics})

    return pd.DataFrame(rows, columns=COLUMNS)


def main() -> None:
    df = generate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUTPUT, index=False, engine="openpyxl")
    print(f"Wrote {OUTPUT} ({len(df)} rows, {df['Month'].iloc[0]} – {df['Month'].iloc[-1]})")

    # Quick growth summary for the console.
    sales = df["Total Sales"].astype(float)
    mom = sales.pct_change().dropna()
    print(f"Sales range: ₹{sales.min():,.0f} – ₹{sales.max():,.0f}")
    print(f"MoM growth: min {mom.min():.1%}, max {mom.max():.1%}, negative months {int((mom < 0).sum())}")


if __name__ == "__main__":
    main()

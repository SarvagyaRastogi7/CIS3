from __future__ import annotations

from datetime import date

from app.models.schemas import MonthlyRecord


def make_monthly_record(
    month: date,
    *,
    sales: float = 100_000,
    collection_factor: float = 0.7,
) -> MonthlyRecord:
    credit = sales * 0.6
    cash = sales - credit
    expenses = sales * 0.8
    cash_exp = expenses * 0.5
    credit_exp = expenses - cash_exp
    return MonthlyRecord(
        month=month,
        total_sales=sales,
        total_credit_sales=credit,
        total_cash_sales=cash,
        collections=credit * collection_factor,
        total_expenses=expenses,
        total_cash_expenses=cash_exp,
        total_credit_expenses=credit_exp,
        cash_paid_credit_expenses=credit_exp * 0.75,
    )


def make_monthly_records(
    count: int = 15,
    *,
    start_year: int = 2023,
    sales_base: float = 100_000,
    sales_step: float = 5_000,
    collection_factor: float = 0.7,
) -> list[MonthlyRecord]:
    return [
        make_monthly_record(
            date(start_year + (i // 12), (i % 12) + 1, 1),
            sales=sales_base + i * sales_step,
            collection_factor=collection_factor,
        )
        for i in range(count)
    ]

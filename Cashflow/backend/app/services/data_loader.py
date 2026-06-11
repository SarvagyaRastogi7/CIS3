from __future__ import annotations

import io
from typing import List

import pandas as pd

from app.models.schemas import MonthlyRecord
from app.utils.dates import parse_month_value

COLUMN_ALIASES = {
    "month": ["month", "date", "period", "mnth"],
    "total_sales": ["total sales", "total_sales", "sales"],
    "total_credit_sales": ["total credit sales", "credit sales", "total_credit_sales", "credit_sales"],
    "total_cash_sales": ["total cash sales", "cash sales", "total_cash_sales", "cash_sales"],
    "collections": [
        "collection from credit sales",
        "collections from credit sales",
        "collections",
        "collection",
    ],
    "total_expenses": ["total expenses", "total_expenses", "expenses"],
    "total_cash_expenses": ["total cash expenses", "cash expenses", "total_cash_expenses"],
    "total_credit_expenses": ["total credit expenses", "credit expenses", "total_credit_expenses"],
    "cash_paid_credit_expenses": [
        "cash paid for credit expenses",
        "cash paid to suppliers",
        "cash_paid_credit_expenses",
        "cash paid",
    ],
}


def _normalize_header(value: str) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def _resolve_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = {_normalize_header(c): c for c in df.columns}
    mapping = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = _normalize_header(alias)
            if key in normalized:
                mapping[normalized[key]] = canonical
                break
    missing = [k for k in COLUMN_ALIASES if k not in mapping.values()]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return df.rename(columns=mapping)[list(COLUMN_ALIASES.keys())]


def load_from_excel(content: bytes) -> List[MonthlyRecord]:
    try:
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"Failed to read Excel file: {exc}") from exc

    if df.empty:
        raise ValueError("Excel file contains no data rows.")

    df = _resolve_columns(df)
    df["month"] = df["month"].apply(parse_month_value)

    numeric_cols = [c for c in df.columns if c != "month"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[numeric_cols].isna().any().any():
        raise ValueError("Non-numeric or missing values found in financial columns.")

    records = [MonthlyRecord(**row) for row in df.to_dict(orient="records")]
    records.sort(key=lambda r: r.month)
    return records

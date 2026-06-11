from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

from app.config import get_settings
from app.models.schemas import MonthlyRecord, ValidationIssue, ValidationReport


TOLERANCE = 0.02


def _issue(severity: str, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(severity=severity, field=field, message=message)


def validate_records(records: List[MonthlyRecord]) -> ValidationReport:
    settings = get_settings()
    issues: List[ValidationIssue] = []

    if len(records) < settings.min_history_months:
        issues.append(
            _issue(
                "error",
                "record_count",
                f"At least {settings.min_history_months} months of data required; got {len(records)}.",
            )
        )

    if len(records) == 0:
        return ValidationReport(valid=False, issues=issues, record_count=0)

    df = pd.DataFrame([r.model_dump() for r in records]).sort_values("month")

    if df["month"].duplicated().any():
        issues.append(_issue("error", "month", "Duplicate months detected in dataset."))

    for idx, row in df.iterrows():
        month_label = str(row["month"])[:7]
        sales = row["total_sales"]
        credit = row["total_credit_sales"]
        cash = row["total_cash_sales"]
        expenses = row["total_expenses"]
        cash_exp = row["total_cash_expenses"]
        credit_exp = row["total_credit_expenses"]

        if sales <= 0:
            issues.append(_issue("error", "total_sales", f"{month_label}: total sales must be positive."))

        if abs((credit + cash) - sales) / max(sales, 1) > TOLERANCE:
            issues.append(
                _issue(
                    "warning",
                    "total_sales",
                    f"{month_label}: credit + cash sales deviate from total sales by >{TOLERANCE * 100:.0f}%.",
                )
            )

        if abs((cash_exp + credit_exp) - expenses) / max(expenses, 1) > TOLERANCE:
            issues.append(
                _issue(
                    "warning",
                    "total_expenses",
                    f"{month_label}: cash + credit expenses deviate from total expenses by >{TOLERANCE * 100:.0f}%.",
                )
            )

        if row["collections"] > credit * 1.5:
            issues.append(
                _issue(
                    "warning",
                    "collections",
                    f"{month_label}: collections unusually high relative to credit sales.",
                )
            )

        if row["cash_paid_credit_expenses"] > credit_exp * 1.5:
            issues.append(
                _issue(
                    "warning",
                    "cash_paid_credit_expenses",
                    f"{month_label}: cash paid for credit expenses unusually high.",
                )
            )

    numeric_cols = [
        "total_sales",
        "total_credit_sales",
        "total_cash_sales",
        "collections",
        "total_expenses",
    ]
    for col in numeric_cols:
        series = df[col].astype(float)
        if series.isna().any() or np.isinf(series).any():
            issues.append(_issue("error", col, f"Invalid numeric values found in {col}."))
            continue
        if (series < 0).any():
            issues.append(_issue("error", col, f"Negative values found in {col}."))

        mean, std = series.mean(), series.std()
        if std > 0:
            z_scores = np.abs((series - mean) / std)
            outliers = z_scores[z_scores > 4]
            if len(outliers) > 0:
                issues.append(
                    _issue(
                        "warning",
                        col,
                        f"{col} has {len(outliers)} outlier month(s) beyond 4 standard deviations.",
                    )
                )

    has_errors = any(i.severity == "error" for i in issues)
    return ValidationReport(valid=not has_errors, issues=issues, record_count=len(records))


def validate_forecast_output(forecast_df: pd.DataFrame) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if forecast_df.empty:
        issues.append(_issue("error", "forecast", "Forecast produced no rows."))
        return issues

    for col in ["total_sales", "total_expenses", "cash_flow"]:
        if (forecast_df[col] < 0).sum() > len(forecast_df) * 0.5:
            issues.append(
                _issue(
                    "warning",
                    col,
                    f"More than half of forecast {col} values are negative — review assumptions.",
                )
            )

    if forecast_df["total_sales"].isna().any() or np.isinf(forecast_df["total_sales"]).any():
        issues.append(_issue("error", "total_sales", "Forecast contains invalid sales values."))

    return issues


def sanitize_upload_filename(filename: str) -> str:
    safe = "".join(c for c in filename if c.isalnum() or c in "._-")
    return safe[:128] or "upload.xlsx"


def check_file_size(size_bytes: int) -> Tuple[bool, str]:
    settings = get_settings()
    if size_bytes > settings.max_upload_bytes:
        max_mb = settings.max_upload_bytes / (1024 * 1024)
        return False, f"File exceeds maximum allowed size of {max_mb:.1f} MB."
    if size_bytes == 0:
        return False, "Uploaded file is empty."
    return True, ""

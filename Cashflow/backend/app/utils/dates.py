from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

import pandas as pd

_MONTH_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m",
    "%b-%y",
    "%b-%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
)


def parse_month_value(value: Any) -> date:
    """Normalize a month input to the first day of that calendar month."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.replace(day=1)
    if isinstance(value, datetime):
        return value.date().replace(day=1)
    if isinstance(value, pd.Timestamp):
        return value.date().replace(day=1)

    text = str(value).strip()
    for fmt in _MONTH_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().replace(day=1)
        except ValueError:
            continue

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Unable to parse month value: {value}")
    return parsed.date().replace(day=1)


def parse_month_value_optional(value: Any) -> Optional[date]:
    if value is None:
        return None
    return parse_month_value(value)

from __future__ import annotations

import re
from typing import Any

MONEY_KEY_HINTS = (
    "sales",
    "expense",
    "cash_flow",
    "cashflow",
    "collection",
    "revenue",
    "payout",
    "inflow",
    "outflow",
    "paid",
    "amount",
    "liquidity",
    "uplift",
    "impact",
    "annual",
    "net_cash",
    "avg_monthly",
    "min_monthly",
    "max_monthly",
    "total_",
)

MONEY_KEY_EXCLUDES = (
    "ratio",
    "percent",
    "pct",
    "rate",
    "days",
    "months",
    "month_num",
    "lag",
    "order",
    "aic",
    "total_months",
    "negative_cash_flow_months",
    "model_mom",
)


def format_inr(value: float, maximum_fraction_digits: int = 0) -> str:
    sign = "-" if value < 0 else ""
    abs_val = abs(value)
    if maximum_fraction_digits:
        formatted = f"{abs_val:,.{maximum_fraction_digits}f}"
    else:
        formatted = f"{abs_val:,.0f}"
    return f"{sign}₹{formatted}"


def format_inr_compact(value: float) -> str:
    abs_val = abs(value)
    if abs_val >= 1e7:
        return f"₹{value / 1e7:.2f} Cr"
    if abs_val >= 1e5:
        return f"₹{value / 1e5:.2f} L"
    return format_inr(value)


def _is_money_key(key: str) -> bool:
    lowered = key.lower()
    if any(exclude in lowered for exclude in MONEY_KEY_EXCLUDES):
        return False
    return any(hint in lowered for hint in MONEY_KEY_HINTS)


def _format_money_value(value: float) -> str:
    if abs(value) >= 1e5:
        return format_inr_compact(value)
    return format_inr(value)


def format_context_for_llm(obj: Any, key: str = "") -> Any:
    if isinstance(obj, dict):
        formatted: dict[str, Any] = {}
        for child_key, child_value in obj.items():
            if isinstance(child_value, (int, float)) and _is_money_key(child_key):
                formatted[child_key] = _format_money_value(float(child_value))
            else:
                formatted[child_key] = format_context_for_llm(child_value, child_key)
        return formatted
    if isinstance(obj, list):
        return [format_context_for_llm(item, key) for item in obj]
    if isinstance(obj, (int, float)) and _is_money_key(key):
        return _format_money_value(float(obj))
    return obj


INR_OUTPUT_RULES = (
    "All monetary amounts are Indian Rupees (INR). "
    "Always write amounts as ₹X,XXX or ₹X.XX L (lakh) / ₹X.XX Cr (crore). "
    "Never use USD ($), 'million', 'M', or 'bn' for money."
)


def normalize_inr_in_narrative(text: str | None) -> str | None:
    if not text:
        return text
    cleaned = text.replace("$", "₹")
    cleaned = re.sub(
        r"₹([\d,]+(?:\.\d+)?)\s*(?:million|mn|m)\b",
        lambda m: format_inr_compact(float(m.group(1).replace(",", "")) * 1_000_000),
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned

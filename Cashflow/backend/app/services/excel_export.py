from __future__ import annotations

import io
from typing import List

import pandas as pd

from app.models.schemas import ForecastMonth


def export_forecast_to_excel(forecast: List[ForecastMonth], sheet_name: str = "Forecast 2026") -> bytes:
    df = pd.DataFrame([f.model_dump() for f in forecast])
    df["month"] = pd.to_datetime(df["month"]).dt.strftime("%b-%y")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    buffer.seek(0)
    return buffer.read()


def export_scenarios_to_excel(scenarios: dict) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, rows in scenarios.items():
            df = pd.DataFrame(rows)
            if "month" in df.columns:
                df["month"] = pd.to_datetime(df["month"]).dt.strftime("%b-%y")
            safe_name = "".join(c for c in name if c.isalnum() or c in " _-")[:31]
            df.to_excel(writer, index=False, sheet_name=safe_name or "Sheet")
    buffer.seek(0)
    return buffer.read()

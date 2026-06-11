from datetime import date

import pandas as pd

from app.models.schemas import ForecastAssumptions
from app.services.arima_model import forecast_at_months, forecast_series
from app.services.forecast_engine import generate_base_forecast
from tests.factories import make_monthly_records


def test_forecast_series_returns_positive_values():
    series = pd.Series([100_000 + i * 3_000 for i in range(24)])
    values, meta = forecast_series(series, steps=6, series_name="total_sales")
    assert len(values) == 6
    assert all(v >= 0 for v in values)
    assert meta["method"] == "ARIMA"
    assert len(meta["order"]) == 3


def test_forecast_at_months_targets_calendar_year():
    history = pd.DataFrame(
        {
            "month": pd.date_range("2023-01-01", periods=24, freq="MS"),
            "total_sales": [100_000 + i * 3_000 for i in range(24)],
        }
    )
    targets = [pd.Timestamp(2026, m, 1) for m in range(1, 13)]
    values, meta = forecast_at_months(history, "total_sales", targets)
    assert len(values) == 12
    assert meta["method"] == "ARIMA"


def test_base_forecast_uses_arima_metadata():
    records = make_monthly_records(24)
    forecast, _, summary, _, model_info = generate_base_forecast(
        records,
        ForecastAssumptions(forecast_start=date(2026, 1, 1), forecast_end=date(2026, 12, 31)),
    )
    assert len(forecast) == 12
    assert summary["total_sales"] > 0
    assert model_info["method"] == "ARIMA"
    assert "total_sales" in model_info["series"]

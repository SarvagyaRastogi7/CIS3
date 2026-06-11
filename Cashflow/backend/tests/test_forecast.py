from datetime import date

from app.models.schemas import ForecastAssumptions
from app.services.cashflow_engine import calculate_historical_cashflow
from app.services.forecast_engine import generate_base_forecast, generate_trend_forecast
from tests.factories import make_monthly_records


def test_historical_cashflow_produces_values():
    records = make_monthly_records()
    cashflow, ratios = calculate_historical_cashflow(records)
    assert len(cashflow) == len(records)
    assert ratios.expense_ratio > 0


def test_base_forecast_returns_twelve_months_by_default():
    records = make_monthly_records()
    forecast, _, summary, _, model_info = generate_base_forecast(records, ForecastAssumptions())
    assert model_info["method"] == "ARIMA"
    assert len(forecast) == 12
    assert summary["total_sales"] > 0


def test_base_forecast_includes_model_mom_change_pct():
    records = make_monthly_records()
    forecast, _, _, _, _ = generate_base_forecast(records, ForecastAssumptions())
    assert forecast[0].model_mom_change_pct is not None
    assert forecast[1].model_mom_change_pct is not None
    first_cf = forecast[0].cash_flow
    expected_second = round((forecast[1].cash_flow - first_cf) / abs(first_cf) * 100, 2)
    assert forecast[1].model_mom_change_pct == expected_second


def test_base_forecast_custom_date_range():
    records = make_monthly_records()
    assumptions = ForecastAssumptions(
        forecast_start=date(2024, 4, 1),
        forecast_end=date(2024, 9, 1),
    )
    forecast, _, _, _, _ = generate_base_forecast(records, assumptions)
    assert len(forecast) == 6
    assert forecast[0].month == date(2024, 4, 1)
    assert forecast[-1].month == date(2024, 9, 1)


def test_base_forecast_calendar_year_range():
    records = make_monthly_records()
    forecast, _, _, _, _ = generate_base_forecast(
        records,
        ForecastAssumptions(forecast_start=date(2028, 1, 1), forecast_end=date(2028, 12, 1)),
    )
    assert len(forecast) == 12
    assert forecast[0].month.year == 2028


def test_trend_forecast_respects_months_ahead():
    records = make_monthly_records()
    forecast, model_info = generate_trend_forecast(records, months_ahead=5)
    assert len(forecast) == 5
    assert model_info["method"] == "ARIMA"

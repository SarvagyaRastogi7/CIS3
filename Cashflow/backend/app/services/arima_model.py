from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

from app.config import get_settings

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


@dataclass
class ArimaFitResult:
    series_name: str
    order: Tuple[int, int, int]
    aic: float


def _months_between(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def _suggest_d(series: np.ndarray, max_d: int) -> int:
    for d in range(max_d + 1):
        test_series = series if d == 0 else np.diff(series, n=d)
        if len(test_series) < 4:
            return d
        try:
            p_value = adfuller(test_series, autolag="AIC")[1]
            if p_value < 0.05:
                return d
        except Exception:
            return d
    return max_d


def _fit_best_arima(series: np.ndarray, series_name: str) -> ArimaFitResult:
    settings = get_settings()
    series = np.asarray(series, dtype=float)
    series = np.maximum(series, 0)

    if len(series) < settings.min_history_months:
        raise ValueError(f"Need at least {settings.min_history_months} points for ARIMA on {series_name}.")

    d = _suggest_d(series, settings.arima_max_d)
    best_order = (1, d, 1)
    best_aic = float("inf")
    best_model = None

    for p in range(settings.arima_max_p + 1):
        for q in range(settings.arima_max_q + 1):
            if p == 0 and q == 0:
                continue
            try:
                model = ARIMA(series, order=(p, d, q))
                fitted = model.fit()
                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_order = (p, d, q)
                    best_model = fitted
            except Exception:
                continue

    if best_model is None:
        model = ARIMA(series, order=(1, d, 0))
        best_model = model.fit()
        best_order = (1, d, 0)
        best_aic = best_model.aic

    return ArimaFitResult(
        series_name=series_name,
        order=best_order,
        aic=float(best_aic),
    )


def forecast_series(
    history: pd.Series,
    steps: int,
    series_name: str,
) -> Tuple[List[float], Dict[str, object]]:
    """Fit ARIMA on history and forecast `steps` periods ahead."""
    if steps < 1:
        last = float(history.iloc[-1])
        return [last], {"series": series_name, "order": [0, 0, 0], "aic": None, "method": "last_value"}

    fit_meta = _fit_best_arima(history.values, series_name)
    model = ARIMA(history.values, order=fit_meta.order)
    fitted = model.fit()
    forecast = fitted.forecast(steps=steps)
    values = [float(max(v, 0)) for v in forecast]

    return values, {
        "series": series_name,
        "order": list(fit_meta.order),
        "aic": round(float(fitted.aic), 2),
        "method": "ARIMA",
    }


def forecast_at_months(
    history: pd.DataFrame,
    column: str,
    target_months: List[pd.Timestamp],
) -> Tuple[List[float], Dict[str, object]]:
    """Forecast values at specific future month dates using one ARIMA fit."""
    last_month = pd.Timestamp(history["month"].max())
    max_steps = max(_months_between(last_month, pd.Timestamp(m)) for m in target_months)
    all_forecasts, meta = forecast_series(history[column], max_steps, column)

    result = []
    for target in target_months:
        step = _months_between(last_month, pd.Timestamp(target))
        if step <= 0:
            result.append(float(history[column].iloc[-1]))
        else:
            result.append(all_forecasts[step - 1])

    return result, meta


def forecast_n_months_ahead(
    history: pd.DataFrame,
    column: str,
    months_ahead: int,
) -> Tuple[List[float], List[pd.Timestamp], Dict[str, object]]:
    last_month = pd.Timestamp(history["month"].max())
    values, meta = forecast_series(history[column], months_ahead, column)
    months = [last_month + pd.DateOffset(months=i) for i in range(1, months_ahead + 1)]
    return values, months, meta

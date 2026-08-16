"""Deterministic educational indicators and leakage-resistant research baselines."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import numpy as np

from repositories.base import SupabaseRepository

INDICATOR_VERSION = "technical-indicators-1.0.0"
FORECAST_VERSION = "walk-forward-linear-1.0.0"


def _ema(values: np.ndarray, span: int) -> np.ndarray:
    alpha = 2 / (span + 1)
    output = np.empty_like(values, dtype=float)
    output[0] = values[0]
    for index in range(1, len(values)):
        output[index] = alpha * values[index] + (1 - alpha) * output[index - 1]
    return output


def _rsi(values: np.ndarray, period: int = 14) -> np.ndarray:
    delta = np.diff(values, prepend=values[0])
    gains, losses = np.maximum(delta, 0), np.maximum(-delta, 0)
    avg_gain, avg_loss = _ema(gains, period), _ema(losses, period)
    ratio = np.divide(avg_gain, avg_loss, out=np.full_like(avg_gain, np.inf), where=avg_loss > 0)
    return 100 - (100 / (1 + ratio))


def indicator_series(dates: list[str], closes: list[float]) -> dict[str, Any]:
    if len(closes) < 35 or len(dates) != len(closes):
        raise ValueError("At least 35 aligned dates and adjusted closing prices are required")
    values = np.asarray(closes, dtype=float)
    parsed_dates = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in dates]
    if any(current <= previous for previous, current in zip(parsed_dates, parsed_dates[1:])):
        raise ValueError("Dates must be unique and strictly increasing")
    if not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("Prices must be finite and greater than zero")
    ema12, ema26 = _ema(values, 12), _ema(values, 26)
    macd = ema12 - ema26
    signal = _ema(macd, 9)
    rsi = _rsi(values)
    points: list[dict[str, Any]] = []
    for index, value in enumerate(values):
        start = max(0, index - 19)
        window = values[start : index + 1]
        mean, std = float(np.mean(window)), float(np.std(window))
        points.append(
            {
                "date": dates[index], "close": round(float(value), 6),
                "rsi_14": round(float(rsi[index]), 4),
                "macd_12_26": round(float(macd[index]), 6),
                "macd_signal_9": round(float(signal[index]), 6),
                "bollinger_mid_20": round(mean, 6) if len(window) == 20 else None,
                "bollinger_upper_20": round(mean + 2 * std, 6) if len(window) == 20 else None,
                "bollinger_lower_20": round(mean - 2 * std, 6) if len(window) == 20 else None,
                "momentum_10": round(float(value / values[index - 10] - 1), 6) if index >= 10 else None,
            }
        )
    returns = np.diff(np.log(values))
    volatility = float(np.std(returns, ddof=1) * math.sqrt(252)) if len(returns) > 1 else 0
    running_high = np.maximum.accumulate(values)
    drawdown = values / running_high - 1
    return {
        "formula_version": INDICATOR_VERSION,
        "window_coverage": {"observations": len(values), "first_date": dates[0], "last_date": dates[-1]},
        "annualized_volatility": round(volatility, 6),
        "maximum_drawdown": round(float(np.min(drawdown)), 6),
        "latest": points[-1],
        "points": points,
        "disclaimer": "Educational historical analytics only; not a trade instruction or a promise of future performance.",
    }


def walk_forward_forecast(values: list[float], window: int = 20) -> dict[str, Any]:
    series = np.asarray(values, dtype=float)
    if len(series) < max(60, window + 10):
        raise ValueError("At least 60 adjusted prices are required for walk-forward evaluation")
    if not np.all(np.isfinite(series)) or np.any(series <= 0):
        raise ValueError("Prices must be finite and greater than zero")
    candidate, baseline, actual = [], [], []
    x = np.arange(window, dtype=float)
    for index in range(window, len(series)):
        train = series[index - window : index]
        slope, intercept = np.polyfit(x, train, 1)
        candidate.append(float(intercept + slope * window))
        baseline.append(float(train[-1]))
        actual.append(float(series[index]))
    candidate_rmse = float(np.sqrt(np.mean((np.asarray(candidate) - actual) ** 2)))
    baseline_rmse = float(np.sqrt(np.mean((np.asarray(baseline) - actual) ** 2)))
    x_next = np.arange(window, dtype=float)
    slope, intercept = np.polyfit(x_next, series[-window:], 1)
    prediction = float(intercept + slope * window)
    residual = float(np.std(np.asarray(candidate) - actual, ddof=1))
    beats = candidate_rmse < baseline_rmse * 0.98
    return {
        "model_version": FORECAST_VERSION,
        "evaluation": "expanding walk-forward one-step evaluation with no future observations in training",
        "window": window,
        "observations": len(series),
        "candidate_rmse": round(candidate_rmse, 6),
        "naive_last_value_rmse": round(baseline_rmse, 6),
        "status": "research_candidate" if beats else "experimental_underperforming_baseline",
        "next_value_estimate": round(prediction, 6),
        "uncertainty_95": [round(prediction - 1.96 * residual, 6), round(prediction + 1.96 * residual, 6)],
        "disclaimer": "Experimental research output with uncertainty; not a personalized recommendation or trade instruction.",
    }


def synthetic_regimes(seed: int, days: int) -> dict[str, Any]:
    generator = np.random.default_rng(seed)
    regimes = {
        "calm": (0.0003, 0.006), "volatile": (0.0001, 0.025), "drawdown": (-0.0015, 0.018),
    }
    output: dict[str, Any] = {}
    for name, (drift, volatility) in regimes.items():
        returns = generator.normal(drift, volatility, days)
        values = 100 * np.exp(np.cumsum(returns))
        output[name] = {
            "ending_index": round(float(values[-1]), 4),
            "maximum_drawdown": round(float(np.min(values / np.maximum.accumulate(values) - 1)), 6),
            "realized_volatility": round(float(np.std(returns, ddof=1) * math.sqrt(252)), 6),
        }
    return {"synthetic": True, "seed": seed, "days": days, "regimes": output, "stored_in_user_tables": False}


class AnalyticsService:
    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def indicators(self, user_id: str, instrument: str, dates: list[str], closes: list[float], source: str) -> dict[str, Any]:
        result = indicator_series(dates, closes)
        self._record(user_id, instrument, "indicators", INDICATOR_VERSION, {}, result, source, dates[-1])
        return {**result, "instrument": instrument, "data_source": source, "data_as_of": dates[-1]}

    def forecast(self, user_id: str, instrument: str, dates: list[str], closes: list[float], source: str, window: int) -> dict[str, Any]:
        result = walk_forward_forecast(closes, window)
        self._record(user_id, instrument, "forecast", FORECAST_VERSION, {"window": window}, result, source, dates[-1])
        return {**result, "instrument": instrument, "data_source": source, "data_as_of": dates[-1]}

    def _record(self, user_id: str, instrument: str, model_type: str, version: str, params: dict[str, Any], result: dict[str, Any], source: str, data_as_of: str) -> None:
        self.db.table("analytics_runs").insert(
            {
                "analytics_run_id": str(uuid4()), "user_id": user_id, "instrument": instrument,
                "model_type": model_type, "model_version": version, "params": params,
                "result": {key: value for key, value in result.items() if key != "points"},
                "data_source": source, "data_as_of": data_as_of,
            }
        ).execute()

"""Shared, evidence-bound portfolio risk and optimization calculations."""
from __future__ import annotations

import math
from datetime import date
from typing import Any

import numpy as np
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

from repositories.base import SupabaseRepository

RISK_FREE_RATE = 0.065
MIN_SNAPSHOT_RETURNS = 30
MIN_OPTIMIZATION_RETURNS = 60
OPTIMIZER_VERSION = "long-only-markowitz-ledoit-wolf-1.0.0"


def snapshot_metrics(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate growth and measured risk from dated portfolio snapshots."""
    usable = [
        row for row in snapshots
        if float(row.get("value") or row.get("net_worth") or 0) > 0
        and (row.get("month") or row.get("snapshot_date"))
    ]
    usable.sort(key=lambda row: str(row.get("month") or row.get("snapshot_date")))
    growth = None
    if len(usable) >= 2:
        first = float(usable[0].get("value") or usable[0].get("net_worth"))
        last = float(usable[-1].get("value") or usable[-1].get("net_worth"))
        growth = round((last / first - 1) * 100, 4) if first > 0 else None

    risk: dict[str, Any] = {
        "status": "insufficient_history",
        "level": None,
        "sample_count": max(0, len(usable) - 1),
        "volatility": None,
        "sharpe_ratio": None,
        "cvar_95": None,
        "sample_period": None,
    }
    if len(usable) < 2:
        return {"growth_percent": growth, "risk": risk}

    values = np.asarray([float(row.get("value") or row.get("net_worth")) for row in usable], dtype=float)
    returns = np.diff(values) / values[:-1]
    dates = [date.fromisoformat(str(row.get("month") or row.get("snapshot_date"))[:10]) for row in usable]
    gaps = np.asarray([(current - previous).days for previous, current in zip(dates, dates[1:])], dtype=float)
    median_gap = max(1.0, float(np.median(gaps)))
    periods_per_year = min(365.25, 365.25 / median_gap)
    volatility = float(np.std(returns, ddof=1) * math.sqrt(periods_per_year))
    annual_return = float(np.mean(returns) * periods_per_year)
    downside = np.sort(returns)[: max(1, int(math.ceil(len(returns) * 0.05)))]
    level = "Low" if volatility < 0.10 else "Medium" if volatility < 0.20 else "High"
    risk.update(
        {
            "status": "available",
            "level": level,
            "sample_count": len(returns),
            "volatility": round(volatility, 6),
            "sharpe_ratio": round((annual_return - RISK_FREE_RATE) / volatility, 6) if volatility > 0 else None,
            "cvar_95": round(float(abs(np.mean(downside))), 6),
            "sample_period": {"from": dates[0].isoformat(), "to": dates[-1].isoformat()},
        }
    )
    return {"growth_percent": growth, "risk": risk}


def markowitz_analysis(
    instrument_names: list[str],
    prices: np.ndarray,
    current_weights: dict[str, float],
    benchmark_prices: np.ndarray | None = None,
) -> dict[str, Any]:
    """Long-only maximum-Sharpe optimization over aligned adjusted prices."""
    matrix = np.asarray(prices, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] != len(instrument_names) or len(instrument_names) < 2:
        raise ValueError("At least two aligned instrument price series are required")
    if matrix.shape[0] < MIN_OPTIMIZATION_RETURNS + 1:
        raise ValueError(f"At least {MIN_OPTIMIZATION_RETURNS + 1} aligned prices are required")
    if not np.all(np.isfinite(matrix)) or np.any(matrix <= 0):
        raise ValueError("Aligned prices must be finite and greater than zero")

    returns = np.diff(matrix, axis=0) / matrix[:-1]
    expected = np.mean(returns, axis=0) * 252
    covariance = LedoitWolf().fit(returns).covariance_ * 252
    initial = np.asarray([max(0.0, float(current_weights.get(name, 0))) for name in instrument_names])
    initial = initial / initial.sum() if initial.sum() > 0 else np.full(len(instrument_names), 1 / len(instrument_names))

    def negative_sharpe(weights: np.ndarray) -> float:
        variance = float(weights @ covariance @ weights)
        volatility = math.sqrt(max(variance, 0))
        if volatility <= 1e-12:
            return 1e6
        return -float((weights @ expected - RISK_FREE_RATE) / volatility)

    optimized = minimize(
        negative_sharpe,
        initial,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * len(instrument_names),
        constraints=[{"type": "eq", "fun": lambda weights: float(np.sum(weights) - 1)}],
        options={"maxiter": 1000, "ftol": 1e-10},
    )
    if not optimized.success or not np.all(np.isfinite(optimized.x)):
        raise ValueError(f"Optimization failed: {optimized.message}")
    weights = np.clip(optimized.x, 0, 1)
    weights = weights / weights.sum()
    current_portfolio_returns = returns @ initial
    volatility = float(math.sqrt(max(float(weights @ covariance @ weights), 0)))
    expected_return = float(weights @ expected)

    beta = None
    beta_status = "benchmark_history_unavailable"
    if benchmark_prices is not None:
        benchmark = np.asarray(benchmark_prices, dtype=float)
        if len(benchmark) == matrix.shape[0] and np.all(np.isfinite(benchmark)) and np.all(benchmark > 0):
            benchmark_returns = np.diff(benchmark) / benchmark[:-1]
            benchmark_variance = float(np.var(benchmark_returns, ddof=1))
            if benchmark_variance > 0:
                beta = float(np.cov(current_portfolio_returns, benchmark_returns, ddof=1)[0, 1] / benchmark_variance)
                beta_status = "available"

    target_weights = {name: round(float(weight), 6) for name, weight in zip(instrument_names, weights)}
    suggestions = []
    for name, target in target_weights.items():
        current = float(current_weights.get(name, 0))
        difference = target - current
        if abs(difference) >= 0.05:
            suggestions.append(
                {
                    "instrument": name,
                    "action": "increase" if difference > 0 else "decrease",
                    "current_weight": round(current, 6),
                    "target_weight": target,
                    "difference": round(difference, 6),
                    "reason": "Long-only maximum-Sharpe research allocation differs by at least 5 percentage points.",
                }
            )
    suggestions.sort(key=lambda item: abs(item["difference"]), reverse=True)
    return {
        "status": "available",
        "model_version": OPTIMIZER_VERSION,
        "observations": matrix.shape[0],
        "instruments": instrument_names,
        "optimized_weights": target_weights,
        "expected_annual_return": round(expected_return, 6),
        "expected_annual_volatility": round(volatility, 6),
        "expected_sharpe_ratio": round((expected_return - RISK_FREE_RATE) / volatility, 6) if volatility > 0 else None,
        "portfolio_beta": round(beta, 6) if beta is not None else None,
        "beta_status": beta_status,
        "beta_basis": "current_portfolio_weights",
        "benchmark": "NIFTY 50",
        "rebalancing_suggestions": suggestions,
        "assumptions": [
            "Adjusted price observations are aligned by date.",
            "Weights are long-only, fully invested, and exclude taxes, slippage, and transaction costs.",
            "Expected returns use historical arithmetic means; covariance uses Ledoit-Wolf shrinkage.",
            "Portfolio beta uses current holding weights rather than proposed optimized weights.",
        ],
        "disclaimer": "Educational research output only. Review completeness, taxes, costs, and suitability before acting.",
    }


class PortfolioAnalyticsService:
    HOLDINGS = {
        "equity_holdings": ("Equity", "symbol", "quantity", "current_price", "avg_price"),
        "mutual_fund_holdings": ("Mutual Fund", "scheme_code", "units", "current_nav", "avg_nav"),
        "etf_holdings": ("ETF", "symbol", "quantity", "current_price", "avg_price"),
        "crypto_holdings": ("Crypto", "symbol", "quantity", "current_price", "avg_price"),
    }

    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def analyze(self, user_id: str) -> dict[str, Any]:
        values: dict[str, float] = {}
        for table, (asset_type, key_field, quantity_field, current_field, average_field) in self.HOLDINGS.items():
            for row in self.repo.list_for_user(table, user_id):
                key = str(row.get(key_field) or "").strip()
                if not key:
                    continue
                name = f"{asset_type}:{key}"
                price = float(row.get(current_field) or row.get(average_field) or 0)
                values[name] = values.get(name, 0) + float(row.get(quantity_field) or 0) * price
        if len(values) < 2:
            return self._unavailable("At least two valued holdings are required")
        total = sum(values.values())
        current_weights = {name: value / total for name, value in values.items()} if total > 0 else {}

        try:
            rows = self.repo.list_for_user("market_price_history", user_id, order_by="price_date")
        except Exception as exc:
            return self._unavailable("Market price history migration is not installed", error=type(exc).__name__)
        series: dict[str, dict[str, float]] = {}
        benchmark: dict[str, float] = {}
        for row in rows:
            name = f"{row.get('asset_type')}:{row.get('instrument_key')}"
            target = benchmark if row.get("asset_type") == "Benchmark" else series.setdefault(name, {})
            target[str(row["price_date"])] = float(row["adjusted_close"])
        eligible = [name for name in values if len(series.get(name, {})) >= MIN_OPTIMIZATION_RETURNS + 1]
        if len(eligible) < 2:
            return self._unavailable(
                f"At least two holdings need {MIN_OPTIMIZATION_RETURNS + 1} historical prices",
                current_weights=current_weights,
            )
        common_dates = sorted(set.intersection(*(set(series[name]) for name in eligible)))
        if len(common_dates) < MIN_OPTIMIZATION_RETURNS + 1:
            return self._unavailable(
                f"Only {len(common_dates)} aligned dates are available; {MIN_OPTIMIZATION_RETURNS + 1} are required",
                current_weights=current_weights,
            )
        matrix = np.asarray([[series[name][day] for name in eligible] for day in common_dates], dtype=float)
        benchmark_prices = (
            np.asarray([benchmark[day] for day in common_dates], dtype=float)
            if all(day in benchmark for day in common_dates)
            else None
        )
        eligible_total = sum(values[name] for name in eligible)
        aligned_weights = {name: values[name] / eligible_total for name in eligible}
        try:
            return markowitz_analysis(eligible, matrix, aligned_weights, benchmark_prices)
        except ValueError as exc:
            return self._unavailable(str(exc), current_weights=current_weights)

    @staticmethod
    def _unavailable(reason: str, **extra: Any) -> dict[str, Any]:
        return {
            "status": "insufficient_data",
            "reason": reason,
            "model_version": OPTIMIZER_VERSION,
            "portfolio_beta": None,
            "beta_status": "insufficient_data",
            "optimized_weights": {},
            "rebalancing_suggestions": [],
            **extra,
        }

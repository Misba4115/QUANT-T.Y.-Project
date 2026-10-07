"""Bounded, long-only mean/variance research using recorded INR prices.

Objective: maximize mu @ w - gamma / 2 * w @ covariance @ w.
https://www.cvxpy.org/examples/basic/quadratic_program.html
At most seven representative series and 253 prices each; no network pricing/AI.
"""
from datetime import date
import numpy as np
from scipy.optimize import minimize


def analyze(db, user_id, proxies, risk_profile):
    unavailable = {key: {"status": "unavailable", "reason": "Need 61 recent, aligned INR prices for at least two category proxies."} for key in proxies}
    series = {}
    for key, (asset_type, instrument) in proxies.items():
        rows = db.table("market_price_history").select("price_date,adjusted_close,provider,fetched_at").eq(
            "user_id", user_id).eq("asset_type", asset_type).eq("instrument_key", instrument).eq(
            "currency", "INR").order("price_date", desc=True).limit(800).execute().data or []
        # Keep providers separate: mixing feeds introduces artificial returns.
        providers = {}
        for row in sorted(rows, key=lambda r: str(r.get("fetched_at", ""))):
            try:
                price = float(row["adjusted_close"])
                day = date.fromisoformat(str(row["price_date"])[:10])
            except (ValueError, TypeError, KeyError):
                continue
            if np.isfinite(price) and price > 0 and day <= date.today():
                providers.setdefault(str(row.get("provider", "unknown")), {})[day] = price
        if not providers:
            continue
        provider, prices = max(providers.items(), key=lambda pair: (max(pair[1]), len(pair[1]), pair[0]))
        days = sorted(prices)[-253:]
        if len(days) >= 61 and (date.today() - days[-1]).days <= 14:
            series[key] = ({day: prices[day] for day in days}, provider)
    if len(series) < 2:
        return unavailable
    keys = sorted(series)
    days = sorted(set.intersection(*(set(series[key][0]) for key in keys)))
    if len(days) < 61:
        return unavailable
    gaps = np.asarray([(b - a).days for a, b in zip(days, days[1:])])
    if max(gaps) > 7:
        return unavailable
    prices = np.asarray([[series[key][0][day] for key in keys] for day in days])
    returns = np.diff(prices, axis=0) / prices[:-1]
    annualization = 365.25 / float(np.mean(gaps))
    means = returns.mean(axis=0) * annualization
    sample = np.atleast_2d(np.cov(returns, rowvar=False, ddof=1)) * annualization
    # Fixed diagonal shrinkage regularizes highly correlated category proxies.
    covariance = .9 * sample + .1 * np.diag(np.diag(sample))
    gamma = {"conservative": 8, "moderate": 4, "aggressive": 2}.get(risk_profile, 4)
    fit = minimize(lambda w: float(gamma / 2 * w @ covariance @ w - means @ w),
                   np.full(len(keys), 1 / len(keys)), method="SLSQP",
                   jac=lambda w: gamma * covariance @ w - means,
                   bounds=[(0, 1)] * len(keys),
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                   options={"maxiter": 100, "ftol": 1e-9})
    if not fit.success or not np.all(np.isfinite(fit.x)) or abs(fit.x.sum() - 1) > 1e-5:
        return unavailable
    for i, key in enumerate(keys):
        # Downsample the aligned, normalized proxy path for a small detail chart.
        chart_indexes = sorted({round(j * (len(days) - 1) / 39) for j in range(40)})
        history = [{"date": days[j].isoformat(), "index": round(float(prices[j, i] / prices[0, i] * 100), 2)}
                   for j in chart_indexes]
        unavailable[key] = dict(status="available", mean_pct=round(float(means[i] * 100), 2),
                                volatility_pct=round(float(np.sqrt(covariance[i, i]) * 100), 2),
                                weight_pct=round(float(fit.x[i] * 100), 2), observations=len(days) - 1,
                                history=history,
                                proxy=proxies[key][1], provider=series[key][1], as_of=days[-1].isoformat(),
                                reason="Historical category proxy, not an individual product forecast. Weights cover eligible proxies only; fees and taxes excluded.")
    return unavailable

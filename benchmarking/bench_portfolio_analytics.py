"""
Benchmark: Portfolio Analytics Engine vs PyPortfolioOpt
=========================================================

Compares:
  1. QUANT Portfolio Analytics Engine
  2. PyPortfolioOpt reference implementation

The same simulated price history is supplied to both engines.

Run from repo root:
    python benchmarking/bench_portfolio_analytics.py
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from services.portfolio_analytics import (  # noqa: E402
    markowitz_analysis,
    RISK_FREE_RATE,
)

# ---------------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------------

TEST_SET_PATH = Path(__file__).parent / "portfolio_analytics_test_set.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_PATH = RESULTS_DIR / "portfolio_analytics_results.json"

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

SIM_OBSERVATIONS = 120
RANDOM_SEED = 42
SHARPE_TOLERANCE = 0.01


# ---------------------------------------------------------------------------
# SIMULATE PRICE DATA
# ---------------------------------------------------------------------------

def simulate_prices(
    tickers: list[str],
    expected_returns: list[float],
    volatilities: list[float],
    corr_matrix: list[list[float]],
    n_obs: int,
    seed: int = RANDOM_SEED,
) -> np.ndarray:

    rng = np.random.default_rng(seed)

    n = len(tickers)

    corr = np.asarray(corr_matrix, dtype=float)
    vols = np.asarray(volatilities, dtype=float)
    mus = np.asarray(expected_returns, dtype=float)

    dt = 1 / 252

    # Validate dimensions
    if corr.shape != (n, n):
        raise ValueError(
            f"Correlation matrix shape {corr.shape} "
            f"does not match {n} assets."
        )

    if len(vols) != n:
        raise ValueError("Volatility count does not match ticker count.")

    if len(mus) != n:
        raise ValueError("Expected return count does not match ticker count.")

    # Covariance matrix
    cov = corr * np.outer(vols, vols)

    # Cholesky decomposition
    try:
        L = np.linalg.cholesky(cov * dt)
    except np.linalg.LinAlgError:
        print("WARNING: Correlation matrix not positive definite.")
        print("Adding small diagonal jitter.")

        cov_jitter = cov + np.eye(n) * 1e-8
        L = np.linalg.cholesky(cov_jitter * dt)

    # Generate prices
    prices = np.ones((n_obs + 1, n)) * 100.0

    z = rng.standard_normal((n_obs, n))

    for t in range(n_obs):
        eps = z[t] @ L.T

        log_returns = (
            (mus - 0.5 * vols**2) * dt
            + eps
        )

        prices[t + 1] = prices[t] * np.exp(log_returns)

    return prices


# ---------------------------------------------------------------------------
# PYPORTFOLIOOPT
# ---------------------------------------------------------------------------

def run_pyportfolioopt(
    tickers: list[str],
    expected_returns: list[float],
    volatilities: list[float],
    corr_matrix: list[list[float]],
    prices: np.ndarray,
    risk_free_rate: float,
) -> dict:

    # -----------------------------------------------------------------------
    # Import
    # -----------------------------------------------------------------------

    try:
        import pandas as pd

        from pypfopt import EfficientFrontier
        from pypfopt.expected_returns import mean_historical_return
        from pypfopt.risk_models import CovarianceShrinkage

    except Exception as exc:

        error = (
            f"IMPORT ERROR: {type(exc).__name__}: {exc}"
        )

        print(f"\n[PPO ERROR] {error}")

        return {
            "error": error,
            "weights": {},
            "sharpe_ratio": None,
        }

    # -----------------------------------------------------------------------
    # Create DataFrame
    # -----------------------------------------------------------------------

    try:
        df = pd.DataFrame(
            prices,
            columns=tickers,
        )

        if df.isnull().any().any():
            raise ValueError("Price dataframe contains NaN values.")

        if not np.isfinite(df.values).all():
            raise ValueError("Price dataframe contains infinite values.")

    except Exception as exc:

        error = (
            f"DATAFRAME ERROR: {type(exc).__name__}: {exc}"
        )

        print(f"\n[PPO ERROR] {error}")

        return {
            "error": error,
            "weights": {},
            "sharpe_ratio": None,
        }

    # -----------------------------------------------------------------------
    # Expected returns
    # -----------------------------------------------------------------------

    try:
        mu = mean_historical_return(
            df,
            compounding=False,
        )

    except Exception as exc:

        error = (
            f"EXPECTED RETURN ERROR: {type(exc).__name__}: {exc}"
        )

        print(f"\n[PPO ERROR] {error}")
        traceback.print_exc()

        return {
            "error": error,
            "weights": {},
            "sharpe_ratio": None,
        }

    # -----------------------------------------------------------------------
    # Covariance matrix
    # -----------------------------------------------------------------------

    try:
        S = CovarianceShrinkage(df).ledoit_wolf()

    except Exception as exc:

        error = (
            f"COVARIANCE ERROR: {type(exc).__name__}: {exc}"
        )

        print(f"\n[PPO ERROR] {error}")
        traceback.print_exc()

        return {
            "error": error,
            "weights": {},
            "sharpe_ratio": None,
        }

    # -----------------------------------------------------------------------
    # Efficient Frontier
    # -----------------------------------------------------------------------

    try:
        ef = EfficientFrontier(mu, S)

        ef.max_sharpe(
            risk_free_rate=risk_free_rate
        )

        cleaned = ef.clean_weights()

        perf = ef.portfolio_performance(
            risk_free_rate=risk_free_rate,
            verbose=False,
        )

    except Exception as exc:

        error = (
            f"OPTIMIZATION ERROR: {type(exc).__name__}: {exc}"
        )

        print(f"\n[PPO ERROR] {error}")
        traceback.print_exc()

        return {
            "error": error,
            "weights": {},
            "sharpe_ratio": None,
        }

    # -----------------------------------------------------------------------
    # Return result
    # -----------------------------------------------------------------------

    return {
        "weights": {
            ticker: float(weight)
            for ticker, weight in cleaned.items()
        },
        "expected_annual_return": float(perf[0]),
        "expected_annual_volatility": float(perf[1]),
        "sharpe_ratio": float(perf[2]),
    }


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:

    print("=" * 60)
    print("BENCHMARK: Portfolio Analytics Engine vs PyPortfolioOpt")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # Check PyPortfolioOpt before running benchmark
    # -----------------------------------------------------------------------

    print("\nChecking PyPortfolioOpt installation...")

    try:
        import pypfopt

        print(
            f"PyPortfolioOpt found: {getattr(pypfopt, '__version__', 'version unknown')}"
        )

    except Exception as exc:

        print("\n❌ PyPortfolioOpt cannot be imported.")
        print(f"Error: {type(exc).__name__}: {exc}")
        print("\nRun:")
        print("    python -m pip install PyPortfolioOpt")
        print("\nThen verify with:")
        print("    python -c \"import pypfopt; print(pypfopt.__version__)\"")

        return

    # -----------------------------------------------------------------------
    # Load test set
    # -----------------------------------------------------------------------

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = json.load(f)

    portfolios = test_set["portfolios"]

    print(f"\nLoaded {len(portfolios)} portfolios.\n")

    # -----------------------------------------------------------------------
    # Counters
    # -----------------------------------------------------------------------

    results = []

    passed = 0
    failed = 0
    errored = 0

    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------

    print(
        f"{'ID':<8}"
        f"{'Engine Sharpe':>14}"
        f"{'PPO Sharpe':>12}"
        f"{'Diff':>8}"
        f"{'Wt Dev':>8}"
        f"{'Pass?':>8}"
    )

    print("-" * 65)

    # -----------------------------------------------------------------------
    # Run portfolios
    # -----------------------------------------------------------------------

    for portfolio in portfolios:

        pid = portfolio["portfolio_id"]

        tickers = [
            asset["ticker"]
            for asset in portfolio["assets"]
        ]

        exp_returns = [
            asset["expected_annual_return"]
            for asset in portfolio["assets"]
        ]

        vols = [
            asset["annual_volatility"]
            for asset in portfolio["assets"]
        ]

        corr = portfolio["correlation_matrix"]

        rfr = portfolio.get(
            "risk_free_rate",
            RISK_FREE_RATE,
        )

        # ---------------------------------------------------------------
        # Simulate prices
        # ---------------------------------------------------------------

        try:

            prices = simulate_prices(
                tickers,
                exp_returns,
                vols,
                corr,
                SIM_OBSERVATIONS,
            )

        except Exception as exc:

            print(
                f"{pid:<8} PRICE SIMULATION ERROR: "
                f"{type(exc).__name__}: {exc}"
            )

            errored += 1

            results.append({
                "portfolio_id": pid,
                "status": "ERROR",
                "error": str(exc),
            })

            continue

        # ---------------------------------------------------------------
        # Starting weights
        # ---------------------------------------------------------------

        n = len(tickers)

        current_weights = {
            ticker: 1.0 / n
            for ticker in tickers
        }

        # ---------------------------------------------------------------
        # YOUR ENGINE
        # ---------------------------------------------------------------

        engine_result = {}
        engine_error = None

        try:

            engine_result = markowitz_analysis(
                tickers,
                prices,
                current_weights,
                benchmark_prices=None,
            )

        except Exception as exc:

            engine_error = (
                f"{type(exc).__name__}: {exc}"
            )

            print(
                f"\n[{pid}] ENGINE ERROR: "
                f"{engine_error}"
            )

        # ---------------------------------------------------------------
        # PYPORTFOLIOOPT
        # ---------------------------------------------------------------

        ppo_result = run_pyportfolioopt(
            tickers,
            exp_returns,
            vols,
            corr,
            prices,
            rfr,
        )

        # ---------------------------------------------------------------
        # Extract results
        # ---------------------------------------------------------------

        engine_sharpe = (
            engine_result.get("expected_sharpe_ratio")
            if not engine_error
            else None
        )

        ppo_sharpe = ppo_result.get(
            "sharpe_ratio"
        )

        # ---------------------------------------------------------------
        # Sharpe difference
        # ---------------------------------------------------------------

        if (
            engine_sharpe is not None
            and ppo_sharpe is not None
        ):

            sharpe_diff = abs(
                float(engine_sharpe)
                - float(ppo_sharpe)
            )

        else:

            sharpe_diff = None

        # ---------------------------------------------------------------
        # Weight comparison
        # ---------------------------------------------------------------

        engine_weights = engine_result.get(
            "optimized_weights",
            {},
        )

        ppo_weights = ppo_result.get(
            "weights",
            {},
        )

        weight_devs = [
            abs(
                float(engine_weights.get(ticker, 0))
                - float(ppo_weights.get(ticker, 0))
            )
            for ticker in tickers
        ]

        mean_weight_dev = (
            round(
                sum(weight_devs)
                / len(weight_devs),
                4,
            )
            if weight_devs
            else None
        )

        # ---------------------------------------------------------------
        # PASS / FAIL / ERROR
        # ---------------------------------------------------------------

        if engine_error or "error" in ppo_result:

            status = "ERROR"
            errored += 1

        elif (
            sharpe_diff is not None
            and sharpe_diff <= SHARPE_TOLERANCE
        ):

            status = "PASS"
            passed += 1

        else:

            status = "FAIL"
            failed += 1

        # ---------------------------------------------------------------
        # Display
        # ---------------------------------------------------------------

        es_str = (
            f"{engine_sharpe:.4f}"
            if engine_sharpe is not None
            else "ERR"
        )

        ps_str = (
            f"{ppo_sharpe:.4f}"
            if ppo_sharpe is not None
            else "ERR"
        )

        sd_str = (
            f"{sharpe_diff:.4f}"
            if sharpe_diff is not None
            else "N/A"
        )

        wd_str = (
            f"{mean_weight_dev:.4f}"
            if mean_weight_dev is not None
            else "N/A"
        )

        print(
            f"{pid:<8}"
            f"{es_str:>14}"
            f"{ps_str:>12}"
            f"{sd_str:>8}"
            f"{wd_str:>8}"
            f"{status:>8}"
        )

        # ---------------------------------------------------------------
        # Save result
        # ---------------------------------------------------------------

        results.append({
            "portfolio_id": pid,
            "description": portfolio.get("description"),
            "tickers": tickers,
            "risk_free_rate": rfr,

            "engine_result": (
                engine_result
                if not engine_error
                else {"error": engine_error}
            ),

            "pyportfolioopt_result": ppo_result,

            "engine_sharpe": engine_sharpe,
            "ppo_sharpe": ppo_sharpe,
            "sharpe_diff": sharpe_diff,

            "mean_weight_deviation": mean_weight_dev,

            "per_ticker_weight_deviation": {
                ticker: dev
                for ticker, dev in zip(
                    tickers,
                    weight_devs,
                )
            },

            "status": status,
        })

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    total = len(portfolios)

    print("\n" + "=" * 60)

    print(
        f"Summary: "
        f"{passed}/{total} PASS, "
        f"{failed}/{total} FAIL, "
        f"{errored}/{total} ERROR"
    )

    print(
        f"Sharpe tolerance: {SHARPE_TOLERANCE}"
    )

    print(
        f"Sim observations: {SIM_OBSERVATIONS}"
    )

    # -----------------------------------------------------------------------
    # Write JSON
    # -----------------------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "component": "portfolio_analytics",
        "total": total,
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "sharpe_tolerance": SHARPE_TOLERANCE,
        "sim_observations": SIM_OBSERVATIONS,
        "risk_free_rate": RISK_FREE_RATE,
        "portfolios": results,
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"\nResults written to: {RESULTS_PATH}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
    
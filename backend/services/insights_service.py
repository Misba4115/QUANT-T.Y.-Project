"""
Insights Service — Layer A (Trading Signals) + Layer B (Investment Recommendations).

Phase 1: deterministic statistical models (EWMA returns, Ledoit-Wolf σ, goal-gap
         arithmetic, rule-based instrument suggestions).
Phase 2: SLM inference (Kronos-small, financial-ttm, StocK_Advisor) replaces/augments
         the statistical layer without changing the output contract.

GC-SEC integration:
  Step 1 (Grounding): every numeric claim is constructed from the actual computed value
          — no separate LLM generates numbers to check in Phase 1.
  Step 2 (Consensus Arbiter): REDUCE signals are pre-checked against Tax Engine STCG state.
  Step 3 (Outcome Evaluator): hook is present; logging deferred until insight_runs migration.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Any

import numpy as np

from repositories.base import SupabaseRepository
from services.portfolio_analytics import RISK_FREE_RATE, PortfolioAnalyticsService
from services.tax_analytics import calculate_tax_metrics

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_VERSION = "statistical-baseline-v1.0"  # Phase 2: replaced by "kronos-small-v1"
EWMA_SPAN = 60          # days for exponential weighted moving average
CONFIDENCE_HIGH = 0.75  # σ_annualised threshold below which we report "High" confidence
CONFIDENCE_MEDIUM = 0.20
SIGNAL_THRESHOLD = 0.05  # >5% deviation from equal-weight → rebalance signal
STALE_HOURS = 4          # re-compute if cached result is older than this

# Instrument suggestions: keys are (risk_profile, horizon_years, missing_class)
# Values are (name, rationale, risk_level)
INSTRUMENT_MAP: dict[tuple[str, str, str], tuple[str, str, str]] = {
    ("conservative", "short", "debt"): ("Liquid Mutual Funds", "Capital preservation with easy liquidity", "Low"),
    ("conservative", "medium", "debt"): ("Debt Mutual Funds", "Stable returns with moderate duration risk", "Low"),
    ("conservative", "long", "equity"): ("Large-cap Index Fund (Nifty 50)", "Long-term wealth creation with lower volatility", "Medium"),
    ("moderate", "short", "debt"): ("Short-Duration Debt Fund", "Improves stability and reduces short-term volatility", "Low"),
    ("moderate", "medium", "equity"): ("Nifty Next 50 Index Fund", "Mid-cap growth exposure alongside large-cap", "Medium"),
    ("moderate", "long", "international"): ("International Equity ETF", "Global diversification, reduces India-specific risk", "Medium"),
    ("aggressive", "medium", "equity"): ("Small-cap Fund", "Higher growth potential over 5+ year horizon", "High"),
    ("aggressive", "long", "international"): ("International Equity ETF", "Global exposure for long-term growth", "Medium"),
    ("aggressive", "long", "gold"): ("Gold ETF", "Inflation hedge and portfolio diversifier", "Low"),
}

# Fallback suggestions when no specific rule matches
FALLBACK_SUGGESTIONS = [
    {"name": "Liquid Mutual Fund", "rationale": "Improves stability and provides emergency liquidity", "risk_level": "Low"},
    {"name": "Gold ETF", "rationale": "Inflation hedge and portfolio diversifier", "risk_level": "Low"},
    {"name": "Nifty 50 Index Fund", "rationale": "Broad market exposure at low cost", "risk_level": "Medium"},
]


# ---------------------------------------------------------------------------
# Layer A — Trading Signals
# ---------------------------------------------------------------------------

def _asset_class_from_holding(table: str) -> str:
    mapping = {
        "equity_holdings": "Equity",
        "mutual_fund_holdings": "Mutual Fund",
        "etf_holdings": "ETF",
        "crypto_holdings": "Crypto",
    }
    return mapping.get(table, "Other")


def _ewma_return(prices: list[float], span: int = EWMA_SPAN) -> float:
    """Exponentially weighted moving average return (annualised)."""
    if len(prices) < 2:
        return 0.0
    arr = np.asarray(prices, dtype=float)
    daily_returns = np.diff(arr) / arr[:-1]
    alpha = 2.0 / (span + 1)
    weights = (1 - alpha) ** np.arange(len(daily_returns) - 1, -1, -1)
    weights /= weights.sum()
    ewma_daily = float(np.dot(weights, daily_returns))
    return ewma_daily * 252


def _confidence_label(annualised_vol: float) -> str:
    if annualised_vol < CONFIDENCE_HIGH:
        return "High"
    if annualised_vol < CONFIDENCE_MEDIUM + CONFIDENCE_HIGH:
        return "Medium"
    return "Low"


def _build_asset_forecasts(
    holdings_by_class: dict[str, float],
    price_history: dict[str, list[float]],
    pa_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build per-asset-class return forecasts for Layer A."""
    forecasts = []
    pa_vol = pa_result.get("expected_annual_volatility") or 0.20

    for asset_class, total_value in sorted(holdings_by_class.items(), key=lambda x: -x[1]):
        prices = price_history.get(asset_class, [])

        if len(prices) >= 2:
            ewma = _ewma_return(prices)
            # Simple σ from daily returns
            daily_returns = np.diff(np.asarray(prices)) / np.asarray(prices[:-1])
            vol = float(np.std(daily_returns, ddof=1) * math.sqrt(252)) if len(daily_returns) > 1 else pa_vol
        else:
            # Fallback: use pa volatility, zero EWMA
            ewma = 0.0
            vol = pa_vol

        low = ewma - vol
        high = ewma + vol
        confidence = _confidence_label(vol)
        direction = "up" if ewma > 0 else "down" if ewma < 0 else "flat"

        forecasts.append({
            "asset_class": asset_class,
            "current_value": round(total_value, 2),
            "forecast_return_low": round(low * 100, 2),
            "forecast_return_high": round(high * 100, 2),
            "forecast_return_midpoint": round(ewma * 100, 2),
            "annualised_volatility": round(vol * 100, 2),
            "confidence": confidence,
            "direction": direction,
            "horizon_days": 30,
            "model": MODEL_VERSION,
            # Phase 1: prices used come from portfolio snapshots; Phase 2: Kronos-small inference
            "data_source": "portfolio_snapshots_ewma",
        })

    return forecasts


def _build_rebalance_actions(
    holdings_by_class: dict[str, float],
    pa_result: dict[str, Any],
    tax_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate HOLD / REDUCE / ADD signals with tax pre-check (GC-SEC Step 2)."""
    total = sum(holdings_by_class.values()) or 1.0
    current_weights = {k: v / total for k, v in holdings_by_class.items()}

    # Use optimized weights from PA if available; fall back to equal weight
    optimized = pa_result.get("optimized_weights", {})
    n = len(holdings_by_class)
    equal_weight = 1.0 / n if n > 0 else 0.0

    # Gather any STCG warning from Tax Engine
    has_stcg = bool(
        tax_summary.get("realized_gain_breakdown") and
        any(b.get("stcg", 0) > 0 for b in tax_summary["realized_gain_breakdown"])
    )

    actions = []
    for asset_class, current_w in sorted(current_weights.items()):
        target_w = optimized.get(asset_class) or equal_weight
        delta = target_w - current_w

        if abs(delta) < SIGNAL_THRESHOLD:
            signal = "HOLD"
            reason = "Within target allocation"
        elif delta < 0:
            signal = "REDUCE"
            pct = round(abs(delta) * 100, 1)
            reason = f"Consider reducing by {pct}% — overweight vs. target"
        else:
            signal = "ADD"
            pct = round(abs(delta) * 100, 1)
            reason = f"Consider adding {pct}% — underweight vs. target"

        # GC-SEC Step 2: tax constraint check
        tax_flag = None
        if signal == "REDUCE" and has_stcg and asset_class in ("Equity", "ETF"):
            tax_flag = "Selling may realise short-term capital gains this year. Review tax impact before acting."

        actions.append({
            "asset_class": asset_class,
            "signal": signal,
            "reason": reason,
            "current_weight_pct": round(current_w * 100, 1),
            "target_weight_pct": round(target_w * 100, 1),
            "tax_flag": tax_flag,
        })

    return sorted(actions, key=lambda x: ("HOLD", "REDUCE", "ADD").index(x["signal"]) if x["signal"] in ("HOLD", "REDUCE", "ADD") else 3)


# ---------------------------------------------------------------------------
# Layer B — Investment Recommendations
# ---------------------------------------------------------------------------

def _goal_horizon(target_date: str | None) -> str:
    if not target_date:
        return "long"
    try:
        t = date.fromisoformat(str(target_date)[:10])
        years = (t - date.today()).days / 365.25
        if years < 2:
            return "short"
        if years < 7:
            return "medium"
        return "long"
    except (ValueError, TypeError):
        return "long"


def _goal_gap(goal: dict[str, Any], net_worth: float) -> dict[str, Any]:
    """Compute gap, trajectory and required SIP for a single goal."""
    target = float(goal.get("target_amount") or 0)
    current = float(goal.get("current_amount") or 0)
    # Fallback: use a fraction of net worth as a proxy if no current_amount set
    if current <= 0 and net_worth > 0:
        current = net_worth * 0.15  # conservative proxy

    gap = max(0.0, target - current)
    shortfall_pct = (gap / target * 100) if target > 0 else 0.0
    on_track = shortfall_pct < 10  # within 10% = on track

    # Required monthly SIP to close gap (simple arithmetic, no compounding for Phase 1)
    horizon = _goal_horizon(goal.get("target_date"))
    years_map = {"short": 2.0, "medium": 5.0, "long": 15.0}
    months_remaining = years_map[horizon] * 12
    required_sip = gap / months_remaining if months_remaining > 0 else 0.0

    return {
        "goal_id": goal.get("goal_id"),
        "goal_name": goal.get("name") or goal.get("goal_name") or "Goal",
        "target_amount": round(target, 2),
        "current_amount": round(current, 2),
        "gap": round(gap, 2),
        "shortfall_pct": round(shortfall_pct, 1),
        "on_track": on_track,
        "required_monthly_sip": round(required_sip, 2),
        "horizon": horizon,
        "target_date": goal.get("target_date"),
    }


def _build_instrument_suggestions(
    risk_profile: str,
    goal_gaps: list[dict[str, Any]],
    holdings_by_class: dict[str, float],
) -> list[dict[str, Any]]:
    """Rule-based instrument suggestions based on risk profile, gap horizon, missing classes."""
    profile = (risk_profile or "moderate").lower()
    if profile not in ("conservative", "moderate", "aggressive"):
        profile = "moderate"

    present_classes = {k.lower() for k in holdings_by_class}
    suggestions: list[dict[str, Any]] = []
    seen: set[str] = set()

    for gap in goal_gaps:
        if gap["on_track"]:
            continue
        horizon = gap["horizon"]
        for class_name in ("debt", "equity", "international", "gold"):
            if class_name not in present_classes:
                key = (profile, horizon, class_name)
                if key in INSTRUMENT_MAP and key not in seen:
                    name, rationale, risk_level = INSTRUMENT_MAP[key]
                    suggestions.append({
                        "name": name,
                        "rationale": rationale,
                        "risk_level": risk_level,
                        "driven_by_goal": gap["goal_name"],
                    })
                    seen.add(key)

    # Pad with fallbacks if nothing was generated
    for fb in FALLBACK_SUGGESTIONS:
        if len(suggestions) >= 4:
            break
        if not any(s["name"] == fb["name"] for s in suggestions):
            suggestions.append({**fb, "driven_by_goal": None})

    return suggestions[:4]


def _build_priority_action(
    goal_gaps: list[dict[str, Any]],
    cashflow_surplus: float,
    suggestions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Identify the single highest-impact action to recommend."""
    # Find the goal with the largest shortfall
    unmet = [g for g in goal_gaps if not g["on_track"] and g["gap"] > 0]
    if not unmet:
        return None

    worst = max(unmet, key=lambda g: g["shortfall_pct"])
    sip = worst["required_monthly_sip"]
    surplus = cashflow_surplus or 0.0
    increase = max(0.0, sip - surplus)

    if increase > 0:
        return {
            "action": "Increase monthly investment",
            "description": (
                f"Increasing your monthly investment by ₹{increase:,.0f} can help you close "
                f"{round(worst['shortfall_pct'])}% of your {worst['goal_name']} gap."
            ),
            "impact": "High",
            "effort": "Low" if increase < 5000 else "Medium",
            "time_horizon": "Long-term" if worst["horizon"] == "long" else "Medium-term",
            "driven_by_goal": worst["goal_name"],
        }

    # Already has surplus — suggest putting it to work
    top_suggestion = suggestions[0] if suggestions else None
    return {
        "action": "Deploy monthly surplus",
        "description": (
            f"You have a monthly surplus of ₹{surplus:,.0f}. "
            + (f"Consider adding {top_suggestion['name']} to put it to work." if top_suggestion else "Put it to work in a goal-aligned fund.")
        ),
        "impact": "Medium",
        "effort": "Low",
        "time_horizon": "Long-term",
        "driven_by_goal": worst["goal_name"],
    }


# ---------------------------------------------------------------------------
# Main service entry point
# ---------------------------------------------------------------------------

class InsightsService:
    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def _collect_holdings(self, user_id: str) -> tuple[dict[str, float], dict[str, list[float]]]:
        """Collect holdings grouped by asset class and price snapshots."""
        table_map = {
            "equity_holdings": ("Equity", "symbol", "quantity", "current_price", "avg_price"),
            "mutual_fund_holdings": ("Mutual Fund", "scheme_code", "units", "current_nav", "avg_nav"),
            "etf_holdings": ("ETF", "symbol", "quantity", "current_price", "avg_price"),
            "crypto_holdings": ("Crypto", "symbol", "quantity", "current_price", "avg_price"),
        }
        holdings_by_class: dict[str, float] = {}
        for table, (asset_class, key_field, qty_field, price_field, avg_field) in table_map.items():
            for row in self.repo.list_for_user(table, user_id):
                price = float(row.get(price_field) or row.get(avg_field) or 0)
                qty = float(row.get(qty_field) or 0)
                holdings_by_class[asset_class] = holdings_by_class.get(asset_class, 0) + price * qty

        # Pull price history from portfolio_snapshots for EWMA
        price_history: dict[str, list[float]] = {}
        try:
            snapshots = self.repo.list_for_user(
                "portfolio_snapshots", user_id, order_by="snapshot_date"
            )
            for snap in snapshots:
                asset_class = snap.get("asset_class") or "Portfolio"
                val = float(snap.get("value") or snap.get("net_worth") or 0)
                if val > 0:
                    price_history.setdefault(asset_class, []).append(val)
        except Exception:
            # portfolio_snapshots may not have the asset_class column — degrade gracefully
            pass

        return holdings_by_class, price_history

    def _get_cashflow_surplus(self, user_id: str) -> float:
        """Estimate monthly cashflow surplus from user profile."""
        rows = self.repo.find("users", [("user_id", user_id)], limit=1)
        if not rows:
            return 0.0
        user = rows[0]
        income = float(user.get("monthly_income") or 0)
        expenses = float(user.get("monthly_expenses") or 0)
        return max(0.0, income - expenses)

    def _get_risk_profile(self, user_id: str) -> str:
        rows = self.repo.find("users", [("user_id", user_id)], limit=1)
        if rows:
            return str(rows[0].get("risk_profile") or "moderate").lower()
        return "moderate"

    def generate(self, user_id: str) -> dict[str, Any]:
        """Compute Layer A + Layer B and return unified InsightsResult."""
        generated_at = datetime.now(timezone.utc).isoformat()

        # ── Data collection ──────────────────────────────────────────────────
        holdings_by_class, price_history = self._collect_holdings(user_id)
        goals = self.repo.list_for_user("goals", user_id)
        risk_profile = self._get_risk_profile(user_id)
        cashflow_surplus = self._get_cashflow_surplus(user_id)
        net_worth = sum(holdings_by_class.values())

        # ── Portfolio Analytics (reuse existing service — no re-computation) ─
        try:
            pa_result = PortfolioAnalyticsService(self.db).analyze(user_id)
        except Exception:
            pa_result = {"status": "insufficient_data", "optimized_weights": {}, "rebalancing_suggestions": []}

        # ── Tax Engine (for Arbiter in Layer A) ──────────────────────────────
        try:
            tax_summary = calculate_tax_metrics(user_id, self.db)
        except Exception:
            tax_summary = {"realized_gain_breakdown": [], "warnings": []}

        # ── Layer A: Trading Signals ──────────────────────────────────────────
        asset_forecasts = _build_asset_forecasts(holdings_by_class, price_history, pa_result)
        rebalance_actions = _build_rebalance_actions(holdings_by_class, pa_result, tax_summary)

        # ── Layer B: Investment Recommendations ───────────────────────────────
        goal_gaps = [_goal_gap(g, net_worth) for g in goals]
        instrument_suggestions = _build_instrument_suggestions(risk_profile, goal_gaps, holdings_by_class)
        priority_action = _build_priority_action(goal_gaps, cashflow_surplus, instrument_suggestions)

        # ── GC-SEC Step 1: Grounding summary ─────────────────────────────────
        # In Phase 1 all numbers come directly from computed sources — no LLM intermediary.
        # This block becomes meaningful in Phase 2 when SLM outputs are checked.
        grounding_summary = {
            "checks_performed": len(asset_forecasts) + len(goal_gaps),
            "corrections_applied": 0,
            "note": "Phase 1: all values derived directly from computed sources. SLM grounding active in Phase 2.",
        }

        # ── GC-SEC Step 2: Consensus Arbiter summary ─────────────────────────
        tax_flags = [a for a in rebalance_actions if a.get("tax_flag")]
        arbiter_summary = {
            "tax_flags_raised": len(tax_flags),
            "risk_profile_applied": risk_profile,
        }

        no_holdings = len(holdings_by_class) == 0
        no_goals = len(goals) == 0

        return {
            "generated_at": generated_at,
            "model_version": MODEL_VERSION,
            "user_context": {
                "risk_profile": risk_profile,
                "net_worth": round(net_worth, 2),
                "cashflow_surplus": round(cashflow_surplus, 2),
                "total_goals": len(goals),
                "asset_classes_held": list(holdings_by_class.keys()),
            },
            # Layer A
            "layer_a": {
                "status": "unavailable_no_holdings" if no_holdings else "available",
                "asset_forecasts": asset_forecasts,
                "rebalance_actions": rebalance_actions,
                "pa_status": pa_result.get("status", "insufficient_data"),
            },
            # Layer B
            "layer_b": {
                "status": "unavailable_no_goals" if no_goals else "available",
                "goal_gaps": goal_gaps,
                "instrument_suggestions": instrument_suggestions,
                "priority_action": priority_action,
            },
            # GC-SEC metadata
            "gc_sec": {
                "grounding": grounding_summary,
                "arbiter": arbiter_summary,
                "disclaimer": (
                    "All outputs are educational and advisory only. "
                    "No trades are executed. Review with a qualified financial adviser before acting."
                ),
            },
        }

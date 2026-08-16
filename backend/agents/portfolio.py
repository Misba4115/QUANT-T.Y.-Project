"""Portfolio agent over shared dashboard and optimization analytics."""
from __future__ import annotations

from typing import Any

from services.dashboard_aggregator import DashboardAggregator
from services.portfolio_analytics import PortfolioAnalyticsService


def run_portfolio_agent(user_id: str, db: Any) -> dict:
    dashboard = DashboardAggregator(db).aggregate(user_id, "1y")
    optimization = PortfolioAnalyticsService(db).analyze(user_id)
    measured = dashboard["measured_portfolio_risk"]
    analytics = {
        "status": measured["status"],
        "sample_count": measured["sample_count"],
        "annualized_volatility": measured["volatility"],
        "sharpe_ratio": measured.get("sharpe_ratio"),
        "cvar_95": measured.get("cvar_95"),
        "portfolio_beta": optimization.get("portfolio_beta"),
        "beta_status": optimization.get("beta_status"),
    }
    return {
        "agent": "portfolio",
        "status": "available" if dashboard["top_holdings"] else "no_holdings",
        "net_worth": dashboard["net_worth"],
        "net_worth_growth": dashboard["net_worth_growth"],
        "asset_allocation": dashboard["asset_allocation"],
        "top_holdings": dashboard["top_holdings"],
        "valuation_status": dashboard["valuation_status"],
        "valuation_coverage": dashboard["valuation_coverage"],
        "analytics": analytics,
        "optimization": optimization,
        "rebalancing_suggestions": optimization.get("rebalancing_suggestions", []),
        "assumptions": [
            "Portfolio risk uses account-level dated snapshots.",
            "Beta and optimization require aligned per-instrument and NIFTY 50 benchmark history.",
        ],
    }

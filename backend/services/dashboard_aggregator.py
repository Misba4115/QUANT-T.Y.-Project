"""Deterministic, provenance-aware dashboard aggregation."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Any

from repositories.base import SupabaseRepository
from services.portfolio_analytics import snapshot_metrics
from services.tax_analytics import SECTION_80C_LIMIT, calculate_tax_metrics


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


class DashboardAggregator:
    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def aggregate(
        self,
        user_id: str,
        time_period: str = "1y",
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict[str, Any]:
        users = self.repo.find("users", [("user_id", user_id)], limit=1)
        if not users:
            raise ValueError("User not found")
        user = users[0]

        accounts = self.repo.list_for_user("banking_accounts", user_id)
        bank_transactions = self.repo.list_for_user(
            "bank_transactions", user_id, order_by="tx_date", descending=True
        )
        holdings_by_type = {
            "Equity": self.repo.list_for_user("equity_holdings", user_id),
            "Mutual Fund": self.repo.list_for_user("mutual_fund_holdings", user_id),
            "ETF": self.repo.list_for_user("etf_holdings", user_id),
            "Crypto": self.repo.list_for_user("crypto_holdings", user_id),
        }

        cash_value = sum(_number(account.get("current_balance")) for account in accounts)
        valuation = self._value_holdings(holdings_by_type)
        net_worth = cash_value + valuation["total_value"]
        asset_values = {"Cash": cash_value, **valuation["asset_values"]}
        allocation = self._allocation(asset_values, net_worth)
        cashflow = self._cashflow(bank_transactions)
        snapshots = self._snapshots(user_id, time_period, date_from, date_to)
        performance = snapshot_metrics(snapshots)
        tax = calculate_tax_metrics(user_id, self.db)
        alerts = self._alerts(net_worth, cashflow, valuation)

        known_asset_cost = valuation["total_cost"]
        known_asset_value = valuation["total_value"]
        pnl = known_asset_value - known_asset_cost

        profile_income = _number(user.get("monthly_income"))
        profile_expenses = _number(user.get("monthly_expenses"))
        current_cf = cashflow["current_month"]
        effective_surplus = round(current_cf["surplus"], 4) if (current_cf["income"] > 0 or current_cf["expense"] > 0) else round(profile_income - profile_expenses, 4)

        return {
            "net_worth": round(net_worth, 4),
            "net_worth_growth": performance["growth_percent"],
            "net_worth_growth_status": "available" if performance["growth_percent"] is not None else "insufficient_history",
            "stated_risk_profile": user.get("risk_profile"),
            "measured_portfolio_risk": performance["risk"],
            "risk_level": performance["risk"]["level"] or "Unavailable",
            "monthly_income": profile_income,
            "monthly_expenses": profile_expenses,
            "surplus": effective_surplus,
            "cashflow": cashflow,
            "tax_saved": tax["section_80c_used"],
            "tax_limit": SECTION_80C_LIMIT,
            "tax_status": tax["section_80c_status"],
            "estimated_capital_gains_tax": tax["estimated_capital_gains_tax"],
            "tax_rule_version": tax["rule_version"],
            "portfolio_history": snapshots,
            "history_status": "available" if snapshots else "insufficient_history",
            "asset_allocation": allocation,
            "top_holdings": valuation["holdings"][:5],
            "portfolio_cost_basis": round(known_asset_cost, 4),
            "portfolio_profit_loss": round(pnl, 4),
            "valuation_coverage": valuation["coverage"],
            "valuation_status": valuation["status"],
            "alerts": alerts,
            "data_as_of": datetime.now(timezone.utc).isoformat(),
            "source_status": valuation["source_status"],
        }

    def _value_holdings(self, holdings_by_type: dict[str, list[dict]]) -> dict[str, Any]:
        config = {
            "Equity": ("symbol", "quantity", "avg_price", "current_price"),
            "Mutual Fund": ("mf_name", "units", "avg_nav", "current_nav"),
            "ETF": ("symbol", "quantity", "avg_price", "current_price"),
            "Crypto": ("symbol", "quantity", "avg_price", "current_price"),
        }
        valued: list[dict[str, Any]] = []
        asset_values: dict[str, float] = {}
        total_cost = 0.0
        market_valued_cost = 0.0
        source_status: dict[str, int] = {}

        for asset_type, rows in holdings_by_type.items():
            name_key, quantity_key, average_key, current_key = config[asset_type]
            asset_total = 0.0
            for row in rows:
                quantity = _number(row.get(quantity_key))
                average = _number(row.get(average_key))
                current_raw = row.get(current_key)
                has_market_price = current_raw is not None and _number(current_raw) > 0
                price = _number(current_raw) if has_market_price else average
                status = "stored" if has_market_price else "estimated_cost_basis"
                source = row.get("price_source") if has_market_price else "user_cost_basis"
                value = quantity * price
                cost = quantity * average
                total_cost += cost
                if has_market_price:
                    market_valued_cost += cost
                asset_total += value
                source_status[status] = source_status.get(status, 0) + 1
                pnl_pct = ((price - average) / average * 100) if average else None
                valued.append(
                    {
                        "instrument": row.get(name_key) or "Unknown",
                        "type": asset_type,
                        "quantity": quantity,
                        "avg_price": average,
                        "current_price": price,
                        "current_value": round(value, 4),
                        "profit_loss_percent": round(pnl_pct, 4) if pnl_pct is not None else None,
                        "valuation_status": status,
                        "price_source": source,
                        "source_timestamp": row.get("source_timestamp"),
                        "last_synced_at": row.get("last_synced_at"),
                    }
                )
            asset_values[asset_type] = asset_total

        valued.sort(key=lambda row: row["current_value"], reverse=True)
        coverage = market_valued_cost / total_cost if total_cost else 1.0
        status = "market_valued" if coverage == 1 else "partial_estimate" if coverage > 0 else "cost_basis_estimate"
        return {
            "holdings": valued,
            "asset_values": asset_values,
            "total_value": sum(asset_values.values()),
            "total_cost": total_cost,
            "coverage": round(coverage, 4),
            "status": status,
            "source_status": source_status,
        }

    @staticmethod
    def _allocation(asset_values: dict[str, float], net_worth: float) -> list[dict[str, Any]]:
        colors = {
            "Cash": "#3b82f6",
            "Equity": "#10b981",
            "Mutual Fund": "#f59e0b",
            "ETF": "#8b5cf6",
            "Crypto": "#ef4444",
        }
        if net_worth <= 0:
            return []
        return [
            {"name": name, "value": round(value / net_worth * 100, 4), "amount": round(value, 4), "color": colors[name]}
            for name, value in asset_values.items()
            if value > 0
        ]

    @staticmethod
    def _cashflow(rows: list[dict[str, Any]]) -> dict[str, Any]:
        today = date.today()
        months: list[str] = []
        year, month = today.year, today.month
        for _ in range(12):
            months.append(f"{year:04d}-{month:02d}")
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        months.reverse()
        series = {key: {"month": key, "income": 0.0, "expense": 0.0, "surplus": 0.0} for key in months}
        categories: dict[str, float] = {}
        uncategorized = 0
        for row in rows:
            value = str(row.get("tx_date") or "")[:7]
            if value not in series:
                continue
            amount = _number(row.get("amount"))
            if row.get("tx_type") == "credit":
                series[value]["income"] += amount
            elif row.get("tx_type") == "debit":
                series[value]["expense"] += amount
                category = row.get("category") or "Uncategorized"
                categories[category] = categories.get(category, 0) + amount
                if not row.get("category"):
                    uncategorized += 1
        for values in series.values():
            values["surplus"] = values["income"] - values["expense"]
            for field in ("income", "expense", "surplus"):
                values[field] = round(values[field], 4)
        current = series[f"{today.year:04d}-{today.month:02d}"]
        return {
            "current_month": current,
            "monthly_series": list(series.values()),
            "spending_by_category": {key: round(value, 4) for key, value in sorted(categories.items())},
            "uncategorized_count": uncategorized,
        }

    def _snapshots(
        self, user_id: str, time_period: str, date_from: date | None = None, date_to: date | None = None
    ) -> list[dict[str, Any]]:
        rows = self.repo.list_for_user(
            "portfolio_snapshots", user_id, order_by="snapshot_date", descending=False
        )
        limits = {"1m": 31, "3m": 93, "6m": 186, "1y": 366, "all": None}
        if time_period == "custom":
            if not date_from or not date_to:
                raise ValueError("Custom dashboard periods require date_from and date_to")
            rows = [
                row for row in rows
                if date_from <= date.fromisoformat(str(row["snapshot_date"])[:10]) <= date_to
            ]
        else:
            days = limits.get(time_period, 366)
            if days:
                cutoff = date.today().toordinal() - days
                rows = [row for row in rows if date.fromisoformat(str(row["snapshot_date"])[:10]).toordinal() >= cutoff]
        return [
            {
                "month": str(row["snapshot_date"])[:10],
                "value": round(_number(row.get("net_worth")), 4),
                "valuation_coverage": _number(row.get("valuation_coverage")),
            }
            for row in rows
        ]

    @staticmethod
    def _alerts(net_worth: float, cashflow: dict[str, Any], valuation: dict[str, Any]) -> list[dict[str, str]]:
        alerts: list[dict[str, str]] = []
        current = cashflow["current_month"]
        if net_worth == 0:
            alerts.append({"id": "empty-data", "type": "info", "message": "Add an account or holding to calculate your dashboard.", "icon": "lightbulb"})
        if current["income"] > 0 and current["expense"] > current["income"]:
            alerts.append({"id": "negative-cashflow", "type": "warning", "message": "Recorded expenses exceed recorded income this month.", "icon": "alert-triangle"})
        if valuation["status"] != "market_valued" and valuation["holdings"]:
            alerts.append({"id": "partial-prices", "type": "warning", "message": "Some holdings use cost basis because a current market price is unavailable.", "icon": "alert-triangle"})
        return alerts

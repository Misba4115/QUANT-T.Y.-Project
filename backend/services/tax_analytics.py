"""Shared evidence-bound Indian capital-gains and Section 80C calculations."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import date
from typing import Any

from repositories.base import SupabaseRepository

SECTION_80C_LIMIT = 150_000.0
RULE_VERSION = "india-equity-tax-2024-07-23-v1"


def _rule(sale_date: date) -> dict[str, float]:
    if sale_date >= date(2024, 7, 23):
        return {"ltcg_exemption": 125_000.0, "ltcg_rate": 0.125, "stcg_rate": 0.20}
    return {"ltcg_exemption": 100_000.0, "ltcg_rate": 0.10, "stcg_rate": 0.15}


def _realized(rows: list[dict[str, Any]], quantity_key: str, price_key: str) -> tuple[list[dict], list[str]]:
    lots: dict[str, deque] = defaultdict(deque)
    gains: list[dict] = []
    warnings: list[str] = []
    for row in sorted(rows, key=lambda item: str(item.get("tx_date") or "")):
        symbol = str(row.get("symbol") or row.get("scheme_code") or row.get("mf_name") or "").upper()
        if not symbol:
            warnings.append("A transaction without an instrument identifier was skipped")
            continue
        quantity = float(row.get(quantity_key) or 0)
        price = float(row.get(price_key) or 0)
        tx_date = date.fromisoformat(str(row["tx_date"])[:10])
        if row.get("tx_type") == "buy":
            lots[symbol].append([quantity, price, tx_date])
            continue
        if row.get("tx_type") != "sell":
            continue
        remaining = quantity
        while remaining > 0 and lots[symbol]:
            lot = lots[symbol][0]
            used = min(remaining, lot[0])
            gains.append({"symbol": symbol, "sale_date": tx_date.isoformat(), "holding_days": (tx_date - lot[2]).days, "gain": used * (price - lot[1])})
            lot[0] -= used
            remaining -= used
            if lot[0] <= 1e-9:
                lots[symbol].popleft()
        if remaining > 1e-9:
            warnings.append(f"Sale of {symbol} lacks acquisition lots for {remaining:g} units")
    return gains, warnings


def calculate_tax_metrics(user_id: str, db: Any) -> dict[str, Any]:
    repo = SupabaseRepository(db)
    equity_gains, warnings = _realized(repo.list_for_user("equity_transactions", user_id), "quantity", "price")
    etf_gains, etf_warnings = _realized(repo.list_for_user("etf_transactions", user_id), "quantity", "price")
    warnings.extend(etf_warnings)
    gains = equity_gains + etf_gains
    by_year: dict[str, dict[str, float]] = defaultdict(lambda: {"ltcg": 0.0, "stcg": 0.0})
    for gain in gains:
        sale_date = date.fromisoformat(gain["sale_date"])
        start = sale_date.year if sale_date.month >= 4 else sale_date.year - 1
        bucket = "ltcg" if gain["holding_days"] > 365 else "stcg"
        by_year[f"{start}-{str(start + 1)[-2:]}"][bucket] += gain["gain"]
    estimated_tax = 0.0
    breakdown = []
    for financial_year, amounts in sorted(by_year.items()):
        rule = _rule(date(int(financial_year[:4]) + 1, 3, 31))
        taxable_ltcg = max(0.0, amounts["ltcg"] - rule["ltcg_exemption"])
        tax = taxable_ltcg * rule["ltcg_rate"] + max(0.0, amounts["stcg"]) * rule["stcg_rate"]
        estimated_tax += tax
        breakdown.append({"financial_year": financial_year, **amounts, "ltcg_exemption": rule["ltcg_exemption"], "estimated_tax": round(tax, 4)})
    explicit_80c = sum(
        float(row.get("amount") or 0)
        for row in repo.list_for_user("bank_transactions", user_id)
        if row.get("tx_type") == "debit" and str(row.get("category") or "").upper() in {"80C", "ELSS", "PPF", "LIC"}
    )
    used = min(explicit_80c, SECTION_80C_LIMIT)
    return {
        "agent": "tax",
        "status": "available" if gains else "unavailable_without_realized_lots",
        "rule_version": RULE_VERSION,
        "section_80c_status": "available" if explicit_80c > 0 else "unavailable_without_eligible_evidence",
        "section_80c_used": round(used, 4),
        "section_80c_headroom": round(SECTION_80C_LIMIT - used, 4),
        "realized_gain_breakdown": breakdown,
        "estimated_capital_gains_tax": round(estimated_tax, 4) if gains else None,
        "warnings": warnings,
        "disclaimer": "Educational estimate only; verify transaction lots and applicable rules with a qualified tax professional.",
    }

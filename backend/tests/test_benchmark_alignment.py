"""Small production-path checks for benchmarked deterministic behavior."""
from datetime import date

import pytest
from pydantic import ValidationError

from schemas.schemas import BankTransactionCreate
from services.guardian_detector import detect_anomalies
from services.statement_parser import categorise, normalize_transaction_row
from services.tax_analytics import calculate_80c_scenario, calculate_equity_gain_scenario


def test_guardian_date_only_does_not_invent_clock_or_exact_duplicate():
    row = {"tx_date": "2026-06-01", "description": "Coffee", "amount": 100}
    records = [("bank_transactions", {**row, "bank_tx_id": str(i)}, 100) for i in range(2)]
    flags, _, _, mode, _ = detect_anomalies(records)
    assert mode == "rule_based_insufficient_sample"
    assert flags.tolist() == [False, False]


def test_guardian_uses_source_local_hour_and_precise_duplicate():
    rows = [
        {"tx_date": "2026-06-01", "occurred_at": "2026-06-01T04:30:00Z", "occurred_local_hour": 10,
         "description": "Coffee", "amount": 100, "account_id": "account-1"},
        {"tx_date": "2026-06-01", "occurred_at": "2026-06-01T04:30:00Z", "occurred_local_hour": 10,
         "description": "Coffee", "amount": 100, "account_id": "account-1"},
    ]
    flags, _, reasons, _, _ = detect_anomalies([("bank_transactions", row, 100) for row in rows])
    assert flags.tolist() == [False, True]
    assert "duplicate" in reasons[1].lower()


def test_statement_timestamp_and_category_families():
    row = normalize_transaction_row({
        "tx_date": "2026-06-01", "occurred_at": "2026-06-01T02:30:00+05:30",
        "description": "BESCOM electricity", "amount": -100,
    })
    assert row["occurred_local_hour"] == 2
    assert row["category"] == "Utilities"
    assert categorise("Apollo pharmacy") == "Healthcare"
    assert categorise("premium payment") != "EMI"


def test_bank_api_requires_offset_for_clock_based_detection():
    payload = {"tx_date": "2026-06-01", "description": "Coffee", "amount": 100, "tx_type": "debit"}
    assert BankTransactionCreate(**payload).occurred_at is None
    with pytest.raises(ValidationError):
        BankTransactionCreate(**payload, occurred_at="2026-06-01T02:30:00")
    assert BankTransactionCreate(**payload, occurred_at="2026-06-01T02:30:00+05:30").occurred_at.hour == 2
    with pytest.raises(ValueError):
        normalize_transaction_row({**payload, "occurred_at": "2026-06-01T02:30:00"})


def test_production_tax_scenarios_are_callable():
    assert calculate_80c_scenario(new_investment=100_000, used_ytd=50_000)["total_80c_used_after"] == 150_000
    assert calculate_equity_gain_scenario(
        holding_period_days=400, capital_gain=200_000, sale_date=date(2025, 4, 1)
    )["taxable_gain"] == 75_000

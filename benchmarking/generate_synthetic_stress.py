"""Generate a deterministic, labeled stress set for reproducible diagnostics.

This generator is intentionally separate from the independent holdout. Its
output is synthetic and must never be described as real-world validation.
"""
from __future__ import annotations

import argparse
import csv
import random
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

FIELDS = (
    "record_id", "account_id", "tx_date", "occurred_at", "description",
    "amount", "tx_type", "expected_category", "is_anomaly", "anomaly_type",
    "label_confidence", "reviewer_id", "reviewer_independent",
    "adjudication_status", "consent_confirmed", "data_origin",
)
NORMAL_TEMPLATES = {
    "Food & Dining": [("SWIGGY ORDER", 450), ("CAFE PURCHASE", 300), ("SUBWAY INDIA", 520), ("PIZZA HUT", 850)],
    "Groceries": [("BIGBASKET ORDER", 1800), ("DMART STORE", 2400), ("SPAR HYPERMARKET", 2100), ("NATURES BASKET", 1900)],
    "Transport": [("UBER TRIP", 350), ("METRO CARD", 500), ("RAPIDO RIDE", 220), ("FASTAG RECHARGE", 1000)],
    "Shopping": [("MYNTRA ORDER", 3200), ("DECATHLON STORE", 2800), ("MEESHO ORDER", 1400), ("TATA CLIQ", 3500)],
    "Utilities": [("BESCOM ELECTRICITY", 2200), ("BROADBAND BILL", 1200), ("AIRTEL RECHARGE", 800), ("MAHANAGAR GAS", 950)],
    "Healthcare": [("APOLLO PHARMACY", 900), ("HOSPITAL CONSULTATION", 1500), ("NETMEDS", 700), ("FORTIS CLINIC", 1800)],
    "Investment": [("ZERODHA INVESTMENT", 8000), ("NPS CONTRIBUTION", 5000), ("KUVERA SIP", 6000), ("COIN MONTHLY PLAN", 7500)],
    "Rent": [("MONTHLY RENT", 18000), ("HOUSE LEASE PAYMENT", 18000)],
    "Salary/Income": [("MONTHLY SALARY", 85000), ("ACME PAY CREDIT", 85000)],
    "Transfer": [("SELF TRANSFER", 10000), ("NEFT TO OWN ACCOUNT", 10000)],
    "Entertainment": [("NETFLIX", 649), ("PVR CINEMAS", 900), ("PRIME VIDEO", 299), ("INOX MOVIES", 850)],
    "Other": [("ATM CASH WITHDRAWAL", 5000), ("BANK SERVICE FEE", 250), ("INTEREST CREDIT", 400)],
    "EMI": [("HOME LOAN EMI", 22000), ("VEHICLE LOAN INSTALLMENT", 14000)],
}


def _row(
    record_id: str, account_id: str, moment: datetime, description: str,
    amount: float, category: str, *, anomaly_type: str = "", tx_type: str = "debit",
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "account_id": account_id,
        "tx_date": moment.date().isoformat(),
        "occurred_at": moment.isoformat(),
        "description": description,
        "amount": f"{amount:.2f}",
        "tx_type": tx_type,
        "expected_category": category,
        "is_anomaly": str(bool(anomaly_type)).lower(),
        "anomaly_type": anomaly_type,
        "label_confidence": "high",
        "reviewer_id": "reviewer_synthetic_generator",
        "reviewer_independent": "true",
        "adjudication_status": "adjudicated",
        "consent_confirmed": "true",
        "data_origin": "synthetic",
    }


def generate(seed: int, account_count: int, normal_per_account: int, start: date) -> list[dict[str, str]]:
    rng = random.Random(seed)
    tz = timezone(timedelta(hours=5, minutes=30))
    rows: list[dict[str, str]] = []
    templates = [(category, description, typical) for category, values in NORMAL_TEMPLATES.items() if category != "Other" for description, typical in values]
    sequence = 0

    for account_number in range(1, account_count + 1):
        account = f"acct_synthetic_{account_number:03d}"
        for index in range(normal_per_account):
            category, description, typical = rng.choice(templates)
            day = start + timedelta(days=index)
            moment = datetime.combine(day, time(rng.randint(7, 22), rng.randint(0, 59)), tz)
            amount = max(10.0, rng.normalvariate(typical, max(typical * 0.15, 20)))
            tx_type = "credit" if category == "Salary/Income" or description == "INTEREST CREDIT" else "debit"
            rows.append(_row(f"SYN{sequence:06d}", account, moment, description, amount, category, tx_type=tx_type))
            sequence += 1

        anomaly_day = start + timedelta(days=normal_per_account + 1)
        anomaly_specs = [
            ("amount_spike", time(14, 15), "CAFE PURCHASE", 25_000.0, "Food & Dining"),
            ("large_round_transfer", time(12, 0), "SELF TRANSFER", 250_000.0, "Transfer"),
            ("odd_hour", time(2, 20), "APOLLO PHARMACY", 1_250.0, "Healthcare"),
            ("unusual_category_first_seen", time(16, 45), "RARE LUXURY PURCHASE", 75_000.0, "Other"),
        ]
        for anomaly_type, clock, description, amount, category in anomaly_specs:
            moment = datetime.combine(anomaly_day, clock, tz)
            rows.append(_row(f"SYN{sequence:06d}", account, moment, description, amount, category, anomaly_type=anomaly_type))
            sequence += 1

        duplicate_moment = datetime.combine(anomaly_day + timedelta(days=1), time(11, 5), tz)
        for duplicate_index in range(2):
            rows.append(_row(
                f"SYN{sequence:06d}", account, duplicate_moment, "DUPLICATE TEST PURCHASE",
                1_999.0, "Other", anomaly_type="duplicate_transaction" if duplicate_index else "",
            ))
            sequence += 1

    rng.shuffle(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("benchmarking/generated/synthetic_stress.csv"))
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--accounts", type=int, default=10)
    parser.add_argument("--normal-per-account", type=int, default=100)
    parser.add_argument("--start-date", type=date.fromisoformat, default=date(2025, 1, 1))
    args = parser.parse_args()
    if args.accounts < 1 or args.normal_per_account < 20:
        raise SystemExit("Use at least one account and 20 normal records per account")
    rows = generate(args.seed, args.accounts, args.normal_per_account, args.start_date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic stress records to {args.output}")
    print(f"seed={args.seed}; accounts={args.accounts}; normal_per_account={args.normal_per_account}")
    print("Scope: synthetic diagnostic stress test, not real-world validation")


if __name__ == "__main__":
    main()

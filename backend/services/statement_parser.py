"""Deterministic bank-statement normalization and categorization."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from services.csv_parser import parse_csv_rows

CATEGORY_KEYWORDS = {
    "Salary": ["salary", "payroll", "neft cr"],
    "Food": ["zomato", "swiggy", "restaurant", "cafe", "domino"],
    "Rent": ["rent", "landlord"],
    "EMI": ["emi", "loan", "installment"],
    "Shopping": ["amazon", "flipkart", "myntra", "nykaa"],
    "Entertainment": ["netflix", "spotify", "pvr", "hotstar"],
    "Investment": ["mutual fund", "zerodha", "groww", "sip"],
}

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d-%b-%Y", "%m/%d/%Y")


def categorise(description: str) -> str:
    lowered = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "Other"


def parse_date(value: Any) -> str:
    text = str(value or "").strip()
    for pattern in DATE_FORMATS:
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized transaction date: {text or '<blank>'}")


def _amount(value: Any) -> float:
    text = str(value or "").replace(",", "").replace("₹", "").strip()
    if not text:
        return 0.0
    if text.startswith("(") and text.endswith(")"):
        text = f"-{text[1:-1]}"
    return float(text)


def normalize_transaction_row(row: dict[str, Any]) -> dict[str, Any]:
    description = str(row.get("description") or "").strip()
    if not description:
        raise ValueError("Transaction description is required")
    debit, credit = _amount(row.get("debit")), _amount(row.get("credit"))
    signed = _amount(row.get("amount"))
    explicit_type = str(row.get("tx_type") or row.get("type") or "").lower().strip()

    if debit and credit:
        raise ValueError("A transaction row cannot have both debit and credit values")
    if credit:
        tx_type, amount = "credit", abs(credit)
    elif debit:
        tx_type, amount = "debit", abs(debit)
    elif explicit_type in {"debit", "credit"}:
        tx_type, amount = explicit_type, abs(signed)
    elif signed < 0:
        tx_type, amount = "debit", abs(signed)
    elif signed > 0:
        raise ValueError("Positive amount requires tx_type or a credit column")
    else:
        raise ValueError("Transaction amount must be non-zero")

    return {
        "account_id": row.get("account_id") or row.get("account") or None,
        "tx_date": parse_date(row.get("tx_date")),
        "description": description,
        "amount": amount,
        "tx_type": tx_type,
        "category": row.get("category") or categorise(description),
    }


def parse_bank_statement(file_bytes: bytes) -> list[dict[str, Any]]:
    return [normalize_transaction_row(row) for row in parse_csv_rows(file_bytes)]

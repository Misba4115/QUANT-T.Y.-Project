"""Deterministic bank-statement normalization and categorization."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from services.csv_parser import parse_csv_rows

# Keep transaction-channel words (UPI, NEFT, IMPS) out of merchant rules: a
# channel alone says nothing about whether a payment is a transfer or a purchase.
CATEGORY_KEYWORDS = {
    "Transfer": ("transfer", "self transfer", "funds moved", "own account", "neft to own account"),
    "Salary": ("salary", "salary credit", "pay credit", "payroll", "freelance payment", "wages"),
    "Rent": ("rent", "landlord", "nobroker rent", "house lease"),
    "Investment": ("mutual fund", "zerodha", "groww", "kuvera", "coin monthly", "sip", "nps", "ppf", "elss", "lic premium"),
    "EMI": ("emi", "loan installment", "loan repayment"),
    "Groceries": ("grocery", "groceries", "supermarket", "hypermarket", "bigbasket", "zepto", "dmart", "reliance fresh", "more supermarket", "natures basket", "spar"),
    "Transport": ("uber", "ola cabs", "rapido", "railway", "irctc", "metro card", "fastag", "fuel", "petrol", "diesel"),
    "Utilities": ("electricity", "bescom", "water board", "gas agency", "mahanagar gas", "indraprastha gas", "postpaid", "recharge", "fiber bill", "broadband"),
    "Healthcare": ("hospital", "pharmacy", "medical", "medplus", "apollo", "practo", "consultation", "netmeds", "fortis", "1mg"),
    "Food": ("zomato", "swiggy", "restaurant", "cafe", "coffee", "domino", "dominos", "mcdonalds", "ccd", "subway", "pizza hut", "starbucks"),
    "Shopping": ("amazon", "flipkart", "myntra", "nykaa", "ajio", "decathlon", "meesho", "tata cliq", "pantaloons", "croma"),
    "Entertainment": ("netflix", "spotify", "pvr", "hotstar", "bookmyshow", "prime video", "inox", "live events", "ticketing"),
}

_CATEGORY_PATTERNS = {
    category: [re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)") for term in terms]
    for category, terms in CATEGORY_KEYWORDS.items()
}

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d-%b-%Y", "%m/%d/%Y")


def categorise(description: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", " ", description.casefold()).strip()
    for category, patterns in _CATEGORY_PATTERNS.items():
        if any(pattern.search(lowered) for pattern in patterns):
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

    occurred_at = str(row.get("occurred_at") or "").strip()
    occurred_local_hour = None
    if occurred_at:
        try:
            parsed_time = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid occurred_at timestamp; use ISO 8601") from exc
        if parsed_time.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone offset")
        occurred_local_hour = parsed_time.hour

    normalized = {
        "account_id": row.get("account_id") or row.get("account") or None,
        "tx_date": parse_date(row.get("tx_date")),
        "description": description,
        "amount": amount,
        "tx_type": tx_type,
        "category": row.get("category") or categorise(description),
    }
    if occurred_at:
        normalized["occurred_at"] = occurred_at
        normalized["occurred_local_hour"] = occurred_local_hour
    return normalized


def parse_bank_statement(file_bytes: bytes) -> list[dict[str, Any]]:
    return [normalize_transaction_row(row) for row in parse_csv_rows(file_bytes)]

"""
Bank Statement Parser + Auto-Categorizer
"""
# import pandas as pd
# import re

CATEGORIES = ["Food", "Rent", "Salary", "EMI", "Shopping", "Entertainment", "Investment", "Other"]

# Simple keyword rules for auto-categorisation
CATEGORY_KEYWORDS = {
    "Salary": ["salary", "payroll", "neft cr"],
    "Food":   ["zomato", "swiggy", "restaurant", "cafe", "domino"],
    "Rent":   ["rent", "landlord"],
    "EMI":    ["emi", "loan", "installment"],
    "Shopping": ["amazon", "flipkart", "myntra", "nykaa"],
    "Entertainment": ["netflix", "spotify", "pvr", "hotstar"],
    "Investment": ["mutual fund", "zerodha", "groww", "sip"],
}


def parse_bank_statement(file_bytes: bytes) -> list[dict]:
    """
    Parse a bank statement CSV and auto-categorise each transaction.

    Supported formats: HDFC Bank, SBI, ICICI (detect by column names).

    Steps:
      1. Read CSV with pandas
      2. Detect bank format from column names
      3. Normalise columns → [date, description, debit, credit]
      4. For each row:
           - tx_type = 'credit' if credit > 0 else 'debit'
           - category = categorise(description) using CATEGORY_KEYWORDS
      5. Return list of dicts matching bank_transactions schema

    Expected output per row:
        {
            "tx_date": "2025-03-01",
            "description": "ZOMATO ORDER",
            "amount": 250.00,
            "tx_type": "debit",
            "category": "Food"
        }

    TODO: implement
    """
    raise NotImplementedError


def categorise(description: str) -> str:
    """Match description to a category using keyword rules. TODO: implement"""
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "Other"

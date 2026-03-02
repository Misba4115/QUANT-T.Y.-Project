"""
Cashflow Engine — Income vs Expense Aggregation
"""
# import pandas as pd


def run_cashflow_agent(user_id: str, db) -> dict:
    """
    Aggregate bank transactions to produce monthly cashflow summary.

    Steps:
      1. Fetch all bank_transactions for user_id
      2. Group by (month, tx_type):
           - credits  → income
           - debits   → expenses
      3. Group debits by category for spending breakdown
         ('Food', 'Rent', 'EMI', 'Shopping', 'Entertainment', 'Investment', 'Other')
      4. Compute surplus = total_income - total_expense per month
      5. Return last 12 months of data for the cashflow chart

    Returns:
        {
            "current_month": {
                "income": float,
                "expense": float,
                "surplus": float
            },
            "monthly_series": [
                {"month": "2025-03", "income": ..., "expense": ..., "surplus": ...},
                ...
            ],
            "spending_by_category": {"Food": float, "Rent": float, ...}
        }

    TODO: implement
    """
    raise NotImplementedError("Cashflow agent not implemented yet")

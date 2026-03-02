"""
CSV Parser — Parse Zerodha/Upstox equity/ETF holding CSV files.
"""
# import pandas as pd


ZERODHA_COLUMNS = ["Stock Symbol", "ISIN", "Quantity", "Average Price", "Last Price", "Close Price", "PnL"]
UPSTOX_COLUMNS  = ["Symbol", "Quantity", "Average Price", "Last Traded Price", "Profit/Loss"]


def parse_equity_csv(file_bytes: bytes, broker: str = "zerodha") -> list[dict]:
    """
    Parse a holdings CSV exported from Zerodha or Upstox.

    Steps:
      1. Read CSV with pandas
      2. Identify column names based on broker format
      3. Clean & standardise rows → list of dicts matching equity_holdings schema
      4. Return list ready to bulk-INSERT into equity_holdings table

    Expected output per row:
        {
            "symbol": "HDFCBANK",
            "name": "HDFC Bank Ltd",
            "exchange": "NSE",
            "quantity": 10,
            "avg_price": 1500.00,
            "broker": "zerodha"
        }

    TODO: implement
    """
    raise NotImplementedError

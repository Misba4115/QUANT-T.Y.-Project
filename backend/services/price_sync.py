"""
Price Sync Service — Yahoo Finance / AMFI / CoinGecko
"""
# import yfinance as yf
# from pycoingecko import CoinGeckoAPI
# import httpx


def sync_equity_prices(symbols: list[str]) -> dict[str, float]:
    """
    Fetch current prices for equity/ETF symbols from Yahoo Finance.
    Append '.NS' for NSE symbols, e.g. 'HDFCBANK' → 'HDFCBANK.NS'

    Returns:
        {"HDFCBANK": 1650.45, "INFY": 1820.10, ...}

    TODO: implement with yfinance.download() or Ticker.info
    """
    raise NotImplementedError


def sync_mf_navs(scheme_codes: list[str]) -> dict[str, float]:
    """
    Fetch current NAVs from AMFI India for mutual fund scheme codes.
    API: https://api.mfapi.in/mf/{scheme_code}

    Returns:
        {"119551": 85.4321, ...}

    TODO: implement with httpx GET
    """
    raise NotImplementedError


def sync_crypto_prices(symbols: list[str]) -> dict[str, float]:
    """
    Fetch current prices in INR from CoinGecko.
    symbols: CoinGecko IDs, e.g. ['bitcoin', 'ethereum']

    Returns:
        {"bitcoin": 6750000.0, "ethereum": 320000.0, ...}

    TODO: implement with pycoingecko
    """
    raise NotImplementedError

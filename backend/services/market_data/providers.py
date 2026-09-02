"""External price-provider adapters. No provider is contacted at import time."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

import httpx

from core.config import get_settings
from services.market_data.models import PriceQuote


class PriceProvider(Protocol):
    name: str

    def fetch(self, instrument_key: str, **metadata) -> PriceQuote: ...

    def fetch_history(self, instrument_key: str, days: int = 370, **metadata) -> list[dict]: ...


def _unavailable(asset_type: str, key: str, provider: str, exc: Exception) -> PriceQuote:
    return PriceQuote(
        asset_type=asset_type,
        instrument_key=key,
        price=None,
        currency="INR",
        provider=provider,
        observed_at=None,
        fetched_at=datetime.now(timezone.utc),
        status="unavailable",
        error=type(exc).__name__,
    )


class YahooFinanceProvider:
    name = "yahoo_finance"

    def __init__(self, asset_type: str):
        self.asset_type = asset_type

    def fetch(self, instrument_key: str, **metadata) -> PriceQuote:
        try:
            import yfinance as yf

            ticker = yf.Ticker(self._ticker_symbol(instrument_key, metadata))
            price = float(ticker.fast_info["last_price"])
            if price <= 0:
                raise ValueError("Provider returned a non-positive price")
            now = datetime.now(timezone.utc)
            return PriceQuote(self.asset_type, instrument_key, price, "INR", self.name, now, now, "delayed")
        except Exception as exc:
            return _unavailable(self.asset_type, instrument_key, self.name, exc)

    @staticmethod
    def _ticker_symbol(instrument_key: str, metadata: dict) -> str:
        explicit = str(metadata.get("provider_symbol") or "").strip()
        if explicit:
            return explicit
        if instrument_key.startswith("^"):
            return instrument_key
        exchange = str(metadata.get("exchange") or "NSE").upper()
        return f"{instrument_key}{'.BO' if exchange == 'BSE' else '.NS'}"

    def fetch_history(self, instrument_key: str, days: int = 370, **metadata) -> list[dict]:
        try:
            import yfinance as yf

            frame = yf.Ticker(self._ticker_symbol(instrument_key, metadata)).history(
                period="2y" if days > 370 else "1y", auto_adjust=True
            )
            if frame.empty or "Close" not in frame:
                return []
            cutoff = datetime.now(timezone.utc).date().toordinal() - max(1, days)
            return [
                {"price_date": index.date().isoformat(), "adjusted_close": float(value)}
                for index, value in frame["Close"].items()
                if index.date().toordinal() >= cutoff and float(value) > 0
            ]
        except Exception:
            return []



class MutualFundNAVProvider:
    name = "mfapi"

    def fetch(self, instrument_key: str, **metadata) -> PriceQuote:
        settings = get_settings()
        try:
            with httpx.Client(timeout=settings.market_data_timeout_seconds) as client:
                response = client.get(f"https://api.mfapi.in/mf/{instrument_key}")
                response.raise_for_status()
                payload = response.json()
            latest = payload["data"][0]
            price = float(latest["nav"])
            observed = datetime.strptime(latest["date"], "%d-%m-%Y").replace(tzinfo=timezone.utc)
            return PriceQuote("Mutual Fund", instrument_key, price, "INR", self.name, observed, datetime.now(timezone.utc), "delayed")
        except Exception as exc:
            return _unavailable("Mutual Fund", instrument_key, self.name, exc)

    def fetch_history(self, instrument_key: str, days: int = 370, **metadata) -> list[dict]:
        del metadata
        settings = get_settings()
        try:
            with httpx.Client(timeout=settings.market_data_timeout_seconds) as client:
                response = client.get(f"https://api.mfapi.in/mf/{instrument_key}")
                response.raise_for_status()
                payload = response.json()
            cutoff = datetime.now(timezone.utc).date().toordinal() - max(1, days)
            points = []
            for item in payload.get("data") or []:
                observed = datetime.strptime(item["date"], "%d-%m-%Y").date()
                nav = float(item["nav"])
                if observed.toordinal() >= cutoff and nav > 0:
                    points.append({"price_date": observed.isoformat(), "adjusted_close": nav})
            return sorted(points, key=lambda item: item["price_date"])
        except Exception:
            return []



class CoinGeckoProvider:
    name = "coingecko"
    SYMBOL_IDS = {
        "BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether", "BNB": "binancecoin",
        "SOL": "solana", "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin",
    }

    def fetch(self, instrument_key: str, **metadata) -> PriceQuote:
        settings = get_settings()
        symbol = instrument_key.upper()
        coin_id = str(metadata.get("provider_id") or self.SYMBOL_IDS.get(symbol) or symbol.lower())
        headers = {"x-cg-demo-api-key": settings.coingecko_api_key} if settings.coingecko_api_key else {}
        try:
            with httpx.Client(timeout=settings.market_data_timeout_seconds, headers=headers) as client:
                response = client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": coin_id, "vs_currencies": "inr", "include_last_updated_at": "true"},
                )
                response.raise_for_status()
                payload = response.json()[coin_id]
            price = float(payload["inr"])
            observed = datetime.fromtimestamp(payload.get("last_updated_at", 0), tz=timezone.utc)
            return PriceQuote("Crypto", symbol, price, "INR", self.name, observed, datetime.now(timezone.utc), "live")
        except Exception as exc:
            return _unavailable("Crypto", symbol, self.name, exc)

    def fetch_history(self, instrument_key: str, days: int = 370, **metadata) -> list[dict]:
        settings = get_settings()
        symbol = instrument_key.upper()
        coin_id = str(metadata.get("provider_id") or self.SYMBOL_IDS.get(symbol) or symbol.lower())
        headers = {"x-cg-demo-api-key": settings.coingecko_api_key} if settings.coingecko_api_key else {}
        try:
            with httpx.Client(timeout=settings.market_data_timeout_seconds, headers=headers) as client:
                response = client.get(
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                    params={"vs_currency": "inr", "days": min(max(1, days), 730), "interval": "daily"},
                )
                response.raise_for_status()
                payload = response.json()
            by_date: dict[str, float] = {}
            for timestamp_ms, price in payload.get("prices") or []:
                observed = datetime.fromtimestamp(float(timestamp_ms) / 1000, tz=timezone.utc).date().isoformat()
                if float(price) > 0:
                    by_date[observed] = float(price)
            return [{"price_date": day, "adjusted_close": by_date[day]} for day in sorted(by_date)]
        except Exception:
            return []


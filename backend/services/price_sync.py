"""Backward-compatible provider helpers; new code uses MarketDataService."""
from services.market_data.providers import CoinGeckoProvider, MutualFundNAVProvider, YahooFinanceProvider


def sync_equity_prices(symbols: list[str]) -> dict[str, float]:
    provider = YahooFinanceProvider("Equity")
    return {symbol: quote.price for symbol in symbols if (quote := provider.fetch(symbol)).price is not None}


def sync_mf_navs(scheme_codes: list[str]) -> dict[str, float]:
    provider = MutualFundNAVProvider()
    return {code: quote.price for code in scheme_codes if (quote := provider.fetch(code)).price is not None}


def sync_crypto_prices(symbols: list[str]) -> dict[str, float]:
    provider = CoinGeckoProvider()
    return {symbol: quote.price for symbol in symbols if (quote := provider.fetch(symbol)).price is not None}

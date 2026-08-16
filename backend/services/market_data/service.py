"""Price refresh, cache persistence, and stale fallback policy."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from repositories.base import SupabaseRepository
from services.market_data.models import PriceQuote
from services.market_data.providers import CoinGeckoProvider, MutualFundNAVProvider, PriceProvider, YahooFinanceProvider


class MarketDataService:
    HOLDINGS = {
        "equity_holdings": ("Equity", "equity_holding_id", "symbol", "current_price", "quantity"),
        "mutual_fund_holdings": ("Mutual Fund", "mf_holding_id", "scheme_code", "current_nav", "units"),
        "etf_holdings": ("ETF", "etf_holding_id", "symbol", "current_price", "quantity"),
        "crypto_holdings": ("Crypto", "crypto_holding_id", "symbol", "current_price", "quantity"),
    }

    def __init__(self, db: Any, providers: dict[str, PriceProvider] | None = None):
        self.db = db
        self.repo = SupabaseRepository(db)
        self.providers = providers or {
            "Equity": YahooFinanceProvider("Equity"),
            "ETF": YahooFinanceProvider("ETF"),
            "Mutual Fund": MutualFundNAVProvider(),
            "Crypto": CoinGeckoProvider(),
        }

    def refresh_user(self, user_id: str, asset_types: set[str] | None = None) -> dict[str, Any]:
        run_id = str(uuid4())
        requested = 0
        updated = 0
        failures: list[dict[str, str]] = []
        self.db.table("price_sync_runs").insert(
            {"price_sync_run_id": run_id, "user_id": user_id, "status": "processing"}
        ).execute()

        quotes: list[dict] = []
        for table, (asset_type, id_field, key_field, price_field, quantity_field) in self.HOLDINGS.items():
            if asset_types is not None and asset_type not in asset_types:
                continue
            for holding in self.repo.list_for_user(table, user_id):
                key = str(holding.get(key_field) or "").strip()
                if not key:
                    failures.append({"asset_type": asset_type, "instrument": "unknown", "error": f"missing {key_field}"})
                    continue
                requested += 1
                quote = self.providers[asset_type].fetch(key, **holding)
                if quote.price is None:
                    quote = self._stale_fallback(asset_type, key, quote)
                quotes.append(quote.to_dict())
                if quote.price is None:
                    failures.append({"asset_type": asset_type, "instrument": key, "error": quote.error or "unavailable"})
                    continue
                current_source = holding.get("source_timestamp")
                if current_source and quote.observed_at:
                    stored_time = datetime.fromisoformat(str(current_source).replace("Z", "+00:00"))
                    observed_time = quote.observed_at
                    if observed_time.tzinfo is None:
                        observed_time = observed_time.replace(tzinfo=timezone.utc)
                    if observed_time < stored_time:
                        failures.append({
                            "asset_type": asset_type,
                            "instrument": key,
                            "error": "older quote ignored; stored valuation is newer",
                        })
                        continue
                values = {
                    price_field: quote.price,
                    "current_value": round(float(holding.get(quantity_field) or 0) * quote.price, 2),
                    "price_source": quote.provider,
                    "source_timestamp": quote.observed_at.isoformat() if quote.observed_at else None,
                    "last_synced_at": quote.fetched_at.isoformat(),
                }
                result = (
                    self.db.table(table).update(values).eq(id_field, holding[id_field]).eq("user_id", user_id).execute()
                )
                if result.data:
                    updated += 1
                    self._cache(quote)
                else:
                    failures.append({"asset_type": asset_type, "instrument": key, "error": "holding update failed"})

        status = "completed" if not failures else "partial" if updated else "failed"
        if updated:
            self._record_daily_snapshot(user_id)
        self.db.table("price_sync_runs").update(
            {
                "status": status,
                "requested_count": requested,
                "updated_count": updated,
                "failed_count": len(failures),
                "errors": failures,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("price_sync_run_id", run_id).eq("user_id", user_id).execute()
        history = self.refresh_history_user(user_id)
        return {"price_sync_run_id": run_id, "status": status, "requested_count": requested, "updated_count": updated, "failed_count": len(failures), "quotes": quotes, "errors": failures, "history": history}

    def refresh_history_user(self, user_id: str, days: int = 370) -> dict[str, Any]:
        try:
            self.db.table("market_price_history").select("price_history_id").limit(1).execute()
        except Exception as exc:
            return {"status": "schema_unavailable", "stored_points": 0, "error": type(exc).__name__}

        stored = 0
        failures: list[dict[str, str]] = []
        requests: list[tuple[str, str, dict, PriceProvider]] = []
        for table, (asset_type, _id_field, key_field, _price_field, _quantity_field) in self.HOLDINGS.items():
            provider = self.providers[asset_type]
            if not callable(getattr(provider, "fetch_history", None)):
                continue
            for holding in self.repo.list_for_user(table, user_id):
                key = str(holding.get(key_field) or "").strip()
                if key:
                    requests.append((asset_type, key, holding, provider))
        benchmark_provider = self.providers.get("Equity")
        if callable(getattr(benchmark_provider, "fetch_history", None)):
            requests.append(("Benchmark", "NIFTY50", {"provider_symbol": "^NSEI"}, benchmark_provider))

        for asset_type, key, metadata, provider in requests:
            try:
                points = provider.fetch_history(key, days=days, **metadata)
                if not points:
                    failures.append({"asset_type": asset_type, "instrument": key, "error": "no historical prices returned"})
                    continue
                payload = [
                    {
                        "user_id": user_id, "asset_type": asset_type, "instrument_key": key,
                        "price_date": point["price_date"], "adjusted_close": point["adjusted_close"],
                        "currency": "INR", "provider": provider.name,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
                    for point in points
                ]
                result = self.db.table("market_price_history").upsert(
                    payload,
                    on_conflict="user_id,asset_type,instrument_key,price_date,provider",
                ).execute()
                stored += len(result.data or [])
            except Exception as exc:
                failures.append({"asset_type": asset_type, "instrument": key, "error": type(exc).__name__})
        status = "completed" if not failures else "partial" if stored else "unavailable"
        return {"status": status, "stored_points": stored, "failures": failures}

    def _record_daily_snapshot(self, user_id: str) -> None:
        from services.dashboard_aggregator import DashboardAggregator

        dashboard = DashboardAggregator(self.db).aggregate(user_id, "1m")
        payload = {
            "user_id": user_id,
            "snapshot_date": date.today().isoformat(),
            "net_worth": dashboard["net_worth"],
            "total_value": dashboard["net_worth"],
            "allocation": dashboard["asset_allocation"],
            "valuation_coverage": dashboard["valuation_coverage"],
            "source_status": dashboard["source_status"],
        }
        existing = (
            self.db.table("portfolio_snapshots").select("*")
            .eq("user_id", user_id).eq("snapshot_date", payload["snapshot_date"]).limit(1).execute().data or []
        )
        if existing:
            self.db.table("portfolio_snapshots").update(payload).eq("snapshot_id", existing[0]["snapshot_id"]).eq("user_id", user_id).execute()
        else:
            self.db.table("portfolio_snapshots").insert(payload).execute()

    def _cache(self, quote: PriceQuote) -> None:
        existing = (
            self.db.table("market_price_cache").select("*")
            .eq("asset_type", quote.asset_type).eq("instrument_key", quote.instrument_key)
            .eq("provider", quote.provider).limit(1).execute().data or []
        )
        payload = {
            "asset_type": quote.asset_type,
            "instrument_key": quote.instrument_key,
            "price": quote.price,
            "currency": quote.currency,
            "provider": quote.provider,
            "source_timestamp": quote.observed_at.isoformat() if quote.observed_at else quote.fetched_at.isoformat(),
            "fetched_at": quote.fetched_at.isoformat(),
            "status": quote.status if quote.status != "unavailable" else "stale",
        }
        if existing:
            self.db.table("market_price_cache").update(payload).eq("price_cache_id", existing[0]["price_cache_id"]).execute()
        else:
            self.db.table("market_price_cache").insert(payload).execute()

    def _stale_fallback(self, asset_type: str, key: str, failed: PriceQuote) -> PriceQuote:
        rows = (
            self.db.table("market_price_cache").select("*")
            .eq("asset_type", asset_type).eq("instrument_key", key)
            .order("fetched_at", desc=True).limit(1).execute().data or []
        )
        if not rows:
            return failed
        cached = rows[0]
        observed = datetime.fromisoformat(str(cached["source_timestamp"]).replace("Z", "+00:00"))
        return PriceQuote(
            asset_type, key, float(cached["price"]), str(cached.get("currency") or "INR"),
            str(cached["provider"]), observed, datetime.now(timezone.utc), "stale", failed.error,
        )

"""Upstox OAuth and read-only portfolio adapter."""
from __future__ import annotations

from datetime import datetime, timezone
from collections import deque
from threading import Lock
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from services.connectors.base import (
    AuthorizationRequired,
    ConnectorCapabilities,
    ConnectorError,
    NormalizedHolding,
)


class _RollingRateLimiter:
    """Process-local safety margin below Upstox's standard API limits."""

    def __init__(self, per_second: int = 45, per_minute: int = 450):
        self.per_second, self.per_minute = per_second, per_minute
        self.calls: deque[float] = deque()
        self.lock = Lock()

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                while self.calls and now - self.calls[0] >= 60:
                    self.calls.popleft()
                recent_second = sum(1 for value in self.calls if now - value < 1)
                if len(self.calls) < self.per_minute and recent_second < self.per_second:
                    self.calls.append(now)
                    return
                wait_for = 0.05 if recent_second >= self.per_second else max(0.05, 60 - (now - self.calls[0]))
            time.sleep(min(wait_for, 1.0))


_LIMITER = _RollingRateLimiter()


class UpstoxConnector:
    provider = "upstox"
    AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
    TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"
    API_URL = "https://api.upstox.com"

    def __init__(self, access_token: str, client: httpx.Client | None = None):
        self.access_token = access_token
        self.client = client or httpx.Client(timeout=12.0)

    @classmethod
    def authorization_url(cls, client_id: str, redirect_uri: str, state: str) -> str:
        return f"{cls.AUTH_URL}?{urlencode({'response_type': 'code', 'client_id': client_id, 'redirect_uri': redirect_uri, 'state': state})}"

    @classmethod
    def exchange_code(
        cls,
        *,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        transport = client or httpx.Client(timeout=12.0)
        response = transport.post(
            cls.TOKEN_URL,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if response.status_code >= 400:
            raise ConnectorError(f"Upstox authorization failed ({response.status_code})")
        payload = response.json()
        if not payload.get("access_token"):
            raise ConnectorError("Upstox did not return an access token")
        return payload

    def get_capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            accounts=True,
            holdings=True,
            positions=True,
            transactions=False,
            orders_reconciliation=True,
            background_sync=False,
            requires_static_ip=False,
        )

    def _get(self, path: str) -> Any:
        response = None
        for attempt in range(3):
            _LIMITER.acquire()
            response = self.client.get(
                f"{self.API_URL}{path}",
                headers={"Accept": "application/json", "Authorization": f"Bearer {self.access_token}"},
            )
            if response.status_code != 429:
                break
            retry_after = response.headers.get("Retry-After")
            delay = min(float(retry_after), 5.0) if retry_after and retry_after.replace(".", "", 1).isdigit() else min(0.5 * (2**attempt), 5.0)
            time.sleep(delay)
        assert response is not None
        if response.status_code in {401, 403}:
            raise AuthorizationRequired("Upstox authorization expired or is no longer valid")
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise ConnectorError(f"Upstox rate limit reached; retry after {retry_after} seconds")
        if response.status_code >= 400:
            raise ConnectorError(f"Upstox request failed ({response.status_code})")
        payload = response.json()
        return payload.get("data", payload)

    def get_profile(self) -> dict[str, Any]:
        value = self._get("/v2/user/profile")
        return value if isinstance(value, dict) else {}

    def get_holdings(self) -> list[NormalizedHolding]:
        rows = self._get("/v2/portfolio/long-term-holdings") or []
        holdings: list[NormalizedHolding] = []
        now = datetime.now(timezone.utc)
        for row in rows:
            symbol = str(row.get("trading_symbol") or row.get("tradingsymbol") or "").strip().upper()
            quantity = float(row.get("quantity") or 0)
            if not symbol or quantity <= 0:
                continue
            isin = str(row.get("isin") or "").strip() or None
            provider_id = str(row.get("instrument_token") or isin or symbol)
            holdings.append(
                NormalizedHolding(
                    provider_item_id=provider_id,
                    asset_type="equity",
                    instrument_key=symbol,
                    name=str(row.get("company_name") or symbol),
                    quantity=quantity,
                    average_price=float(row.get("average_price") or 0),
                    exchange=str(row.get("exchange") or "NSE").upper(),
                    isin=isin,
                    source_timestamp=now,
                    raw_payload=dict(row),
                )
            )
        return holdings

    def get_positions(self) -> list[dict[str, Any]]:
        value = self._get("/v2/portfolio/short-term-positions")
        return list(value or [])

    def get_transactions(self, date_from: str, date_to: str) -> list[dict[str, Any]]:
        del date_from, date_to
        return []

    def get_orders(self) -> list[dict[str, Any]]:
        value = self._get("/v2/order/retrieve-all")
        return list(value or [])

    def revoke(self) -> None:
        # Upstox does not expose a general refresh-token lifecycle for the
        # interactive access token. Local deletion is the reliable revocation.
        return None

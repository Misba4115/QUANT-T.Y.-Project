from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from services.connectors import upstox as upstox_module
from services.connectors.base import AuthorizationRequired, ConnectorError
from services.connectors.upstox import UpstoxConnector


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_authorization_url_preserves_redirect_and_state_without_secret():
    url = UpstoxConnector.authorization_url("client id", "https://app.example/callback?a=1", "state/value")
    query = parse_qs(urlparse(url).query)
    assert query == {
        "response_type": ["code"],
        "client_id": ["client id"],
        "redirect_uri": ["https://app.example/callback?a=1"],
        "state": ["state/value"],
    }
    assert "secret" not in url


def test_exchange_code_contract_and_secret_safe_failures():
    captured: list[httpx.Request] = []

    def success(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"access_token": "access", "token_type": "Bearer"})

    payload = UpstoxConnector.exchange_code(
        code="one-time", client_id="client", client_secret="highly-secret",
        redirect_uri="https://app.example/callback", client=_client(success),
    )
    assert payload["access_token"] == "access"
    body = captured[0].content.decode()
    assert "grant_type=authorization_code" in body and "client_secret=highly-secret" in body

    failing = _client(lambda _request: httpx.Response(400, json={"error": "highly-secret"}))
    with pytest.raises(ConnectorError) as error:
        UpstoxConnector.exchange_code(
            code="bad", client_id="client", client_secret="highly-secret",
            redirect_uri="https://app.example/callback", client=failing,
        )
    assert "highly-secret" not in str(error.value)


@pytest.mark.parametrize("status", [401, 403])
def test_expired_or_forbidden_access_requires_reauthorization(status: int, monkeypatch):
    monkeypatch.setattr(upstox_module._LIMITER, "acquire", lambda: None)
    connector = UpstoxConnector("expired", _client(lambda _request: httpx.Response(status, json={})))
    with pytest.raises(AuthorizationRequired):
        connector.get_profile()


def test_rate_limit_retries_are_bounded_and_retry_after_is_reported(monkeypatch):
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, headers={"Retry-After": "2"}, json={})

    monkeypatch.setattr(upstox_module._LIMITER, "acquire", lambda: None)
    sleeps: list[float] = []
    monkeypatch.setattr(upstox_module.time, "sleep", sleeps.append)
    connector = UpstoxConnector("token", _client(handler))
    with pytest.raises(ConnectorError, match="retry after 2 seconds"):
        connector.get_orders()
    assert calls == 3
    assert sleeps == [2.0, 2.0, 2.0]


def test_holdings_normalization_filters_invalid_rows_and_is_read_only(monkeypatch):
    monkeypatch.setattr(upstox_module._LIMITER, "acquire", lambda: None)
    rows = [
        {"instrument_token": "NSE|1", "trading_symbol": " infy ", "company_name": "Infosys", "quantity": "3", "average_price": "1400.50", "exchange": "nse", "isin": "INE009A01021"},
        {"trading_symbol": "", "quantity": 5},
        {"trading_symbol": "TCS", "quantity": 0},
    ]
    connector = UpstoxConnector("token", _client(lambda _request: httpx.Response(200, json={"data": rows})))
    holdings = connector.get_holdings()
    assert len(holdings) == 1
    assert holdings[0].instrument_key == "INFY"
    assert holdings[0].quantity == 3 and holdings[0].average_price == 1400.5
    assert connector.get_capabilities().transactions is False
    assert connector.get_transactions("2026-01-01", "2026-02-01") == []


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (httpx.Response(500, json={}), "request failed"),
        (httpx.Response(200, text="not-json"), "invalid API response"),
    ],
)
def test_api_failures_are_typed_and_do_not_leak_tokens(response, message, monkeypatch):
    monkeypatch.setattr(upstox_module._LIMITER, "acquire", lambda: None)
    connector = UpstoxConnector("private-token", _client(lambda _request: response))
    with pytest.raises(ConnectorError, match=message) as error:
        connector.get_profile()
    assert "private-token" not in str(error.value)

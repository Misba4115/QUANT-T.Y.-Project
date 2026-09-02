"""Lazy Supabase client configuration.

Importing the application must not contact a hosted dependency or fail because a
developer has not yet created `.env`. The proxy also gives tests one explicit
injection point without monkeypatching every router.
"""
from __future__ import annotations

from threading import Lock
from typing import Any

from core.config import get_settings

_client: Any | None = None
_client_lock = Lock()


def get_supabase_client() -> Any:
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    if not settings.database_configured:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in backend/.env."
        )

    with _client_lock:
        if _client is None:
            import httpx
            from supabase import ClientOptions, create_client

            # Disable HTTP/2 multiplexing on Windows to avoid WinError 10035 non-blocking socket aborts in worker threads
            http_client = httpx.Client(http2=False, timeout=httpx.Timeout(60.0))
            options = ClientOptions(httpx_client=http_client, postgrest_client_timeout=60.0)
            _client = create_client(settings.supabase_url, settings.supabase_runtime_key, options=options)
    return _client


def set_supabase_client(client: Any | None) -> None:
    """Inject a fake client in tests, or reset the cached production client."""
    global _client
    _client = client


class _LazySupabaseProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_supabase_client(), name)

    def table(self, name: str) -> Any:
        return get_supabase_client().table(name)

    def rpc(self, name: str, params: dict[str, Any] | None = None) -> Any:
        return get_supabase_client().rpc(name, params or {})


supabase = _LazySupabaseProxy()

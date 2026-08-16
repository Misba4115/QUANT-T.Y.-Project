from __future__ import annotations

import os

import pytest

os.environ.setdefault("QUANT_ENV", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-that-is-long-and-never-used-in-production")
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

from db.supabase_client import set_supabase_client
from tests.fake_supabase import FakeSupabase


@pytest.fixture()
def fake_db():
    client = FakeSupabase()
    set_supabase_client(client)
    yield client
    set_supabase_client(None)

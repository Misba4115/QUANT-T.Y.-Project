"""
DB helper — thin passthrough so all routers can do `Depends(get_db)`.
No async engine, no SQLAlchemy. We use the Supabase Python client directly.
"""
from db.supabase_client import get_supabase_client


def get_db():
    """Yield the Supabase client. Used as a FastAPI dependency."""
    return get_supabase_client()

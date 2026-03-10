"""
DB helper — thin passthrough so all routers can do `Depends(get_db)`.
No async engine, no SQLAlchemy. We use the Supabase Python client directly.
"""
from db.supabase_client import supabase


def get_db():
    """Yield the Supabase client. Used as a FastAPI dependency."""
    return supabase

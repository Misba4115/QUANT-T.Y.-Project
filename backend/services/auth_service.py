"""
Auth Service — register, login, JWT, get_current_user dependency
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db.supabase_client import supabase
from schemas.schemas import RegisterRequest, LoginRequest, TokenResponse

# ── Config ──────────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALG    = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 h

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


# ── Helpers ─────────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(user_id: str) -> str:
    expire  = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


# ── Service functions ────────────────────────────────────────────────────────

def register_user(body: RegisterRequest) -> TokenResponse:
    """Check for duplicate email, hash password, insert user, return JWT."""
    
    # Check if user exists
    result = supabase.table('users').select("*").eq('email', body.email).execute()
    
    if result.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Insert new user
    new_user = supabase.table('users').insert({
        "email": body.email,
        "password_hash": _hash_password(body.password),
        "name": body.name,
        "age": body.age,
        "monthly_income": body.monthly_income,
        "monthly_expenses": body.monthly_expenses,
        "primary_goal": body.primary_goal,
    }).execute()
    
    if not new_user.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    user_id = new_user.data[0]['id']
    return TokenResponse(access_token=_create_token(str(user_id)))


def login_user(body: LoginRequest) -> TokenResponse:
    """Verify email + password and return JWT."""
    
    result = supabase.table('users').select("*").eq('email', body.email).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    user = result.data[0]
    
    if not _verify_password(body.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(access_token=_create_token(str(user['id'])))


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[Any, Any]:
    """Decode the Bearer token and return the authenticated User data.
    
    Use this as a dependency in any endpoint that requires a logged-in user:
        current_user: dict = Depends(get_current_user)
    """
    token = credentials.credentials
    try:
        payload  = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("Missing subject in token")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = supabase.table('users').select("*").eq('id', user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return result.data[0]
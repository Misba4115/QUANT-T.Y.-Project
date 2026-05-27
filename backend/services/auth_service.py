"""
Auth Service — register, login, JWT, get_current_user dependency
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import bcrypt as _bcrypt_lib
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db.supabase_client import supabase
from schemas.schemas import RegisterRequest, LoginRequest, TokenResponse

# ── Config ──────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALG    = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 h

bearer_scheme = HTTPBearer()

# ── Password helpers (using bcrypt directly — passlib is not compatible with bcrypt v4+)
def _hash_password(plain: str) -> str:
    return _bcrypt_lib.hashpw(plain.encode("utf-8"), _bcrypt_lib.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt_lib.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


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

    # Insert new user - match ALL fields from your schema
    new_user = supabase.table('users').insert({
        "email": body.email,
        "password_hash": _hash_password(body.password),
        "name": body.name,
        "phone": body.phone,  # Added
        "age": body.age,
        "monthly_income": body.monthly_income,
        "monthly_expenses": body.monthly_expenses,
        "primary_goal": body.primary_goal,
        "risk_profile": body.risk_profile,  # Added
    }).execute()
    
    if not new_user.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    user_id = str(new_user.data[0]['user_id'])
    return TokenResponse(access_token=_create_token(user_id))


def login_user(body: LoginRequest) -> TokenResponse:
    """Verify email + password and return JWT."""
    
    result = supabase.table('users').select("*").eq('email', body.email).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email address",
        )
    
    user = result.data[0]
    
    if not _verify_password(body.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again.",
        )

    return TokenResponse(access_token=_create_token(str(user['user_id'])))


def google_auth_user(id_token_str: str) -> TokenResponse:
    """Verify Google ID token and login or register the user."""
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests

    try:
        # Verify the Google ID token
        google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        id_info = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            google_client_id,
        )
        email = id_info.get("email")
        name = id_info.get("name", "")
        if not email:
            raise ValueError("No email in Google token")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
        )

    # Check if user exists
    result = supabase.table('users').select("*").eq('email', email).execute()

    if result.data:
        # Existing user — login
        user = result.data[0]
        return TokenResponse(
            access_token=_create_token(str(user['user_id'])),
            is_new_user=False,
        )
    else:
        # New user — register with Google
        new_user = supabase.table('users').insert({
            "email": email,
            "password_hash": "_google_oauth_",  # placeholder — not used for Google users
            "name": name,
            "phone": None,
            "age": 0,
            "monthly_income": 0,
            "monthly_expenses": 0,
            "primary_goal": "",
            "risk_profile": None,
        }).execute()

        if not new_user.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user via Google auth",
            )

        user_id = str(new_user.data[0]['user_id'])
        return TokenResponse(
            access_token=_create_token(user_id),
            is_new_user=True,
        )


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

    result = supabase.table('users').select("*").eq('user_id', user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return result.data[0]
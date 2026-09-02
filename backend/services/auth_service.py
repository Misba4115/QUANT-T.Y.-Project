"""Registration, login, JWT issuance, and authenticated-user dependency."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from core.config import get_settings
from db.postgres import get_db
from schemas.schemas import LoginRequest, RegisterRequest, TokenResponse

bearer_scheme = HTTPBearer(auto_error=False)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _create_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "iat": datetime.now(timezone.utc)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def register_user(body: RegisterRequest, db: Any) -> TokenResponse:
    existing = db.table("users").select("user_id").eq("email", str(body.email).lower()).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    result = db.table("users").insert(
        {
            "email": str(body.email).lower(),
            "password_hash": _hash_password(body.password),
            "name": body.name,
            "phone": body.phone,
            "age": body.age,
            "monthly_income": body.monthly_income,
            "monthly_expenses": body.monthly_expenses,
            "primary_goal": body.primary_goal,
            "risk_profile": body.risk_profile,
        }
    ).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return TokenResponse(access_token=_create_token(str(result.data[0]["user_id"])))


def login_user(body: LoginRequest, db: Any) -> TokenResponse:
    result = db.table("users").select("*").eq("email", str(body.email).lower()).limit(1).execute()
    if not result.data or not _verify_password(body.password, result.data[0].get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=_create_token(str(result.data[0]["user_id"])))


def google_auth_user(id_token_str: str, db: Any) -> TokenResponse:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google authentication is not configured")
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), settings.google_client_id
        )
        email = str(id_info["email"]).lower()
        name = str(id_info.get("name") or "")
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Google token") from exc

    existing = db.table("users").select("*").eq("email", email).limit(1).execute()
    if existing.data:
        return TokenResponse(
            access_token=_create_token(str(existing.data[0]["user_id"])),
            is_new_user=False,
        )

    result = db.table("users").insert(
        {
            "email": email,
            "password_hash": "_google_oauth_",
            "name": name or None,
            "phone": None,
            "age": None,
            "monthly_income": 0,
            "monthly_expenses": 0,
            "primary_goal": None,
            "risk_profile": None,
        }
    ).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create user via Google auth")
    return TokenResponse(
        access_token=_create_token(str(result.data[0]["user_id"])),
        is_new_user=True,
    )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    settings = get_settings()
    token = credentials.credentials if credentials else request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("missing subject")
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = None
    try:
        result = db.table("users").select("*").eq("user_id", user_id).limit(1).execute()
        if result.data:
            user = dict(result.data[0])
            user.pop("password_hash", None)
    except Exception as exc:
        import logging
        logging.warning("User lookup transient error (%s), using token subject fallback", exc)

    if not user:
        user = {"user_id": user_id, "email": payload.get("email", ""), "name": payload.get("name", "User")}
    return user

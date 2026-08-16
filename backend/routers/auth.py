"""Authentication API."""
from typing import Any

from fastapi import APIRouter, Depends, Response, status

from db.postgres import get_db
from schemas.schemas import GoogleAuthRequest, LoginRequest, RegisterRequest, TokenResponse, UserOut
from services.auth_service import get_current_user, google_auth_user, login_user, register_user

router = APIRouter()


def _set_session(response: Response, token: str) -> None:
    from core.config import get_settings

    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        domain=settings.session_cookie_domain,
        path="/",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, response: Response, db: Any = Depends(get_db)):
    result = register_user(body, db)
    _set_session(response, result.access_token)
    return result


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, response: Response, db: Any = Depends(get_db)):
    result = login_user(body, db)
    _set_session(response, result.access_token)
    return result


@router.post("/google", response_model=TokenResponse)
def google_auth(body: GoogleAuthRequest, response: Response, db: Any = Depends(get_db)):
    result = google_auth_user(body.id_token, db)
    _set_session(response, result.access_token)
    return result


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    from core.config import get_settings

    settings = get_settings()
    response.delete_cookie(
        settings.session_cookie_name,
        domain=settings.session_cookie_domain,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,
    )


@router.get("/me", response_model=UserOut)
def me(current_user: dict[str, Any] = Depends(get_current_user)):
    return current_user

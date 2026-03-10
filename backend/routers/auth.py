"""
Auth Router — POST /auth/register, POST /auth/login, GET /auth/me
"""
from fastapi import APIRouter, Depends, status
from typing import Dict, Any

from schemas.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut
from services.auth_service import register_user, login_user, get_current_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    """Register a new user and return a JWT access token."""
    return register_user(body)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """Login with email + password and return a JWT access token."""
    return login_user(body)


@router.get("/me", response_model=UserOut)
def me(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
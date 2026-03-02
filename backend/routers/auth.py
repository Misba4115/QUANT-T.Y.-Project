"""
Auth Router — POST /auth/register, POST /auth/login
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db
# from schemas.auth import RegisterRequest, LoginRequest, TokenResponse
# from services import auth_service  # TODO: implement

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    # body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    Steps:
      1. Check email is not already taken
      2. Hash password with bcrypt
      3. Insert into users table
      4. Return JWT token
    TODO: implement with auth_service.register()
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/login")
async def login(
    # body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login and return a JWT access token.
    Steps:
      1. Fetch user by email
      2. Verify password hash
      3. Create and return JWT token
    TODO: implement with auth_service.login()
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")

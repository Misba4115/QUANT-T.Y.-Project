"""Authenticated user profile API."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from db.postgres import get_db
from schemas.schemas import UserOut, UserProfileUpdate
from services.auth_service import get_current_user

router = APIRouter(prefix="/user")


@router.get("/profile", response_model=UserOut)
def get_profile(current_user: dict[str, Any] = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserOut)
def update_profile(
    body: UserProfileUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    values = body.model_dump(exclude_unset=True, mode="json")
    if not values:
        return current_user
    result = db.table("users").update(values).eq("user_id", current_user["user_id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    user = dict(result.data[0])
    user.pop("password_hash", None)
    return user

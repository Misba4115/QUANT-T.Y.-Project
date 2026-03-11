"""
User Profile Router — GET /user/profile, PUT /user/profile
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from schemas.schemas import UserOut
from services.auth_service import get_current_user
from db.supabase_client import supabase

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/profile", response_model=UserOut)
def get_profile(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """Get current user profile (alias of /auth/me for frontend compatibility)."""
    return current_user


@router.put("/profile", response_model=UserOut)
def update_profile(
    updates: dict,  # name, risk_profile, monthly_income, etc.
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """Update user profile."""
    user_id = current_user['user_id']
    
    # Update in Supabase
    result = supabase.table('users').update(updates).eq('user_id', user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    
    return result.data[0]

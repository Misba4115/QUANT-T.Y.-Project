"""
Goals Router — CRUD /goals
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from schemas.schemas import GoalCreate, GoalOut
from services.auth_service import get_current_user
from db.supabase_client import supabase

router = APIRouter()


@router.get("/", response_model=List[GoalOut])
def list_goals(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """
    List all goals for current user.
    
    Returns empty array if user has no goals.
    """
    user_id = current_user['user_id']
    result = supabase.table('goals').select('*').eq('user_id', user_id).execute()
    return result.data or []


@router.post("/", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    body: GoalCreate,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Create a new financial goal.
    
    Goal types: house, retirement, education, emergency, wealth, custom
    """
    user_id = current_user['user_id']
    
    new_goal = supabase.table('goals').insert({
        "user_id": user_id,
        "goal_name": body.goal_name,
        "goal_type": body.goal_type,
        "target_amount": body.target_amount,
        "current_saved": body.current_saved,
        "target_date": str(body.target_date) if body.target_date else None
    }).execute()
    
    if not new_goal.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create goal"
        )
    
    return new_goal.data[0]


@router.put("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: str,
    updates: dict,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Update a goal.
    
    Can update: goal_name, target_amount, current_saved, target_date
    """
    user_id = current_user['user_id']
    
    result = supabase.table('goals')\
        .update(updates)\
        .eq('goal_id', goal_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return result.data[0]


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Delete a goal.
    
    Only the goal owner can delete their goals.
    """
    user_id = current_user['user_id']
    
    result = supabase.table('goals')\
        .delete()\
        .eq('goal_id', goal_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return None
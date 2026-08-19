"""User-scoped financial-goal CRUD."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from db.postgres import get_db
from repositories.base import SupabaseRepository
from schemas.schemas import GoalCreate, GoalOut, GoalUpdate
from services.auth_service import get_current_user

router = APIRouter()


@router.get("", response_model=list[GoalOut])
def list_goals(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return SupabaseRepository(db).list_for_user("goals", current_user["user_id"])


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    body: GoalCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return SupabaseRepository(db).create_for_user(
        "goals", current_user["user_id"], body.model_dump(mode="json")
    )


@router.put("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: str,
    body: GoalUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    result = SupabaseRepository(db).update_for_user(
        "goals", goal_id, current_user["user_id"], body.model_dump(exclude_unset=True, mode="json")
    )
    if not result:
        raise HTTPException(status_code=404, detail="Goal not found")
    return result


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    if not SupabaseRepository(db).delete_for_user("goals", goal_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Goal not found")
    return None

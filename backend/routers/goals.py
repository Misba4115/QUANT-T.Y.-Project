"""
Goals Router — CRUD /goals
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db

router = APIRouter()


@router.get("/")
async def list_goals(db: AsyncSession = Depends(get_db)):
    """List financial goals for the logged-in user. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/", status_code=201)
async def create_goal(db: AsyncSession = Depends(get_db)):
    """Create a new financial goal. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{goal_id}")
async def update_goal(goal_id: str, db: AsyncSession = Depends(get_db)):
    """Update a goal (name, target amount, target date). TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(goal_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a goal. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")

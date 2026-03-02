"""
Dashboard Router — POST /dashboard/generate, GET /dashboard/result/{run_id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db

router = APIRouter()


@router.post("/generate", status_code=202)
async def generate_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Kick off all 4 agents asynchronously.
    Steps:
      1. Create a dashboard_run record (status='pending')
      2. Run Guardian → Portfolio → Tax → Cashflow agents in LangGraph
      3. Store result in dashboard_runs (status='completed')
      4. Return run_id for polling
    TODO: implement with LangGraph StateGraph
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/result/{run_id}")
async def get_dashboard_result(run_id: str, db: AsyncSession = Depends(get_db)):
    """
    Poll dashboard generation status and retrieve result.
    TODO: implement
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/config")
async def get_dashboard_config(db: AsyncSession = Depends(get_db)):
    """Return the user's saved widget preferences. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/config")
async def save_dashboard_config(db: AsyncSession = Depends(get_db)):
    """Save widget selection + time period preference. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")

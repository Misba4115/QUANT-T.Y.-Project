"""
Dashboard Router — POST /dashboard/generate, GET /dashboard/result/{run_id}
Aggregates user financial data and returns computed dashboard metrics
"""
import time
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.postgres import get_db
from models.models import DashboardRun, User
from schemas.schemas import DashboardRunOut, DashboardGenerateRequest
from services.dashboard_aggregator import DashboardAggregator
from services.auth_service import get_current_user

router = APIRouter()


@router.post("/generate", status_code=200)
async def generate_dashboard(
    request: DashboardGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Generate dashboard for the current user.
    Steps:
      1. Create a dashboard_run record (status='processing')
      2. Aggregate user financial data
      3. Store result in dashboard_runs (status='completed')
      4. Return run_id and result
    """
    try:
        # Get user_id from current_user dict
        user_id_str = current_user.get('user_id')
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        user_id = uuid.UUID(user_id_str)

        # Create dashboard run record with processing status
        run_id = str(uuid.uuid4())
        start_time = time.time()
        
        dashboard_run = DashboardRun(
            id=uuid.UUID(run_id),
            user_id=user_id,
            status="processing",
            params={
                "widgets": request.widgets,
                "time_period": request.time_period
            }
        )
        db.add(dashboard_run)
        await db.flush()

        # Aggregate user financial data
        aggregator = DashboardAggregator(db)
        result = await aggregator.aggregate(user_id)

        # Update dashboard run with result
        processing_time_ms = int((time.time() - start_time) * 1000)
        dashboard_run.status = "completed"
        dashboard_run.result = result
        dashboard_run.processing_time_ms = processing_time_ms
        
        await db.commit()

        return DashboardRunOut(
            run_id=run_id,
            status="completed",
            result=result
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")


@router.get("/result/{run_id}")
async def get_dashboard_result(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Retrieve dashboard generation result by run_id.
    """
    try:
        # Get the dashboard run
        result = await db.execute(
            select(DashboardRun).where(DashboardRun.id == uuid.UUID(run_id))
        )
        dashboard_run = result.scalars().first()
        
        if not dashboard_run:
            raise HTTPException(status_code=404, detail="Dashboard run not found")
        
        # Verify user owns this run
        user_id_str = current_user.get('user_id')
        if user_id_str and dashboard_run.user_id != uuid.UUID(user_id_str):
            raise HTTPException(status_code=403, detail="Unauthorized")

        return DashboardRunOut(
            run_id=run_id,
            status=dashboard_run.status,
            result=dashboard_run.result
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard: {str(e)}")


@router.get("/config")
async def get_dashboard_config(db: AsyncSession = Depends(get_db)):
    """Return the user's saved widget preferences. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/config")
async def save_dashboard_config(db: AsyncSession = Depends(get_db)):
    """Save widget selection + time period preference. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")

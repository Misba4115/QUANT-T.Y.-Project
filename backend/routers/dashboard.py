"""Dashboard generation, retrieval, and user configuration."""
from __future__ import annotations

import time
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from db.postgres import get_db
from repositories.base import SupabaseRepository
from schemas.schemas import (
    DashboardConfigOut,
    DashboardConfigUpdate,
    DashboardGenerateRequest,
    DashboardRunOut,
)
from services.auth_service import get_current_user
from services.dashboard_aggregator import DashboardAggregator
from services.report_export import ReportExportService

router = APIRouter()


class ExportRequest(BaseModel):
    format: str
    time_period: str = "1y"
    date_from: date | None = None
    date_to: date | None = None
    chart: str = "portfolio_history"


@router.post("/generate", response_model=DashboardRunOut)
def generate_dashboard(
    request: DashboardGenerateRequest,
    db: Any = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    run_id = str(uuid4())
    started = time.perf_counter()
    db.table("dashboard_runs").insert(
        {
            "run_id": run_id,
            "user_id": user_id,
            "status": "processing",
            "params": request.model_dump(mode="json"),
        }
    ).execute()
    try:
        result = DashboardAggregator(db).aggregate(
            user_id, request.time_period, request.date_from, request.date_to
        )
        elapsed = int((time.perf_counter() - started) * 1000)
        status = "partial" if result["valuation_status"] != "market_valued" else "completed"
        updated = (
            db.table("dashboard_runs")
            .update(
                {
                    "status": status,
                    "result": result,
                    "processing_time_ms": elapsed,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("run_id", run_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not updated.data:
            raise RuntimeError("Dashboard run could not be persisted")
        return DashboardRunOut(run_id=run_id, status=status, result=result)
    except Exception as exc:
        db.table("dashboard_runs").update(
            {"status": "failed", "error": type(exc).__name__, "completed_at": datetime.now(timezone.utc).isoformat()}
        ).eq("run_id", run_id).eq("user_id", user_id).execute()
        raise HTTPException(status_code=500, detail="Dashboard generation failed") from exc


@router.get("/result/{run_id}", response_model=DashboardRunOut)
def get_dashboard_result(
    run_id: str,
    db: Any = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    row = SupabaseRepository(db).get_for_user("dashboard_runs", run_id, current_user["user_id"])
    if not row:
        raise HTTPException(status_code=404, detail="Dashboard run not found")
    return DashboardRunOut(
        run_id=run_id,
        status=row["status"],
        result=row.get("result"),
        error=row.get("error"),
    )


@router.get("/config", response_model=DashboardConfigOut)
def get_dashboard_config(
    db: Any = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    rows = SupabaseRepository(db).list_for_user("dashboard_configs", current_user["user_id"], limit=1)
    if rows:
        return rows[0]
    return DashboardConfigOut(
        user_id=current_user["user_id"],
        widgets=["net_worth", "asset_allocation", "portfolio_performance", "cashflow", "top_holdings", "alerts"],
        time_period="1y",
        chart_preferences={"portfolio_history": "line", "asset_allocation": "donut"},
        currency="INR",
    )


@router.put("/config", response_model=DashboardConfigOut)
def save_dashboard_config(
    body: DashboardConfigUpdate,
    db: Any = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    existing = SupabaseRepository(db).list_for_user("dashboard_configs", user_id, limit=1)
    payload = {**body.model_dump(mode="json"), "updated_at": datetime.now(timezone.utc).isoformat()}
    if existing:
        result = db.table("dashboard_configs").update(payload).eq("user_id", user_id).execute()
    else:
        result = db.table("dashboard_configs").insert({**payload, "user_id": user_id}).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Dashboard configuration could not be saved")
    return result.data[0]


@router.post("/exports")
def request_export(
    body: ExportRequest,
    db: Any = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    if body.format not in {"pdf", "png"}:
        raise HTTPException(status_code=422, detail="Export format must be pdf or png")
    if body.chart != "portfolio_history":
        raise HTTPException(status_code=422, detail="Only portfolio_history chart export is supported")
    return ReportExportService(db).request(
        current_user["user_id"], format=body.format, params=body.model_dump()
    )


@router.get("/exports/{export_id}/download")
def download_export(
    export_id: str,
    token: str = Query(min_length=20),
    db: Any = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    try:
        filename, media_type, content = ReportExportService(db).render(
            current_user["user_id"], export_id, token
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
    )

"""Read-only broker connection and synchronization endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from core.config import get_settings
from db.postgres import get_db
from services.auth_service import get_current_user
from services.connectors.base import AuthorizationRequired, ConnectorError
from services.connectors.service import ConnectorService

router = APIRouter()


class SandboxAccountRequest(BaseModel):
    holdings: list[dict[str, Any]] = Field(default_factory=list, max_length=100)


def _service(db: Any) -> ConnectorService:
    return ConnectorService(db)


@router.get("")
def list_connections(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _service(db).list_accounts(current_user["user_id"])


@router.post("/upstox/authorize")
def authorize_upstox(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    try:
        return _service(db).begin_upstox_authorization(current_user["user_id"])
    except ConnectorError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/upstox/callback")
def upstox_callback(code: str = Query(min_length=1), state: str = Query(min_length=16), db: Any = Depends(get_db)):
    try:
        _user_id, account = _service(db).complete_upstox_authorization(code, state)
    except ConnectorError as exc:
        return RedirectResponse(f"{get_settings().public_app_url}/settings?connector=upstox&status=error", status_code=303)
    return RedirectResponse(
        f"{get_settings().public_app_url}/settings?connector=upstox&status={account['status']}", status_code=303
    )


@router.post("/sandbox")
def create_sandbox(
    body: SandboxAccountRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    try:
        return _service(db).create_sandbox_account(current_user["user_id"], body.holdings)
    except ConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{connector_account_id}/sync/preview")
def preview_sync(
    connector_account_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    try:
        return _service(db).preview_sync(connector_account_id, current_user["user_id"])
    except AuthorizationRequired as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sync/{connector_sync_run_id}/commit")
def commit_sync(
    connector_sync_run_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    try:
        return _service(db).commit_sync(connector_sync_run_id, current_user["user_id"])
    except ConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{connector_account_id}", status_code=204)
def revoke(
    connector_account_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    try:
        _service(db).revoke(connector_account_id, current_user["user_id"])
    except ConnectorError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

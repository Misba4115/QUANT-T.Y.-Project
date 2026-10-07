"""Unified preview/confirm financial import API."""
import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from db.postgres import get_db
from schemas.schemas import ImportCommitRequest
from services.auth_service import get_current_user
from services.import_service import (
    commit_import,
    delete_import_preview,
    get_import,
    list_imports,
    normalized_csv_export,
    preview_import,
)

router = APIRouter()


@router.get("/capabilities")
def parser_capabilities():
    from services.parsers.registry import parser_capability_matrix
    return parser_capability_matrix()


@router.get("")
def history(
    limit: int = 50,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return list_imports(current_user["user_id"], db, limit)


@router.post("/preview")
async def preview(
    file: UploadFile = File(...),
    target_type: str | None = Form(default=None),
    column_mapping: str | None = Form(default=None),
    file_mode: str | None = Form(default=None),
    account_id: str | None = Form(default=None),
    statement_frequency: str | None = Form(default=None),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    parsed_mapping: dict[str, str] | None = None
    if file_mode not in {None, "holdings_snapshot", "investment_history", "bank_transactions"}:
        raise HTTPException(status_code=422, detail="Unsupported file clarification")
    if column_mapping:
        try:
            candidate = json.loads(column_mapping)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="Column mapping must be valid JSON") from exc
        if not isinstance(candidate, dict) or len(candidate) > 100 or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in candidate.items()
        ):
            raise HTTPException(status_code=422, detail="Column mapping must contain at most 100 source-to-field pairs")
        parsed_mapping = candidate
    return await preview_import(
        file,
        current_user["user_id"],
        db,
        target_override=target_type,
        mapping_override=parsed_mapping,
        file_mode=file_mode,
        account_id=account_id,
        statement_frequency=statement_frequency,
    )


@router.post("/{import_batch_id}/commit")
def commit(
    import_batch_id: str,
    body: ImportCommitRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return commit_import(import_batch_id, current_user["user_id"], db, body.column_mapping)


@router.get("/{import_batch_id}")
def status_result(
    import_batch_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return get_import(import_batch_id, current_user["user_id"], db)


@router.get("/{import_batch_id}/normalized.csv")
def download_normalized(
    import_batch_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    filename, content = normalized_csv_export(import_batch_id, current_user["user_id"], db)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, no-store",
        },
    )


@router.delete("/{import_batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preview(
    import_batch_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    delete_import_preview(import_batch_id, current_user["user_id"], db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

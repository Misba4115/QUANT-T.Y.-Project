"""Two-step, user-scoped, idempotent financial-file ingestion."""
from __future__ import annotations

import hashlib
import csv
import io
import json
import logging
import re
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError

from core.config import get_settings
from repositories.base import SupabaseRepository
from services.file_parser import PARSER_VERSION, analyze_financial_file, mapping_diagnostics, normalize_row
from services.import_mapping_service import suggest_import_mapping

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".pdf"}

EXPORT_COLUMNS = {
    "equity_holdings": ["symbol", "equity_name", "exchange", "quantity", "avg_price", "current_price", "broker", "demat_account", "price_source"],
    "mutual_fund_holdings": ["mf_name", "scheme_code", "isin", "fund_house", "category", "units", "avg_nav", "current_nav", "platform", "folio_number", "price_source"],
    "etf_holdings": ["symbol", "etf_name", "isin", "exchange", "category", "quantity", "avg_price", "current_price", "broker", "demat_account", "price_source"],
    "crypto_holdings": ["symbol", "crypto_name", "network", "quantity", "avg_price", "current_price", "exchange", "wallet_address", "price_source"],
    "bank_transactions": ["account_id", "tx_date", "description", "amount", "tx_type", "category"],
    "mixed_asset_transactions": ["asset_type", "tx_date", "tx_type", "symbol", "mf_name", "scheme_code", "quantity", "units", "price", "nav", "fees", "source"],
}


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_filename(filename: str | None) -> str:
    name = Path(filename or "upload").name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name[:240]


def _error_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "; ".join(
            f"{'.'.join(str(item) for item in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
    return str(exc)


async def preview_import(
    file: UploadFile,
    user_id: str,
    db: Any,
    target_override: str | None = None,
    mapping_override: dict[str, str] | None = None,
    file_mode: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    filename = _safe_filename(file.filename)
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only CSV, XLSX, and text-based CAS PDF files are supported")
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_bytes} bytes")
    if not content:
        raise HTTPException(status_code=422, detail="The uploaded file is empty")

    content_hash = hashlib.sha256(content).hexdigest()
    repo = SupabaseRepository(db)
    try:
        existing = repo.find(
            "import_batches",
            [("user_id", user_id), ("content_hash", content_hash), ("parser_version", PARSER_VERSION)],
            limit=1,
        )
    except Exception as exc:
        if "import_batches" in str(exc) and "PGRST205" in str(exc):
            raise HTTPException(
                status_code=503,
                detail="The import database tables are not installed. Review and apply the recovery-services migration in Supabase before importing files.",
            ) from exc
        raise
    if existing:
        return _batch_response(existing[0], duplicate=True)

    try:
        parsed = analyze_financial_file(filename, content, target_override, mapping_override)
    except ValueError as exc:
        diagnostics = mapping_diagnostics(filename, content) if not target_override else None
        if diagnostics:
            suggestion = suggest_import_mapping(diagnostics["source_columns"], filename, content, file_mode)
            if suggestion:
                try:
                    parsed = analyze_financial_file(
                        filename,
                        content,
                        suggestion["target_type"],
                        suggestion["column_mapping"],
                    )
                    parsed = replace(parsed, mapping_method="llm_headers")
                except ValueError:
                    diagnostics["reason"] = str(exc)
                    raise HTTPException(status_code=422, detail=diagnostics) from exc
            else:
                diagnostics["reason"] = str(exc)
                raise HTTPException(status_code=422, detail=diagnostics) from exc
        else:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    target, raw_rows = parsed.target, parsed.rows
    if len(raw_rows) > settings.max_import_rows:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_import_rows}-row limit")

    preview_rows: list[dict[str, Any]] = []
    row_errors: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rows, start=2):
        try:
            normalized = normalize_row(target, raw)
            fingerprint = _canonical_hash({"target": target, "row": normalized})
            preview_rows.append({**normalized, "_row_number": index, "_row_hash": fingerprint})
        except (ValidationError, ValueError, TypeError) as exc:
            row_errors.append(
                {
                    "row_number": index,
                    "code": "invalid_row",
                    "message": _error_message(exc),
                    "raw_row": raw,
                }
            )

    if not preview_rows:
        raise HTTPException(
            status_code=422,
            detail={"message": "No valid rows were found", "row_errors": row_errors[:20]},
        )

    result = db.table("import_batches").insert(
        {
            "user_id": user_id,
            "filename": filename,
            "content_hash": content_hash,
            "source_type": extension.removeprefix("."),
            "target_type": target,
            "parser_version": PARSER_VERSION,
            "status": "pending",
            "preview_rows": preview_rows,
            "column_mapping": {
                "source_to_canonical": parsed.source_to_canonical,
                "recognized_columns": parsed.recognized_columns,
                "ignored_columns": parsed.ignored_columns,
                "method": parsed.mapping_method,
            },
            "valid_count": len(preview_rows),
            "error_count": len(row_errors),
            "committed_count": 0,
        }
    ).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Import preview could not be persisted")
    batch = result.data[0]
    if row_errors:
        db.table("import_row_errors").insert(
            [{**error, "import_batch_id": batch["import_batch_id"]} for error in row_errors]
        ).execute()
    response = _batch_response(batch)
    response["row_errors"] = row_errors
    return response


def _resolve_account_reference(value: str | None, user_id: str, repo: SupabaseRepository) -> str | None:
    if not value:
        return None
    accounts = repo.list_for_user("banking_accounts", user_id)
    for account in accounts:
        if value in {str(account.get("account_id")), str(account.get("account_type")), str(account.get("account_name"))}:
            return str(account["account_id"])
    raise ValueError(f"No owned bank account matches '{value}'")


def commit_import(import_batch_id: str, user_id: str, db: Any, column_mapping: dict[str, str] | None = None) -> dict[str, Any]:
    repo = SupabaseRepository(db)
    batch = repo.get_for_user("import_batches", import_batch_id, user_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    if batch["status"] == "completed":
        return _batch_response(batch, duplicate=True)

    target = batch.get("target_type")
    if target not in {
        "equity_holdings", "mutual_fund_holdings",
        "etf_holdings", "crypto_holdings", "bank_transactions",
        "mixed_asset_transactions",
        "equity_transactions", "mf_transactions", "etf_transactions", "crypto_transactions",
    }:
        raise HTTPException(status_code=422, detail="Import target is not commit-capable")

    mapping_metadata = dict(batch.get("column_mapping") or {})
    if column_mapping:
        mapping_metadata["user_overrides"] = column_mapping
    db.table("import_batches").update(
        {"status": "processing", "column_mapping": mapping_metadata}
    ).eq("import_batch_id", import_batch_id).eq("user_id", user_id).execute()

    # A retry supersedes commit-time errors from the previous attempt. Preview
    # validation errors use a different code and remain part of the audit trail.
    previous_commit_errors = (
        db.table("import_row_errors").select("import_row_error_id").eq(
            "import_batch_id", import_batch_id
        ).eq("code", "commit_failed").execute().data
        or []
    )
    db.table("import_row_errors").delete().eq("import_batch_id", import_batch_id).eq(
        "code", "commit_failed"
    ).execute()

    committed = 0
    errors: list[dict[str, Any]] = []
    for row in batch.get("preview_rows") or []:
        row_target = str(row.get("_target_table")) if target == "mixed_asset_transactions" else target
        payload = {key: value for key, value in row.items() if not key.startswith("_")}
        fingerprint = row["_row_hash"]
        try:
            if row_target == "bank_transactions":
                payload["account_id"] = _resolve_account_reference(payload.get("account_id"), user_id, repo)
            if row_target in {"equity_transactions", "mf_transactions", "etf_transactions", "crypto_transactions"}:
                payload.pop("asset_type", None)
                if row_target != "mf_transactions":
                    payload["amount"] = float(payload["quantity"]) * float(payload["price"])
                    payload["charges"] = payload.get("fees", 0)
            existing = repo.find(row_target, [("user_id", user_id), ("source_row_hash", fingerprint)], limit=1)
            if not existing:
                payload.update(
                    {
                        "user_id": user_id,
                        "import_batch_id": import_batch_id,
                        "source_row_hash": fingerprint,
                        "source": "file_import" if row_target == "bank_transactions" else payload.get("source"),
                    }
                )
                if row_target not in {"bank_transactions", "equity_transactions", "mf_transactions", "etf_transactions", "crypto_transactions"}:
                    payload.pop("source", None)
                result = db.table(row_target).insert(payload).execute()
                if not result.data:
                    raise RuntimeError("database returned no inserted row")
            # Count all rows belonging to this batch that are now persisted,
            # including rows recovered idempotently after a prior partial save.
            committed += 1
        except Exception as exc:
            errors.append(
                {
                    "row_number": row.get("_row_number", 0),
                    "code": "commit_failed",
                    "message": _error_message(exc),
                    "raw_row": payload,
                }
            )
            continue

        # Guardian is a derived monitoring stream. Its availability must not
        # change the truth of whether the user's financial row was saved.
        try:
            from services.guardian_stream import GuardianStreamService

            asset_map = {
                "bank_transactions": "bank", "equity_transactions": "equity",
                "mf_transactions": "mutual_fund", "etf_transactions": "etf",
                "crypto_transactions": "crypto", "equity_holdings": "equity",
                "mutual_fund_holdings": "mutual_fund", "etf_holdings": "etf",
                "crypto_holdings": "crypto",
            }
            occurred_raw = payload.get("tx_date") or payload.get("source_timestamp")
            occurred_at = datetime.now(timezone.utc)
            if occurred_raw:
                try:
                    occurred_at = datetime.fromisoformat(str(occurred_raw).replace("Z", "+00:00"))
                    if occurred_at.tzinfo is None:
                        occurred_at = occurred_at.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            amount = payload.get("amount")
            if amount is None:
                quantity = payload.get("quantity") or payload.get("units") or 0
                price = payload.get("price") or payload.get("nav") or payload.get("avg_price") or payload.get("avg_nav") or 0
                amount = float(quantity) * float(price)
            GuardianStreamService(db).ingest(
                user_id=user_id, event_id=f"import:{import_batch_id}:{fingerprint}",
                asset_type=asset_map.get(row_target, "bank"),
                event_type="imported_record", occurred_at=occurred_at,
                payload={"amount": amount, "quantity": payload.get("quantity") or payload.get("units"), "source": "file_import"},
                enqueue=False,
            )
        except Exception as exc:
            logger.warning(
                "Financial import row persisted but Guardian event was not recorded "
                "(batch=%s row=%s): %s",
                import_batch_id,
                row.get("_row_number", 0),
                _error_message(exc),
            )

    if errors:
        db.table("import_row_errors").insert(
            [{**error, "import_batch_id": import_batch_id} for error in errors]
        ).execute()
    if committed:
        try:
            from services.jobs import JobService

            JobService(db).enqueue_once("guardian_events", user_id, {"import_batch_id": import_batch_id})
        except Exception as exc:
            logger.warning(
                "Import completed but Guardian processing could not be queued (batch=%s): %s",
                import_batch_id,
                _error_message(exc),
            )
    total_prior_errors = max(
        0,
        int(batch.get("error_count") or 0) - len(previous_commit_errors),
    )
    status = "completed" if not errors and total_prior_errors == 0 else "partial"
    if committed == 0 and errors:
        status = "failed"
    updated = db.table("import_batches").update(
        {
            "status": status,
            "committed_count": committed,
            "error_count": total_prior_errors + len(errors),
            "error_message": errors[0]["message"] if status == "failed" else None,
        }
    ).eq("import_batch_id", import_batch_id).eq("user_id", user_id).execute()
    if not updated.data:
        raise HTTPException(status_code=500, detail="Import result could not be persisted")
    response = _batch_response(updated.data[0])
    response["row_errors"] = errors
    return response


def get_import(import_batch_id: str, user_id: str, db: Any) -> dict[str, Any]:
    batch = SupabaseRepository(db).get_for_user("import_batches", import_batch_id, user_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    response = _batch_response(batch)
    response["row_errors"] = (
        db.table("import_row_errors")
        .select("*")
        .eq("import_batch_id", import_batch_id)
        .order("row_number")
        .execute()
        .data
        or []
    )
    return response


def list_imports(user_id: str, db: Any, limit: int = 50) -> list[dict[str, Any]]:
    """Return a lightweight, newest-first library of the user's imports."""
    rows = SupabaseRepository(db).list_for_user(
        "import_batches",
        user_id,
        order_by="created_at",
        descending=True,
        limit=max(1, min(limit, 100)),
    )
    results: list[dict[str, Any]] = []
    for row in rows:
        item = _batch_response(row)
        # Full normalized rows are fetched only when the user opens an import.
        item["preview_rows"] = []
        results.append(item)
    return results


def delete_import_preview(import_batch_id: str, user_id: str, db: Any) -> None:
    repo = SupabaseRepository(db)
    batch = repo.get_for_user("import_batches", import_batch_id, user_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    if not repo.delete_for_user("import_batches", import_batch_id, user_id):
        raise HTTPException(status_code=500, detail="Import preview could not be deleted")


def normalized_csv_export(import_batch_id: str, user_id: str, db: Any) -> tuple[str, bytes]:
    """Render the user-owned normalized preview as a spreadsheet-safe CSV."""
    batch = SupabaseRepository(db).get_for_user("import_batches", import_batch_id, user_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    target = str(batch.get("target_type") or "")
    rows = batch.get("preview_rows") or []
    if target not in EXPORT_COLUMNS or not rows:
        raise HTTPException(status_code=422, detail="This import has no normalized rows to download")

    populated = {key for row in rows for key, value in row.items() if not key.startswith("_") and value is not None}
    columns = [key for key in EXPORT_COLUMNS[target] if key in populated]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _spreadsheet_safe(row.get(key)) for key in columns})

    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(str(batch["filename"])).stem).strip("-.") or "quant-import"
    return f"{stem}-normalized.csv", output.getvalue().encode("utf-8-sig")


def _spreadsheet_safe(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def _batch_response(batch: dict[str, Any], duplicate: bool = False) -> dict[str, Any]:
    return {
        "import_batch_id": batch["import_batch_id"],
        "filename": batch["filename"],
        "target_type": batch.get("target_type"),
        "status": batch["status"],
        "preview_rows": batch.get("preview_rows") or [],
        "valid_count": int(batch.get("valid_count") or 0),
        "error_count": int(batch.get("error_count") or 0),
        "committed_count": int(batch.get("committed_count") or 0),
        "parser_version": batch["parser_version"],
        "column_mapping": batch.get("column_mapping") or {},
        "duplicate": duplicate,
        "error_message": batch.get("error_message"),
        "created_at": batch.get("created_at"),
        "updated_at": batch.get("updated_at"),
    }

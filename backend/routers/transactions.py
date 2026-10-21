"""User-scoped bank and investment transaction APIs."""
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from db.postgres import get_db
from repositories.base import SupabaseRepository
from schemas.schemas import AssetTransactionCreate, BankTransactionCreate, BankTransactionOut
from services.auth_service import get_current_user

router = APIRouter()
ASSET_TABLES = {
    "equity": ("equity_transactions", "equity_tx_id"),
    "mf": ("mf_transactions", "mf_tx_id"),
    "etf": ("etf_transactions", "etf_tx_id"),
    "crypto": ("crypto_transactions", "crypto_tx_id"),
}


@router.get("/bank", response_model=list[BankTransactionOut])
def list_bank_transactions(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return SupabaseRepository(db).list_for_user(
        "bank_transactions", current_user["user_id"], order_by="tx_date", descending=True
    )


@router.post("/bank", response_model=BankTransactionOut, status_code=status.HTTP_201_CREATED)
def create_bank_transaction(
    body: BankTransactionCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    repo = SupabaseRepository(db)
    user_id = current_user["user_id"]
    if body.account_id and not repo.get_for_user("banking_accounts", body.account_id, user_id):
        raise HTTPException(status_code=422, detail="account_id does not belong to the authenticated user")
    payload = body.model_dump(mode="json", exclude_none=True)
    if body.occurred_at is not None:
        payload["occurred_local_hour"] = body.occurred_at.hour
    created = repo.create_for_user("bank_transactions", user_id, payload)
    from services.guardian_stream import GuardianStreamService

    GuardianStreamService(db).ingest(
        user_id=user_id,
        event_id=f"bank-transaction:{created['bank_tx_id']}",
        asset_type="bank",
        event_type="transaction_created",
        occurred_at=(datetime.fromisoformat(str(created["occurred_at"]).replace("Z", "+00:00"))
                     if created.get("occurred_at") else datetime.fromisoformat(str(created["tx_date"])).replace(tzinfo=timezone.utc)),
        payload={"amount": created["amount"], "tx_type": created["tx_type"], "category": created.get("category")},
    )
    return created


@router.delete("/bank/{bank_tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank_transaction(
    bank_tx_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    if not SupabaseRepository(db).delete_for_user("bank_transactions", bank_tx_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Transaction not found")


def _asset_table(asset_type: str) -> str:
    if asset_type not in ASSET_TABLES:
        raise HTTPException(status_code=404, detail="Unsupported asset transaction type")
    return ASSET_TABLES[asset_type][0]


@router.get("/{asset_type}")
def list_asset_transactions(
    asset_type: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return SupabaseRepository(db).list_for_user(
        _asset_table(asset_type), current_user["user_id"], order_by="tx_date", descending=True
    )


@router.post("/{asset_type}", status_code=status.HTTP_201_CREATED)
def create_asset_transaction(
    asset_type: str,
    body: AssetTransactionCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    table = _asset_table(asset_type)
    payload = body.model_dump(exclude_none=True, mode="json")
    if asset_type == "mf":
        if not payload.get("mf_name") or not payload.get("units") or payload.get("nav") is None:
            raise HTTPException(status_code=422, detail="Mutual-fund transactions require mf_name, units, and nav")
        payload.pop("symbol", None)
        payload.pop("quantity", None)
        payload.pop("price", None)
        payload.pop("fees", None)
    else:
        if not payload.get("symbol") or not payload.get("quantity") or payload.get("price") is None:
            raise HTTPException(status_code=422, detail=f"{asset_type} transactions require symbol, quantity, and price")
        payload.pop("mf_name", None)
        payload.pop("scheme_code", None)
        payload.pop("units", None)
        payload.pop("nav", None)
        # Preserve compatibility with the hosted legacy schema, where amount is
        # required alongside the canonical quantity/price fields.
        payload["amount"] = float(payload["quantity"]) * float(payload["price"])
        payload["charges"] = payload.get("fees", 0)
    created = SupabaseRepository(db).create_for_user(table, current_user["user_id"], payload)
    from services.guardian_stream import GuardianStreamService

    amount = float(payload.get("amount") or (float(payload.get("units") or 0) * float(payload.get("nav") or 0)))
    GuardianStreamService(db).ingest(
        user_id=current_user["user_id"],
        event_id=f"{asset_type}-transaction:{created[ASSET_TABLES[asset_type][1]]}",
        asset_type="mutual_fund" if asset_type == "mf" else asset_type,
        event_type="transaction_created",
        occurred_at=datetime.fromisoformat(str(created["tx_date"])).replace(tzinfo=timezone.utc),
        payload={"amount": amount, "quantity": payload.get("quantity") or payload.get("units"), "tx_type": payload.get("tx_type")},
    )
    return created


@router.delete("/{asset_type}/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_transaction(
    asset_type: str,
    tx_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    if not SupabaseRepository(db).delete_for_user(_asset_table(asset_type), tx_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Transaction not found")

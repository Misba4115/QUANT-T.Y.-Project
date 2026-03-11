"""
Transactions Router — CRUD for bank_transactions table
Also handles unsupported asset types (equity/mf/etf/crypto) with 400.
"""
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from schemas.schemas import BankTransactionCreate, BankTransactionOut
from services.auth_service import get_current_user
from db.supabase_client import supabase

router = APIRouter()


# ── Bank Transactions ─────────────────────────────────────────────────────────

@router.get("/bank", response_model=List[BankTransactionOut])
def list_bank_transactions(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """List all bank transactions for the current user, newest first."""
    user_id = current_user["user_id"]
    result = (
        supabase.table("bank_transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("tx_date", desc=True)
        .execute()
    )
    return result.data or []


@router.post("/bank", response_model=BankTransactionOut, status_code=status.HTTP_201_CREATED)
def create_bank_transaction(
    body: BankTransactionCreate,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Record a new bank transaction (debit or credit)."""
    if body.tx_type not in ("debit", "credit"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tx_type must be 'debit' or 'credit'",
        )

    user_id = current_user["user_id"]
    new = supabase.table("bank_transactions").insert({
        "user_id": user_id,
        "account_id": body.account_id,
        "tx_date": body.tx_date,
        "description": body.description,
        "amount": body.amount,
        "tx_type": body.tx_type,
        "category": body.category,
    }).execute()

    if not new.data:
        raise HTTPException(status_code=500, detail="Failed to create transaction")

    return new.data[0]


@router.delete("/bank/{bank_tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank_transaction(
    bank_tx_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Delete a bank transaction (ownership enforced)."""
    user_id = current_user["user_id"]
    result = (
        supabase.table("bank_transactions")
        .delete()
        .eq("bank_tx_id", bank_tx_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return None


# ── Unsupported asset types ───────────────────────────────────────────────────
# equity/mf/etf/crypto transaction tracking is not yet implemented.
# These catch-all routes prevent 404s and clearly communicate the limitation.

@router.get("/{asset_type}")
def get_transactions_unsupported(asset_type: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Transaction tracking for '{asset_type}' is not yet implemented. Only 'bank' is supported.",
    )


@router.post("/{asset_type}", status_code=201)
def create_transaction_unsupported(asset_type: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Transaction tracking for '{asset_type}' is not yet implemented. Only 'bank' is supported.",
    )


@router.delete("/{asset_type}/{tx_id}", status_code=204)
def delete_transaction_unsupported(asset_type: str, tx_id: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Transaction tracking for '{asset_type}' is not yet implemented. Only 'bank' is supported.",
    )
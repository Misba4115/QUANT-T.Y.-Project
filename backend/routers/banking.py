"""User-scoped banking account CRUD."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from db.postgres import get_db
from repositories.base import SupabaseRepository
from schemas.schemas import BankingAccountCreate, BankingAccountOut, BankingAccountUpdate
from services.auth_service import get_current_user

router = APIRouter()


@router.get("", response_model=list[BankingAccountOut])
def list_accounts(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return SupabaseRepository(db).list_for_user("banking_accounts", current_user["user_id"])


@router.post("", response_model=BankingAccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    body: BankingAccountCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return SupabaseRepository(db).create_for_user(
        "banking_accounts", current_user["user_id"], body.model_dump(mode="json")
    )


@router.put("/{account_id}", response_model=BankingAccountOut)
def update_account(
    account_id: str,
    body: BankingAccountUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    result = SupabaseRepository(db).update_for_user(
        "banking_accounts",
        account_id,
        current_user["user_id"],
        body.model_dump(exclude_unset=True, mode="json"),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    if not SupabaseRepository(db).delete_for_user("banking_accounts", account_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Account not found")
    return None

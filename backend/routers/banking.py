"""
Banking Router — CRUD /banking-accounts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db
# from schemas.banking import BankingAccountCreate, BankingAccountOut
# from services import banking_service  # TODO: implement

router = APIRouter()


@router.get("/")
async def list_banking_accounts(
    # current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all banking accounts for the logged-in user. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/", status_code=201)
async def create_banking_account(
    # body: BankingAccountCreate,
    # current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new banking account entry. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{account_id}")
async def update_banking_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing banking account. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{account_id}", status_code=204)
async def delete_banking_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a banking account. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")

"""
Transactions Router — CRUD + CSV upload for all transaction tables
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db

router = APIRouter()


@router.get("/{asset_type}")
async def list_transactions(
    asset_type: str,   # 'equity' | 'mf' | 'etf' | 'crypto' | 'bank'
    db: AsyncSession = Depends(get_db),
):
    """
    List transactions for a given asset type.
    asset_type must be one of: equity, mf, etf, crypto, bank
    TODO: implement
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{asset_type}", status_code=201)
async def create_transaction(
    asset_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Add a single transaction. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/bank/upload-csv", status_code=201)
async def upload_bank_statement(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload bank statement CSV.
    Calls statement_parser → auto-categorise transactions → store in bank_transactions.
    TODO: implement
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{asset_type}/{tx_id}", status_code=204)
async def delete_transaction(
    asset_type: str,
    tx_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a transaction. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")

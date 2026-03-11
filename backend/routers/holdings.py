"""
Holdings Router — CRUD /holdings/{equity|mf|etf|crypto}

Endpoints:
  Equity        GET /holdings/equity            list
                POST /holdings/equity           create
                DELETE /holdings/equity/{id}    remove
                POST /holdings/equity/upload-csv  CSV parse preview (no DB insert)

  Mutual Fund   GET /holdings/mf
                POST /holdings/mf
                DELETE /holdings/mf/{id}
                POST /holdings/mf/upload-cas      CAS parse preview (no DB insert)

  ETF           GET /holdings/etf
                POST /holdings/etf
                DELETE /holdings/etf/{id}

  Crypto        GET /holdings/crypto
                POST /holdings/crypto
                DELETE /holdings/crypto/{id}
"""
import io
import csv
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from schemas.schemas import (
    EquityCreate, EquityOut,
    MutualFundCreate, MutualFundOut,
    ETFCreate, ETFOut,
    CryptoCreate, CryptoOut,
)
from services.auth_service import get_current_user
from db.supabase_client import supabase

router = APIRouter()


# ── Equity ────────────────────────────────────────────────────────────────────

@router.get("/equity", response_model=List[EquityOut])
def list_equity(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """List all equity holdings for the current user."""
    user_id = current_user["user_id"]
    result = supabase.table("equity_holdings").select("*").eq("user_id", user_id).execute()
    return result.data or []


@router.post("/equity", response_model=EquityOut, status_code=status.HTTP_201_CREATED)
def create_equity(
    body: EquityCreate,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Add a new equity holding manually."""
    user_id = current_user["user_id"]
    new = supabase.table("equity_holdings").insert({
        "user_id": user_id,
        "symbol": body.symbol,
        "equity_name": body.equity_name,
        "exchange": body.exchange,
        "quantity": body.quantity,
        "avg_price": body.avg_price,
        "broker": body.broker,
        "demat_account": body.demat_account,
    }).execute()

    if not new.data:
        raise HTTPException(status_code=500, detail="Failed to create equity holding")

    return new.data[0]


@router.post("/equity/upload-csv")
async def upload_equity_csv(
    file: UploadFile = File(...),
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """
    Parse-only CSV upload (Zerodha / Upstox format).
    Returns a preview of rows — NO database insertion.
    Expected columns: symbol, equity_name, exchange, quantity, avg_price
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    text = content.decode("utf-8-sig")          # handle BOM
    reader = csv.DictReader(io.StringIO(text))

    required = {"symbol", "quantity", "avg_price"}
    rows = []
    for i, row in enumerate(reader):
        keys = {k.strip().lower() for k in row.keys()}
        if i == 0 and not required.issubset(keys):
            raise HTTPException(
                status_code=422,
                detail=f"CSV must have columns: {required}. Found: {keys}",
            )
        rows.append({k.strip().lower(): v.strip() for k, v in row.items()})

    return {"preview": rows, "row_count": len(rows), "inserted": False}


@router.delete("/equity/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equity(
    holding_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Delete an equity holding (ownership enforced)."""
    user_id = current_user["user_id"]
    result = supabase.table("equity_holdings") \
        .delete() \
        .eq("equity_holding_id", holding_id) \
        .eq("user_id", user_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Equity holding not found")
    return None


# ── Mutual Funds ──────────────────────────────────────────────────────────────

@router.get("/mf", response_model=List[MutualFundOut])
def list_mf(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """List all mutual fund holdings for the current user."""
    user_id = current_user["user_id"]
    result = supabase.table("mutual_fund_holdings").select("*").eq("user_id", user_id).execute()
    return result.data or []


@router.post("/mf", response_model=MutualFundOut, status_code=status.HTTP_201_CREATED)
def create_mf(
    body: MutualFundCreate,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Add a mutual fund holding manually."""
    user_id = current_user["user_id"]
    new = supabase.table("mutual_fund_holdings").insert({
        "user_id": user_id,
        "mf_name": body.mf_name,
        "scheme_code": body.scheme_code,
        "isin": body.isin,
        "fund_house": body.fund_house,
        "category": body.category,
        "units": body.units,
        "avg_nav": body.avg_nav,
        "platform": body.platform,
        "folio_number": body.folio_number,
    }).execute()

    if not new.data:
        raise HTTPException(status_code=500, detail="Failed to create MF holding")

    return new.data[0]


@router.post("/mf/upload-cas")
async def upload_cas_pdf(
    file: UploadFile = File(...),
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """
    Parse-only CAS upload stub.
    Returns file metadata preview — NO database insertion.
    Full CAS PDF parsing to be implemented later.
    """
    allowed = {".pdf", ".csv", ".txt"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="File must be PDF, CSV or TXT")

    content = await file.read()
    return {
        "filename": file.filename,
        "size_bytes": len(content),
        "content_type": file.content_type,
        "preview": "CAS parsing not yet implemented — file received successfully.",
        "inserted": False,
    }


@router.delete("/mf/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mf(
    holding_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Delete a mutual fund holding (ownership enforced)."""
    user_id = current_user["user_id"]
    result = supabase.table("mutual_fund_holdings") \
        .delete() \
        .eq("mf_holding_id", holding_id) \
        .eq("user_id", user_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="MF holding not found")
    return None


# ── ETF ───────────────────────────────────────────────────────────────────────

@router.get("/etf", response_model=List[ETFOut])
def list_etf(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """List all ETF holdings for the current user."""
    user_id = current_user["user_id"]
    result = supabase.table("etf_holdings").select("*").eq("user_id", user_id).execute()
    return result.data or []


@router.post("/etf", response_model=ETFOut, status_code=status.HTTP_201_CREATED)
def create_etf(
    body: ETFCreate,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Add an ETF holding manually."""
    user_id = current_user["user_id"]
    new = supabase.table("etf_holdings").insert({
        "user_id": user_id,
        "symbol": body.symbol,
        "etf_name": body.etf_name,
        "isin": body.isin,
        "exchange": body.exchange,
        "category": body.category,
        "quantity": body.quantity,
        "avg_price": body.avg_price,
        "broker": body.broker,
        "demat_account": body.demat_account,
    }).execute()

    if not new.data:
        raise HTTPException(status_code=500, detail="Failed to create ETF holding")

    return new.data[0]


@router.delete("/etf/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_etf(
    holding_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Delete an ETF holding (ownership enforced)."""
    user_id = current_user["user_id"]
    result = supabase.table("etf_holdings") \
        .delete() \
        .eq("etf_holding_id", holding_id) \
        .eq("user_id", user_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="ETF holding not found")
    return None


# ── Crypto ────────────────────────────────────────────────────────────────────

@router.get("/crypto", response_model=List[CryptoOut])
def list_crypto(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """List all crypto holdings for the current user."""
    user_id = current_user["user_id"]
    result = supabase.table("crypto_holdings").select("*").eq("user_id", user_id).execute()
    return result.data or []


@router.post("/crypto", response_model=CryptoOut, status_code=status.HTTP_201_CREATED)
def create_crypto(
    body: CryptoCreate,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Add a crypto holding manually."""
    user_id = current_user["user_id"]
    new = supabase.table("crypto_holdings").insert({
        "user_id": user_id,
        "symbol": body.symbol,
        "crypto_name": body.crypto_name,
        "network": body.network,
        "quantity": body.quantity,
        "avg_price": body.avg_price,
        "exchange": body.exchange,
        "wallet_address": body.wallet_address,
    }).execute()

    if not new.data:
        raise HTTPException(status_code=500, detail="Failed to create crypto holding")

    return new.data[0]


@router.delete("/crypto/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crypto(
    holding_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user),
):
    """Delete a crypto holding (ownership enforced)."""
    user_id = current_user["user_id"]
    result = supabase.table("crypto_holdings") \
        .delete() \
        .eq("crypto_holding_id", holding_id) \
        .eq("user_id", user_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Crypto holding not found")
    return None

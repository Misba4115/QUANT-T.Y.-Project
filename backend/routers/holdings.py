"""
Holdings Router — CRUD /holdings/{equity|mf|etf|crypto}
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db

router = APIRouter()

# ── Equity ────────────────────────────────────────────────────────────────────

@router.get("/equity")
async def list_equity(db: AsyncSession = Depends(get_db)):
    """List equity holdings. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/equity", status_code=201)
async def create_equity(db: AsyncSession = Depends(get_db)):
    """Add equity holding (manual). TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/equity/upload-csv", status_code=201)
async def upload_equity_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload Zerodha/Upstox CSV to bulk-add equity holdings. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/equity/{holding_id}", status_code=204)
async def delete_equity(holding_id: str, db: AsyncSession = Depends(get_db)):
    """Delete equity holding. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


# ── Mutual Funds ──────────────────────────────────────────────────────────────

@router.get("/mf")
async def list_mf(db: AsyncSession = Depends(get_db)):
    """List mutual fund holdings. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/mf", status_code=201)
async def create_mf(db: AsyncSession = Depends(get_db)):
    """Add MF holding (manual). TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/mf/upload-cas", status_code=201)
async def upload_cas_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload CAS PDF (CAMS/KFintech) to bulk-add MF holdings. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/mf/{holding_id}", status_code=204)
async def delete_mf(holding_id: str, db: AsyncSession = Depends(get_db)):
    """Delete MF holding. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


# ── ETF ───────────────────────────────────────────────────────────────────────

@router.get("/etf")
async def list_etf(db: AsyncSession = Depends(get_db)):
    """List ETF holdings. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/etf", status_code=201)
async def create_etf(db: AsyncSession = Depends(get_db)):
    """Add ETF holding. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/etf/{holding_id}", status_code=204)
async def delete_etf(holding_id: str, db: AsyncSession = Depends(get_db)):
    """Delete ETF holding. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


# ── Crypto ────────────────────────────────────────────────────────────────────

@router.get("/crypto")
async def list_crypto(db: AsyncSession = Depends(get_db)):
    """List crypto holdings. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/crypto", status_code=201)
async def create_crypto(db: AsyncSession = Depends(get_db)):
    """Add crypto holding. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/crypto/{holding_id}", status_code=204)
async def delete_crypto(holding_id: str, db: AsyncSession = Depends(get_db)):
    """Delete crypto holding. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")

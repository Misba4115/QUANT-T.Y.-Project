"""User-scoped holdings CRUD and backward-compatible import-preview aliases."""
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from db.postgres import get_db
from repositories.base import SupabaseRepository
from schemas.schemas import (
    CryptoCreate,
    CryptoOut,
    EquityCreate,
    EquityOut,
    ETFCreate,
    ETFOut,
    MutualFundCreate,
    MutualFundOut,
)
from services.auth_service import get_current_user
from services.import_service import preview_import

router = APIRouter()


def _repo(db: Any) -> SupabaseRepository:
    return SupabaseRepository(db)


@router.get("/equity", response_model=list[EquityOut])
def list_equity(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _repo(db).list_for_user("equity_holdings", current_user["user_id"])


@router.post("/equity", response_model=EquityOut, status_code=status.HTTP_201_CREATED)
def create_equity(body: EquityCreate, current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _repo(db).create_for_user("equity_holdings", current_user["user_id"], body.model_dump(mode="json"))


@router.post("/equity/upload-csv")
async def upload_equity_csv(file: UploadFile = File(...), current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    result = await preview_import(file, current_user["user_id"], db)
    if result["target_type"] != "equity_holdings":
        raise HTTPException(status_code=422, detail="The file is not an equity-holdings export")
    return result


@router.delete("/equity/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equity(holding_id: str, current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    if not _repo(db).delete_for_user("equity_holdings", holding_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Equity holding not found")


@router.get("/mf", response_model=list[MutualFundOut])
def list_mf(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _repo(db).list_for_user("mutual_fund_holdings", current_user["user_id"])


@router.post("/mf", response_model=MutualFundOut, status_code=status.HTTP_201_CREATED)
def create_mf(body: MutualFundCreate, current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _repo(db).create_for_user("mutual_fund_holdings", current_user["user_id"], body.model_dump(mode="json"))


@router.post("/mf/upload-cas")
async def upload_cas_pdf(file: UploadFile = File(...), current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    result = await preview_import(file, current_user["user_id"], db)
    if result["target_type"] != "mutual_fund_holdings":
        raise HTTPException(status_code=422, detail="The file is not a supported mutual-fund statement")
    return result


@router.delete("/mf/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mf(holding_id: str, current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    if not _repo(db).delete_for_user("mutual_fund_holdings", holding_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Mutual-fund holding not found")


@router.get("/etf", response_model=list[ETFOut])
def list_etf(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _repo(db).list_for_user("etf_holdings", current_user["user_id"])


@router.post("/etf", response_model=ETFOut, status_code=status.HTTP_201_CREATED)
def create_etf(body: ETFCreate, current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _repo(db).create_for_user("etf_holdings", current_user["user_id"], body.model_dump(mode="json"))


@router.delete("/etf/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_etf(holding_id: str, current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    if not _repo(db).delete_for_user("etf_holdings", holding_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="ETF holding not found")


@router.get("/crypto", response_model=list[CryptoOut])
def list_crypto(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _repo(db).list_for_user("crypto_holdings", current_user["user_id"])


@router.post("/crypto", response_model=CryptoOut, status_code=status.HTTP_201_CREATED)
def create_crypto(body: CryptoCreate, current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return _repo(db).create_for_user("crypto_holdings", current_user["user_id"], body.model_dump(mode="json"))


@router.delete("/crypto/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crypto(holding_id: str, current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    if not _repo(db).delete_for_user("crypto_holdings", holding_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Crypto holding not found")

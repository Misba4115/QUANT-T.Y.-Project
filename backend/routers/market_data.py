from typing import Any

from fastapi import APIRouter, Depends

from db.postgres import get_db
from services.auth_service import get_current_user
from services.market_data import MarketDataService

router = APIRouter()


@router.post("/sync")
def sync_prices(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return MarketDataService(db).refresh_user(current_user["user_id"])

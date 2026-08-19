from typing import Any

from fastapi import APIRouter, Depends

from db.postgres import get_db
from services.auth_service import get_current_user
from services.insights.context import InsightContextService

router = APIRouter()


@router.get("/readiness")
def readiness(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return InsightContextService(db).build(current_user["user_id"])

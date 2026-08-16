"""Risk assessment and explicit presentation preferences."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from db.postgres import get_db
from services.auth_service import get_current_user
from services.personalization import PersonalizationService

router = APIRouter()


class RiskAssessmentRequest(BaseModel):
    loss_tolerance: int | None = Field(default=None, ge=0, le=4)
    emergency_months: float | None = Field(default=None, ge=0, le=60)
    time_horizon_years: float | None = Field(default=None, ge=0, le=60)
    income_stability: int | None = Field(default=None, ge=0, le=4)
    liability_ratio: float | None = Field(default=None, ge=0, le=1)
    concentration_ratio: float | None = Field(default=None, ge=0, le=1)
    illiquid_ratio: float | None = Field(default=None, ge=0, le=1)
    knowledge_level: int | None = Field(default=None, ge=0, le=4)


class PreferencesUpdate(BaseModel):
    persona: Literal["guided", "analytical", "minimal"] | None = None
    explanation_depth: Literal["concise", "balanced", "detailed"] | None = None
    dashboard_emphasis: list[str] | None = Field(default=None, max_length=20)
    explicit_feedback: dict[str, Literal["more", "less", "neutral"]] | None = None


@router.post("/risk-assessments")
def assess(
    body: RiskAssessmentRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return PersonalizationService(db).assess(current_user["user_id"], body.model_dump())


@router.get("/risk-assessments/latest")
def latest(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return PersonalizationService(db).latest_assessment(current_user["user_id"])


@router.get("/preferences")
def get_preferences(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return PersonalizationService(db).preferences(current_user["user_id"])


@router.put("/preferences")
def update_preferences(
    body: PreferencesUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return PersonalizationService(db).update_preferences(
        current_user["user_id"], body.model_dump(exclude_none=True)
    )


@router.delete("/preferences")
def reset_preferences(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return PersonalizationService(db).reset_preferences(current_user["user_id"])

"""Validated public request and response contracts for QUANT."""
from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Money = Annotated[float, Field(ge=0, allow_inf_nan=False)]
PositiveNumber = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Currency = Literal["INR", "USD"]


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore", str_strip_whitespace=True)


class RegisterRequest(APIModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    phone: str | None = Field(default=None, max_length=24)
    age: int | None = Field(default=None, ge=18, le=120)
    monthly_income: Money = 0
    monthly_expenses: Money = 0
    primary_goal: str | None = Field(default=None, min_length=1, max_length=120)
    risk_profile: Literal["conservative", "moderate", "aggressive"] | None = None


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class GoogleAuthRequest(APIModel):
    id_token: str = Field(min_length=20, max_length=10_000)


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool | None = None


class UserOut(APIModel):
    user_id: str
    email: str
    name: str | None = None
    phone: str | None = None
    age: int | None = None
    monthly_income: float | None = None
    monthly_expenses: float | None = None
    primary_goal: str | None = None
    risk_profile: str | None = None
    created_at: str
    updated_at: str | None = None


class UserProfileUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=24)
    age: int | None = Field(default=None, ge=18, le=120)
    monthly_income: Money | None = None
    monthly_expenses: Money | None = None
    primary_goal: str | None = Field(default=None, min_length=1, max_length=120)
    risk_profile: Literal["conservative", "moderate", "aggressive"] | None = None


class BankingAccountCreate(APIModel):
    account_type: Literal["savings", "current", "fixed_deposit", "recurring_deposit"]
    account_name: str = Field(min_length=1, max_length=120)
    institution: str = Field(min_length=1, max_length=120)
    account_number: str | None = Field(default=None, max_length=40)
    current_balance: Money = 0
    currency: Currency = "INR"
    is_primary: bool = False


class BankingAccountUpdate(APIModel):
    account_type: Literal["savings", "current", "fixed_deposit", "recurring_deposit"] | None = None
    account_name: str | None = Field(default=None, min_length=1, max_length=120)
    institution: str | None = Field(default=None, min_length=1, max_length=120)
    account_number: str | None = Field(default=None, max_length=40)
    current_balance: Money | None = None
    currency: Currency | None = None
    is_primary: bool | None = None


class BankingAccountOut(BankingAccountCreate):
    account_id: str
    user_id: str
    created_at: str
    updated_at: str


class EquityCreate(APIModel):
    symbol: str = Field(min_length=1, max_length=32)
    equity_name: str = Field(min_length=1, max_length=200)
    exchange: Literal["NSE", "BSE"] = "NSE"
    quantity: PositiveNumber
    avg_price: Money
    broker: str | None = Field(default=None, max_length=120)
    demat_account: str | None = Field(default=None, max_length=80)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.upper()


class EquityOut(EquityCreate):
    equity_holding_id: str
    user_id: str
    current_price: float | None = None
    current_value: float | None = None
    price_source: str | None = None
    source_timestamp: str | None = None
    last_synced_at: str | None = None
    created_at: str
    updated_at: str


class MutualFundCreate(APIModel):
    mf_name: str = Field(min_length=1, max_length=240)
    scheme_code: str | None = Field(default=None, max_length=40)
    isin: str | None = Field(default=None, max_length=32)
    fund_house: str | None = Field(default=None, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    units: PositiveNumber
    avg_nav: Money
    platform: str | None = Field(default=None, max_length=120)
    folio_number: str | None = Field(default=None, max_length=80)


class MutualFundOut(MutualFundCreate):
    mf_holding_id: str
    user_id: str
    current_nav: float | None = None
    current_value: float | None = None
    price_source: str | None = None
    source_timestamp: str | None = None
    last_synced_at: str | None = None
    created_at: str
    updated_at: str


class ETFCreate(APIModel):
    symbol: str = Field(min_length=1, max_length=32)
    etf_name: str = Field(min_length=1, max_length=200)
    isin: str | None = Field(default=None, max_length=32)
    exchange: Literal["NSE", "BSE"] = "NSE"
    category: str | None = Field(default=None, max_length=80)
    quantity: PositiveNumber
    avg_price: Money
    broker: str | None = Field(default=None, max_length=120)
    demat_account: str | None = Field(default=None, max_length=80)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.upper()


class ETFOut(ETFCreate):
    etf_holding_id: str
    user_id: str
    current_price: float | None = None
    current_value: float | None = None
    price_source: str | None = None
    source_timestamp: str | None = None
    last_synced_at: str | None = None
    created_at: str
    updated_at: str


class CryptoCreate(APIModel):
    symbol: str = Field(min_length=1, max_length=32)
    crypto_name: str = Field(min_length=1, max_length=120)
    network: str | None = Field(default=None, max_length=80)
    quantity: PositiveNumber
    avg_price: Money
    exchange: str | None = Field(default=None, max_length=120)
    wallet_address: str | None = Field(default=None, max_length=200)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.upper()


class CryptoOut(CryptoCreate):
    crypto_holding_id: str
    user_id: str
    current_price: float | None = None
    current_value: float | None = None
    price_source: str | None = None
    source_timestamp: str | None = None
    last_synced_at: str | None = None
    created_at: str
    updated_at: str


class GoalCreate(APIModel):
    goal_name: str = Field(min_length=1, max_length=160)
    goal_type: Literal["house", "retirement", "education", "emergency", "wealth", "custom"] = "custom"
    target_amount: PositiveNumber | None = None
    current_saved: Money = 0
    target_date: date | None = None


class GoalUpdate(APIModel):
    goal_name: str | None = Field(default=None, min_length=1, max_length=160)
    goal_type: Literal["house", "retirement", "education", "emergency", "wealth", "custom"] | None = None
    target_amount: PositiveNumber | None = None
    current_saved: Money | None = None
    target_date: date | None = None


class GoalOut(GoalCreate):
    goal_id: str
    user_id: str
    created_at: str
    updated_at: str | None = None


class BankTransactionCreate(APIModel):
    account_id: str | None = None
    tx_date: date
    description: str = Field(min_length=1, max_length=500)
    amount: PositiveNumber
    tx_type: Literal["debit", "credit"]
    category: str | None = Field(default=None, max_length=80)


class BankTransactionOut(BankTransactionCreate):
    bank_tx_id: str
    user_id: str
    is_anomaly: bool = False
    anomaly_score: float | None = None
    anomaly_model_version: str | None = None
    anomaly_detected_at: str | None = None
    created_at: str


class AssetTransactionCreate(APIModel):
    tx_date: date
    tx_type: Literal["buy", "sell"]
    symbol: str | None = Field(default=None, max_length=32)
    mf_name: str | None = Field(default=None, max_length=240)
    scheme_code: str | None = Field(default=None, max_length=40)
    quantity: PositiveNumber | None = None
    units: PositiveNumber | None = None
    price: Money | None = None
    nav: Money | None = None
    fees: Money = 0


class ChatRequest(APIModel):
    message: str = Field(min_length=1, max_length=4_000)
    conversation_id: str | None = None
    view_context: str | None = Field(default=None, max_length=240)


class Citation(APIModel):
    citation_id: str
    title: str
    source_type: Literal["private_import", "public_knowledge"]
    source_url: str | None = None
    authority: str | None = None
    effective_date: str | None = None
    retrieved_date: str | None = None
    excerpt: str | None = None
    locator: str | None = None
    similarity: float | None = None
    metadata: dict[str, Any] = {}


class AnalysisSection(APIModel):
    specialist: str
    status: str
    summary: str
    metrics: dict[str, Any] = {}


class ChatResponse(APIModel):
    reply: str
    conversation_id: str
    intent: str = "general"
    agent: str = "general"
    citations: list[Citation] = []
    data_as_of: str | None = None
    warnings: list[str] = []
    routing_confidence: float | None = None
    consulted_agents: list[str] = []
    analysis_sections: list[AnalysisSection] = []
    evidence_summary: dict[str, Any] = {}
    limitations: list[str] = []
    degraded_dependencies: list[str] = []


class DashboardGenerateRequest(APIModel):
    widgets: list[str] = []
    time_period: Literal["1m", "3m", "6m", "1y", "all", "custom"] = "1y"
    date_from: date | None = None
    date_to: date | None = None

    @field_validator("date_to")
    @classmethod
    def validate_date_to(cls, value: date | None, info):
        start = info.data.get("date_from")
        if value and start and value < start:
            raise ValueError("date_to must be on or after date_from")
        return value


class DashboardRunOut(APIModel):
    run_id: str
    status: Literal["pending", "processing", "completed", "partial", "failed"]
    result: dict[str, Any] | None = None
    error: str | None = None


class DashboardConfigUpdate(APIModel):
    widgets: list[str]
    time_period: Literal["1m", "3m", "6m", "1y", "all", "custom"] = "1y"
    chart_preferences: dict[str, Literal["line", "area", "bar", "donut"]] = {}
    custom_date_from: date | None = None
    custom_date_to: date | None = None
    currency: Literal["INR", "USD"] = "INR"


class DashboardConfigOut(DashboardConfigUpdate):
    user_id: str
    updated_at: str | None = None


class ImportCommitRequest(APIModel):
    column_mapping: dict[str, str] | None = None

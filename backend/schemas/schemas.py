"""
Pydantic Schemas — Request/Response validation for all QUANT endpoints
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: Optional[int] = None
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    primary_goal: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
    risk_profile: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Banking ───────────────────────────────────────────────────────────────────

class BankingAccountCreate(BaseModel):
    account_type: str    # savings|current|fixed_deposit|recurring_deposit
    name: str
    institution: str
    account_number: Optional[str] = None
    current_balance: float = 0
    is_primary: bool = False

class BankingAccountOut(BankingAccountCreate):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ── Equity ────────────────────────────────────────────────────────────────────

class EquityCreate(BaseModel):
    symbol: str
    name: str
    exchange: Optional[str] = "NSE"
    quantity: float
    avg_price: float
    broker: Optional[str] = None

class EquityOut(EquityCreate):
    id: UUID
    current_price: Optional[float]
    current_value: Optional[float]

    class Config:
        from_attributes = True


# ── Mutual Fund ───────────────────────────────────────────────────────────────

class MutualFundCreate(BaseModel):
    name: str
    scheme_code: Optional[str] = None
    isin: Optional[str] = None
    fund_house: Optional[str] = None
    category: Optional[str] = None          # equity|debt|hybrid|liquid
    units: float
    avg_nav: float
    platform: Optional[str] = None
    folio_number: Optional[str] = None

class MutualFundOut(MutualFundCreate):
    id: UUID
    current_nav: Optional[float]
    current_value: Optional[float]

    class Config:
        from_attributes = True


# ── ETF ───────────────────────────────────────────────────────────────────────

class ETFCreate(BaseModel):
    symbol: str
    name: str
    isin: Optional[str] = None
    exchange: Optional[str] = "NSE"
    category: Optional[str] = None
    quantity: float
    avg_price: float
    broker: Optional[str] = None

class ETFOut(ETFCreate):
    id: UUID
    current_price: Optional[float]
    current_value: Optional[float]

    class Config:
        from_attributes = True


# ── Crypto ────────────────────────────────────────────────────────────────────

class CryptoCreate(BaseModel):
    symbol: str           # BTC, ETH
    name: str
    network: Optional[str] = None
    quantity: float
    avg_price: float      # in INR
    exchange: Optional[str] = None

class CryptoOut(CryptoCreate):
    id: UUID
    current_price: Optional[float]
    current_value: Optional[float]

    class Config:
        from_attributes = True


# ── Goals ─────────────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    name: str
    goal_type: Optional[str] = "custom"   # house|retirement|education|emergency|wealth|custom
    target_amount: Optional[float] = None
    current_saved: float = 0
    target_date: Optional[date] = None

class GoalOut(GoalCreate):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None   # None → start new conversation

class ChatResponse(BaseModel):
    reply: str
    conversation_id: UUID


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardGenerateRequest(BaseModel):
    widgets: List[str]  # ['net_worth','asset_allocation','portfolio_performance','cashflow','tax_tracker','top_holdings','alerts']
    time_period: str    # '1m'|'3m'|'6m'|'1y'|'all'

class DashboardRunOut(BaseModel):
    run_id: UUID
    status: str         # pending|processing|completed|failed
    result: Optional[dict] = None

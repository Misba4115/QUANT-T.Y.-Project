"""
Pydantic Schemas — Request/Response validation for all QUANT endpoints
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID


# ── Auth ──────────────────────────────────────────────────────────────────────
# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None  # Added from schema
    age: int
    monthly_income: float
    monthly_expenses: float
    primary_goal: str
    risk_profile: Optional[str] = None  # Added from schema

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    user_id: str  # Matches your schema
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None  # Added from schema
    age: Optional[int] = None
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    primary_goal: Optional[str] = None
    risk_profile: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
# ── Banking ───────────────────────────────────────────────────────────────────

class BankingAccountCreate(BaseModel):
    account_type: str    # savings|current|fixed_deposit|recurring_deposit
    account_name: str    # Changed from 'name' to 'account_name'
    institution: str
    account_number: Optional[str] = None
    current_balance: float = 0
    currency: str = "INR"  # Added
    is_primary: bool = False

class BankingAccountOut(BankingAccountCreate):
    account_id: str  # Changed from 'id' to 'account_id'
    user_id: str  # Changed from UUID to str
    created_at: str  # Changed from datetime to str
    updated_at: str  # Added

    class Config:
        from_attributes = True


# ── Equity ────────────────────────────────────────────────────────────────────

class EquityCreate(BaseModel):
    symbol: str
    equity_name: str  # Changed from 'name' to 'equity_name'
    exchange: Optional[str] = "NSE"
    quantity: float
    avg_price: float
    broker: Optional[str] = None
    demat_account: Optional[str] = None  # Added

class EquityOut(EquityCreate):
    equity_holding_id: str  # Changed from 'id' to 'equity_holding_id'
    user_id: str  # Added
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    last_synced_at: Optional[str] = None  # Added
    created_at: str  # Added
    updated_at: str  # Added

    class Config:
        from_attributes = True


# ── Mutual Fund ───────────────────────────────────────────────────────────────

class MutualFundCreate(BaseModel):
    mf_name: str  # Changed from 'name' to 'mf_name'
    scheme_code: Optional[str] = None
    isin: Optional[str] = None
    fund_house: Optional[str] = None
    category: Optional[str] = None          # equity|debt|hybrid|liquid
    units: float
    avg_nav: float
    platform: Optional[str] = None
    folio_number: Optional[str] = None

class MutualFundOut(MutualFundCreate):
    mf_holding_id: str  # Changed from 'id' to 'mf_holding_id'
    user_id: str  # Added
    current_nav: Optional[float] = None
    current_value: Optional[float] = None
    last_synced_at: Optional[str] = None  # Added
    created_at: str  # Added
    updated_at: str  # Added

    class Config:
        from_attributes = True


# ── ETF ───────────────────────────────────────────────────────────────────────

class ETFCreate(BaseModel):
    symbol: str
    etf_name: str  # Changed from 'name' to 'etf_name'
    isin: Optional[str] = None
    exchange: Optional[str] = "NSE"
    category: Optional[str] = None
    quantity: float
    avg_price: float
    broker: Optional[str] = None
    demat_account: Optional[str] = None  # Added

class ETFOut(ETFCreate):
    etf_holding_id: str  # Changed from 'id' to 'etf_holding_id'
    user_id: str  # Added
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    last_synced_at: Optional[str] = None  # Added
    created_at: str  # Added
    updated_at: str  # Added

    class Config:
        from_attributes = True


# ── Crypto ────────────────────────────────────────────────────────────────────

class CryptoCreate(BaseModel):
    symbol: str           # BTC, ETH
    crypto_name: str  # Changed from 'name' to 'crypto_name'
    network: Optional[str] = None
    quantity: float
    avg_price: float      # in INR
    exchange: Optional[str] = None
    wallet_address: Optional[str] = None  # Added

class CryptoOut(CryptoCreate):
    crypto_holding_id: str  # Changed from 'id' to 'crypto_holding_id'
    user_id: str  # Added
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    last_synced_at: Optional[str] = None  # Added
    created_at: str  # Added
    updated_at: str  # Added

    class Config:
        from_attributes = True


# ── Goals ─────────────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    goal_name: str  # Changed from 'name' to 'goal_name'
    goal_type: Optional[str] = "custom"   # house|retirement|education|emergency|wealth|custom
    target_amount: Optional[float] = None
    current_saved: float = 0
    target_date: Optional[date] = None

class GoalOut(GoalCreate):
    goal_id: str  # Changed from 'id' to 'goal_id'
    user_id: str  # Changed from UUID to str
    created_at: str  # Changed from datetime to str

    class Config:
        from_attributes = True


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None   # Changed from UUID to str

class ChatResponse(BaseModel):
    reply: str
    conversation_id: str  # Changed from UUID to str


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardGenerateRequest(BaseModel):
    widgets: List[str]  # ['net_worth','asset_allocation','portfolio_performance','cashflow','tax_tracker','top_holdings','alerts']
    time_period: str    # '1m'|'3m'|'6m'|'1y'|'all'

class DashboardRunOut(BaseModel):
    run_id: str  # Changed from UUID to str
    status: str         # pending|processing|completed|failed
    result: Optional[dict] = None
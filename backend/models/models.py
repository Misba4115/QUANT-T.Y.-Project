"""
SQLAlchemy ORM Models for QUANT
All tables mirror the PostgreSQL schema in scripts/init_db.sql
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, Numeric, Date,
    DateTime, ForeignKey, Text, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email            = Column(String(255), unique=True, nullable=False)
    password_hash    = Column(String(255), nullable=False)
    name             = Column(String(255))
    phone            = Column(String(20))
    risk_profile     = Column(String(20))    # conservative | moderate | aggressive
    monthly_income   = Column(Numeric(12, 2))
    monthly_expenses = Column(Numeric(12, 2))
    primary_goal     = Column(String(100))
    age              = Column(Integer)
    created_at       = Column(TIMESTAMP, default=datetime.utcnow)

    banking_accounts     = relationship("BankingAccount",    back_populates="user", cascade="all, delete")
    equity_holdings      = relationship("EquityHolding",     back_populates="user", cascade="all, delete")
    mutual_fund_holdings = relationship("MutualFundHolding", back_populates="user", cascade="all, delete")
    etf_holdings         = relationship("ETFHolding",        back_populates="user", cascade="all, delete")
    crypto_holdings      = relationship("CryptoHolding",     back_populates="user", cascade="all, delete")
    goals                = relationship("Goal",              back_populates="user", cascade="all, delete")
    chat_conversations   = relationship("ChatConversation",  back_populates="user", cascade="all, delete")
    dashboard_runs       = relationship("DashboardRun",      back_populates="user", cascade="all, delete")


class BankingAccount(Base):
    __tablename__ = "banking_accounts"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_type    = Column(String(20), nullable=False)  # savings|current|fixed_deposit|recurring_deposit
    name            = Column(String(255), nullable=False)
    institution     = Column(String(255), nullable=False)
    account_number  = Column(String(100))   # masked only
    current_balance = Column(Numeric(15, 2), default=0)
    currency        = Column(String(3), default="INR")
    is_primary      = Column(Boolean, default=False)
    created_at      = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at      = Column(TIMESTAMP, default=datetime.utcnow)

    user             = relationship("User", back_populates="banking_accounts")
    bank_transactions = relationship("BankTransaction", back_populates="account", cascade="all, delete")


class EquityHolding(Base):
    __tablename__ = "equity_holdings"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol         = Column(String(50), nullable=False)   # e.g. "HDFCBANK"
    name           = Column(String(255), nullable=False)
    exchange       = Column(String(20))                   # NSE | BSE
    quantity       = Column(Numeric(20, 8), nullable=False)
    avg_price      = Column(Numeric(15, 2), nullable=False)
    current_price  = Column(Numeric(15, 2))
    current_value  = Column(Numeric(15, 2))
    broker         = Column(String(100))
    demat_account  = Column(String(100))
    last_synced_at = Column(TIMESTAMP)
    created_at     = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at     = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="equity_holdings")


class MutualFundHolding(Base):
    __tablename__ = "mutual_fund_holdings"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_code   = Column(String(50))     # AMFI scheme code
    isin          = Column(String(50))
    name          = Column(String(255), nullable=False)
    fund_house    = Column(String(100))
    category      = Column(String(50))     # equity|debt|hybrid|liquid
    units         = Column(Numeric(20, 8), nullable=False)
    avg_nav       = Column(Numeric(15, 4), nullable=False)
    current_nav   = Column(Numeric(15, 4))
    current_value = Column(Numeric(15, 2))
    platform      = Column(String(100))
    folio_number  = Column(String(100))
    last_synced_at = Column(TIMESTAMP)
    created_at    = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at    = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="mutual_fund_holdings")


class ETFHolding(Base):
    __tablename__ = "etf_holdings"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol        = Column(String(50), nullable=False)
    name          = Column(String(255), nullable=False)
    isin          = Column(String(50))
    exchange      = Column(String(20))
    category      = Column(String(50))     # equity_index|gold|debt|international
    quantity      = Column(Numeric(20, 8), nullable=False)
    avg_price     = Column(Numeric(15, 2), nullable=False)
    current_price = Column(Numeric(15, 2))
    current_value = Column(Numeric(15, 2))
    broker        = Column(String(100))
    demat_account = Column(String(100))
    last_synced_at = Column(TIMESTAMP)
    created_at    = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at    = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="etf_holdings")


class CryptoHolding(Base):
    __tablename__ = "crypto_holdings"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol         = Column(String(20), nullable=False)   # BTC, ETH
    name           = Column(String(100), nullable=False)
    network        = Column(String(50))
    quantity       = Column(Numeric(20, 8), nullable=False)
    avg_price      = Column(Numeric(15, 2), nullable=False)   # in INR
    current_price  = Column(Numeric(15, 2))
    current_value  = Column(Numeric(15, 2))
    exchange       = Column(String(100))
    wallet_address = Column(String(255))
    last_synced_at = Column(TIMESTAMP)
    created_at     = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at     = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="crypto_holdings")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_id    = Column(UUID(as_uuid=True), ForeignKey("banking_accounts.id", ondelete="SET NULL"))
    tx_type       = Column(String(20), nullable=False)   # credit | debit
    category      = Column(String(100))
    description   = Column(Text)
    amount        = Column(Numeric(15, 2), nullable=False)
    tx_date       = Column(Date, nullable=False)
    is_anomaly    = Column(Boolean, default=False)
    anomaly_score = Column(Numeric(5, 4))
    created_at    = Column(TIMESTAMP, default=datetime.utcnow)

    account = relationship("BankingAccount", back_populates="bank_transactions")


class Goal(Base):
    __tablename__ = "goals"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name          = Column(String(255), nullable=False)
    goal_type     = Column(String(50))       # house|retirement|education|emergency|wealth|custom
    target_amount = Column(Numeric(15, 2))
    current_saved = Column(Numeric(15, 2), default=0)
    target_date   = Column(Date)
    created_at    = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title      = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)

    user     = relationship("User", back_populates="chat_conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False)
    role            = Column(String(20), nullable=False)   # user | assistant
    content         = Column(Text, nullable=False)
    created_at      = Column(TIMESTAMP, default=datetime.utcnow)

    conversation = relationship("ChatConversation", back_populates="messages")


class DashboardRun(Base):
    __tablename__ = "dashboard_runs"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    requested_at     = Column(TIMESTAMP, default=datetime.utcnow)
    status           = Column(String(20), default="pending")  # pending|processing|completed|failed
    params           = Column(JSONB, nullable=True)
    result           = Column(JSONB, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    error_message    = Column(Text, nullable=True)

    user = relationship("User", back_populates="dashboard_runs")

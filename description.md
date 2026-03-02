# QUANT – Multi-Agent AI Financial Advisor

> An autonomous, multi-agent personal finance management platform for Indian retail investors,
> built with LangGraph, RAG-Grounded Modern Portfolio Theory, and a clean React frontend.

---

## 1. Project Overview

**QUANT** is a full-stack, AI-powered personal finance management web application
designed for Indian retail investors. It goes beyond passive dashboards by combining
a stateful multi-agent AI backend (LangGraph + GPT-4o) with a clean, modern React
frontend.

Users input their financial data — bank accounts, equity holdings, mutual funds,
ETFs, and crypto — and QUANT runs a team of specialized AI agents to generate a
personalized financial dashboard with portfolio insights, anomaly alerts, tax
optimization recommendations, and cashflow analysis. A persistent conversational
chatbot is available on every page for real-time finance Q&A.

**Academic Context:**
Final Year B.Tech Project — Computer Science & Technology
Usha Mittal Institute of Technology, SNDT Women's University, Mumbai
Guide: Ms. Shehnaz Siddique | January 2026

---

## 2. Problem Statement

Most Indian retail investors manage their money across multiple disconnected platforms
— HDFC Bank, Zerodha, Groww, WazirX — with no unified view. Existing tools are:

- **Passive** — they display historical data but cannot reason or act
- **Disconnected** — no tool understands your MF + stock + crypto + bank together
- **Non-intelligent** — no proactive tax alerts, portfolio rebalancing, or goal tracking

QUANT solves this by providing a single platform that:
1. Ingests all financial data (manual entry + file uploads)
2. Runs four specialized AI agents that analyze the data holistically
3. Presents actionable recommendations through a dashboard and chatbot
4. Operates with human-in-the-loop approval for all sensitive actions

---

## 3. Key Features

### Data Collection
- Manual entry forms for banking accounts, equity, mutual funds, ETFs, crypto
- CSV upload for equity/ETF holdings (Zerodha/Upstox format)
- CAS PDF upload for mutual fund holdings (CAMS/KFintech format)
- Bank statement CSV upload with auto-categorization of transactions

### AI-Powered Dashboard
- **Net Worth** — aggregated across all accounts and holdings
- **Risk Level Meter** — current portfolio risk vs user's stated risk profile
- **Monthly Cashflow** — income vs expenses with surplus/deficit
- **Tax Saving Tracker** — Section 80C utilization (₹0 – ₹1,50,000)
- **Portfolio Over Time** — 12-month net worth line chart
- **Asset Allocation** — donut chart (Equity / Debt / Gold / Cash / Crypto)
- **Top Holdings** — table with current value and P&L %
- **Alerts & Insights** — anomaly flags, rebalancing tips, tax opportunities

### Persistent Chatbot (always visible)
- Floating 💬 button visible on every page
- Answers goal-based questions: "How much should I save to buy a house in 5 years?"
- Answers holdings-based questions: "Is my portfolio too risky?"
- Answers tax questions: "How much LTCG will I pay if I sell my HDFC Bank shares?"
- Answers spending questions: "How much did I spend on food last month?"
- Grounded in user's own data + Indian finance knowledge base (RAG)

### Onboarding
- 3-screen onboarding: financial profile → risk quiz → asset checklist
- Risk profile auto-computed from behavioural quiz (conservative / moderate / aggressive)

---

## 4. Tech Stack

| Layer              | Technology                                        |
|--------------------|---------------------------------------------------|
| Frontend           | React.js, Tailwind CSS                            |
| Backend            | Python, FastAPI                                   |
| AI Orchestration   | LangGraph (StateGraph multi-agent framework)      |
| LLM                | GPT-4o (OpenAI API)                               |
| Embeddings         | Sentence-BERT / MiniLM (sentence-transformers)    |
| Vector Database    | Qdrant                                            |
| Relational DB      | PostgreSQL                                        |
| Equity Prices      | Yahoo Finance API (yfinance)                      |
| MF NAV             | AMFI India API                                    |
| Crypto Prices      | CoinGecko API                                     |
| Portfolio Math     | PyPortfolioOpt, NumPy, Pandas                     |
| Anomaly Detection  | scikit-learn (Isolation Forest)                   |
| PDF Parsing        | pdfplumber / camelot (for CAS statements)         |
| Auth               | JWT (JSON Web Tokens), bcrypt                     |
| Dev Tools          | VS Code, Git, GitHub                              |

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    UI LAYER (React)                     │
│                                                         │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │  Input Data  │  │  Dashboard  │  │   Settings    │  │
│  │  (Tab 1)     │  │  (Tab 2)    │  │   (Tab 3)     │  │
│  └──────────────┘  └─────────────┘  └───────────────┘  │
│                                      ┌────────────────┐ │
│                                      │  💬 Chatbot    │ │
│                                      │  (always on)   │ │
│                                      └────────────────┘ │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────┐
│              BACKEND API LAYER (FastAPI)                │
│                                                         │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │ Auth Service│  │Dashboard         │  │  Chat     │  │
│  │             │  │Aggregator        │  │Orchestrator│  │
│  └─────────────┘  └────────┬─────────┘  └─────┬─────┘  │
└───────────────────────────-│───────────────────│────────┘
                             │                   │
┌────────────────────────────▼───────────────────▼────────┐
│           INTELLIGENCE LAYER (LangGraph Agents)         │
│                                                         │
│  ┌──────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │  Guardian    │  │ Portfolio  │  │  Tax Engine    │  │
│  │  Anomaly     │  │ Analytics  │  │  (Rules + RAG) │  │
│  │  (Isolation  │  │ (Markowitz │  │                │  │
│  │  Forest)     │  │ + CVaR)    │  │                │  │
│  └──────────────┘  └────────────┘  └────────────────┘  │
│                   ┌────────────────┐                    │
│                   │ Cashflow Engine│                    │
│                   │ (Aggregation)  │                    │
│                   └────────────────┘                    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    DATA LAYER                           │
│                                                         │
│  ┌──────────────────────────┐  ┌─────────────────────┐  │
│  │       PostgreSQL         │  │   Qdrant Vector DB  │  │
│  │  users, banking_accounts │  │  financial_docs     │  │
│  │  equity/mf/etf/crypto    │  │  chat_messages_vec  │  │
│  │  holdings + transactions │  │                     │  │
│  │  goals, snapshots, chat  │  │                     │  │
│  └──────────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 6. AI Agents

### 6.1 Guardian — Anomaly Detection
- **Algorithm:** Isolation Forest (scikit-learn)
- **Input:** All transaction tables
- **Output:** Sets `is_anomaly = TRUE` and `anomaly_score` on suspicious transactions
- **Displayed:** Alerts & Insights panel on dashboard

### 6.2 Portfolio Analytics Engine
- **Algorithms:**
  - Ledoit-Wolf shrinkage for covariance matrix estimation
  - Markowitz Mean-Variance Optimization (PyPortfolioOpt)
  - Conditional Value at Risk (CVaR) for downside risk
- **Input:** All holdings tables + live prices from Yahoo Finance / AMFI / CoinGecko
- **Output:** Net worth, asset allocation %, portfolio beta, Sharpe ratio, rebalancing suggestions
- **Displayed:** Portfolio chart, donut chart, top holdings table

### 6.3 Tax Optimization Engine
- **Type:** Rule-based engine + RAG
- **Rules:** Section 80C (max ₹1.5L), LTCG (>1yr equity >₹1L @ 10%), STCG (<1yr @ 15%)
- **Input:** Holdings + transaction dates + user income from profile
- **Output:** Tax exposure estimates, 80C headroom, ELSS/PPF suggestions
- **Displayed:** Tax Saving (80C) progress bar, Tax Insights section

### 6.4 Cashflow Engine
- **Type:** Aggregation + categorization
- **Input:** `bank_transactions` credits vs debits grouped by month + category
- **Output:** Monthly income, monthly spend, surplus/deficit, spending breakdown
- **Displayed:** Monthly Cashflow card, Cashflow tab

### 6.5 Chat Orchestrator (RAG Pipeline)
- **Architecture:** LangGraph RAG agent
  1. Embed user query (Sentence-BERT)
  2. Search `financial_docs` vector collection (HNSW)
  3. Retrieve user context from PostgreSQL (holdings, goals, profile)
  4. GPT-4o generates grounded response
  5. Store message + embedding in `chat_messages_vec`
- **Always visible** as floating button on every page

---

## 7. User Flows

### Flow 1: Registration & Onboarding
```
Register (name, email, password)
  → Onboarding Screen 1: Income, expenses, age, primary goal
  → Onboarding Screen 2: Risk quiz (3 questions → auto-compute risk profile)
  → Onboarding Screen 3: Asset checklist (what do you own?)
  → Land on Input Data page
```

### Flow 2: Data Input
```
Input Data tab
  → Click a category card (Banking / Investments / Trading / Crypto / Goals)
  → Form expands below cards
  → Fill details → Save & Continue
  → Repeat for each category
  → Quick Stats sidebar updates in real time
```

Data entry methods per category:
| Category | Method |
|---|---|
| Banking | Manual form (account type, bank, balance) |
| Equity / ETF | Manual form OR CSV upload (Zerodha/Upstox format) |
| Mutual Funds | Manual form OR CAS PDF upload (CAMS/KFintech) |
| Crypto | Manual form (symbol, qty, avg buy price in INR) |
| Bank Transactions | Bank statement CSV upload (auto-categorized) |
| Goals | Manual form (name, target amount, target date) |

### Flow 3: Dashboard Generation
```
Dashboard tab
  → Select widgets (checkboxes)
  → Select time period (1m / 3m / 6m / 1y / all)
  → Fill any additional info if prompted
  → Click "✨ GENERATE DASHBOARD"
  → Backend runs all 4 agents (async)
  → Dashboard renders with all widgets
```

### Flow 4: Chatbot
```
Click 💬 floating button (any page)
  → Chat drawer opens
  → Type any finance question
  → Orchestrator retrieves relevant context + knowledge
  → GPT-4o responds in plain language
  → Conversation saved for future context
```

---

## 8. Database Schema

### PostgreSQL Tables

```sql
-- Core user identity
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(20),
    risk_profile VARCHAR(20),         -- 'conservative' | 'moderate' | 'aggressive'
    monthly_income NUMERIC(12,2),
    monthly_expenses NUMERIC(12,2),
    primary_goal VARCHAR(100),
    age INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Banking accounts
CREATE TABLE banking_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_type VARCHAR(20) NOT NULL, -- 'savings'|'current'|'fixed_deposit'|'recurring_deposit'
    name VARCHAR(255) NOT NULL,
    institution VARCHAR(255) NOT NULL,
    account_number VARCHAR(100),       -- masked only
    current_balance NUMERIC(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'INR',
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Equity holdings (stocks)
CREATE TABLE equity_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,       -- e.g. "HDFCBANK"
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(20),              -- 'NSE' | 'BSE'
    quantity NUMERIC(20,8) NOT NULL,
    avg_price NUMERIC(15,2) NOT NULL,
    current_price NUMERIC(15,2),
    current_value NUMERIC(15,2),
    broker VARCHAR(100),
    demat_account VARCHAR(100),
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Mutual fund holdings
CREATE TABLE mutual_fund_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheme_code VARCHAR(50),           -- AMFI scheme code
    isin VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    fund_house VARCHAR(100),
    category VARCHAR(50),              -- 'equity'|'debt'|'hybrid'|'liquid'
    units NUMERIC(20,8) NOT NULL,
    avg_nav NUMERIC(15,4) NOT NULL,
    current_nav NUMERIC(15,4),
    current_value NUMERIC(15,2),
    platform VARCHAR(100),
    folio_number VARCHAR(100),
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ETF holdings
CREATE TABLE etf_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    isin VARCHAR(50),
    exchange VARCHAR(20),
    category VARCHAR(50),              -- 'equity_index'|'gold'|'debt'|'international'
    quantity NUMERIC(20,8) NOT NULL,
    avg_price NUMERIC(15,2) NOT NULL,
    current_price NUMERIC(15,2),
    current_value NUMERIC(15,2),
    broker VARCHAR(100),
    demat_account VARCHAR(100),
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cryptocurrency holdings
CREATE TABLE crypto_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,       -- e.g. "BTC", "ETH"
    name VARCHAR(100) NOT NULL,
    network VARCHAR(50),
    quantity NUMERIC(20,8) NOT NULL,
    avg_price NUMERIC(15,2) NOT NULL,  -- in INR
    current_price NUMERIC(15,2),
    current_value NUMERIC(15,2),
    exchange VARCHAR(100),
    wallet_address VARCHAR(255),
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Equity transactions
CREATE TABLE equity_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    holding_id UUID REFERENCES equity_holdings(id) ON DELETE SET NULL,
    tx_type VARCHAR(20) NOT NULL,      -- 'buy'|'sell'|'dividend'|'bonus'|'split'
    symbol VARCHAR(50) NOT NULL,
    quantity NUMERIC(20,8) NOT NULL,
    price NUMERIC(15,2) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    charges NUMERIC(15,2) DEFAULT 0,
    net_amount NUMERIC(15,2),
    tx_date DATE NOT NULL,
    description TEXT,
    broker VARCHAR(100),
    order_id VARCHAR(100),
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score NUMERIC(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Mutual fund transactions
CREATE TABLE mutual_fund_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    holding_id UUID REFERENCES mutual_fund_holdings(id) ON DELETE SET NULL,
    tx_type VARCHAR(20) NOT NULL,      -- 'purchase'|'redemption'|'switch'|'dividend'
    scheme_code VARCHAR(50),
    units NUMERIC(20,8) NOT NULL,
    nav NUMERIC(15,4) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    charges NUMERIC(15,2) DEFAULT 0,
    net_amount NUMERIC(15,2),
    tx_date DATE NOT NULL,
    description TEXT,
    platform VARCHAR(100),
    folio_number VARCHAR(100),
    transaction_id VARCHAR(100),
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score NUMERIC(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ETF transactions
CREATE TABLE etf_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    holding_id UUID REFERENCES etf_holdings(id) ON DELETE SET NULL,
    tx_type VARCHAR(20) NOT NULL,      -- 'buy'|'sell'|'dividend'
    symbol VARCHAR(50) NOT NULL,
    quantity NUMERIC(20,8) NOT NULL,
    price NUMERIC(15,2) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    charges NUMERIC(15,2) DEFAULT 0,
    net_amount NUMERIC(15,2),
    tx_date DATE NOT NULL,
    description TEXT,
    broker VARCHAR(100),
    order_id VARCHAR(100),
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score NUMERIC(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Crypto transactions
CREATE TABLE crypto_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    holding_id UUID REFERENCES crypto_holdings(id) ON DELETE SET NULL,
    tx_type VARCHAR(20) NOT NULL,
    -- 'buy'|'sell'|'transfer_in'|'transfer_out'|'stake'|'unstake'
    symbol VARCHAR(20) NOT NULL,
    quantity NUMERIC(20,8) NOT NULL,
    price NUMERIC(15,2) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    charges NUMERIC(15,2) DEFAULT 0,
    net_amount NUMERIC(15,2),
    tx_date DATE NOT NULL,
    tx_hash VARCHAR(255),
    description TEXT,
    exchange VARCHAR(100),
    wallet_address VARCHAR(255),
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score NUMERIC(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bank transactions (daily spending, salary credits, etc.)
CREATE TABLE bank_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID REFERENCES banking_accounts(id) ON DELETE SET NULL,
    tx_type VARCHAR(20) NOT NULL,      -- 'credit' | 'debit'
    category VARCHAR(100),
    -- 'Food'|'Rent'|'Salary'|'EMI'|'Shopping'|'Entertainment'|'Investment'|'Other'
    description TEXT,
    amount NUMERIC(15,2) NOT NULL,
    tx_date DATE NOT NULL,
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score NUMERIC(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Financial goals
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,        -- e.g. "Buy a house"
    goal_type VARCHAR(50),
    -- 'house'|'retirement'|'education'|'emergency'|'wealth'|'custom'
    target_amount NUMERIC(15,2),
    current_saved NUMERIC(15,2) DEFAULT 0,
    target_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Daily portfolio snapshots (for 12-month line chart)
CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_value NUMERIC(15,2) NOT NULL,
    equity_value NUMERIC(15,2) DEFAULT 0,
    mf_value NUMERIC(15,2) DEFAULT 0,
    etf_value NUMERIC(15,2) DEFAULT 0,
    crypto_value NUMERIC(15,2) DEFAULT 0,
    cash_value NUMERIC(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, snapshot_date)
);

-- Dashboard configuration
CREATE TABLE dashboard_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    selected_widgets JSONB,
    -- ['net_worth','asset_allocation','portfolio_performance',
    --  'cashflow','tax_tracker','top_holdings','alerts']
    default_time_period VARCHAR(20),   -- '1m'|'3m'|'6m'|'1y'|'all'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Dashboard generation runs
CREATE TABLE dashboard_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    requested_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending',
    -- 'pending'|'processing'|'completed'|'failed'
    params JSONB,
    result JSONB,
    processing_time_ms INTEGER,
    error_message TEXT
);

-- Chat conversations
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Chat messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL
        REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,         -- 'user' | 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 9. Vector Database

**Engine:** Qdrant | **Embedding model:** Sentence-BERT / MiniLM | **Vector size:** 1536 | **Distance:** Cosine

### Collection: `financial_docs`
Knowledge base for chatbot RAG — Indian tax laws, SEBI regulations, finance concepts, FAQs.

```json
{
  "collection_name": "financial_docs",
  "fields": {
    "id": "string",
    "title": "string",
    "text": "string (chunked ~512 tokens)",
    "embedding": "vector",
    "type": "string  -- tax | concept | regulation | faq",
    "source": "string  -- it_act | sebi | amfi | blog",
    "created_at": "timestamp"
  }
}
```

Seeded with: Section 80C rules, LTCG/STCG rules, MF categories explained,
risk profile definitions, crypto taxation, Markowitz theory basics, SIP concepts.

### Collection: `chat_messages_vec`
Semantic search over past user conversations — chatbot memory.

```json
{
  "collection_name": "chat_messages_vec",
  "fields": {
    "id": "string",
    "user_id": "string",
    "conversation_id": "string",
    "message_id": "string",
    "role": "string  -- user | assistant",
    "text": "string",
    "embedding": "vector",
    "created_at": "timestamp"
  }
}
```

---

## 10. External APIs

| Data | Source | Sync Interval | Library |
|---|---|---|---|
| Equity / ETF prices | Yahoo Finance | Every 15 min (market hours 9:15–15:30 IST) | `yfinance` |
| Mutual Fund NAV | AMFI India | Once daily after 8 PM IST | `mfapi.in` or direct AMFI CSV |
| Crypto prices | CoinGecko | Every 5 minutes (24/7) | `pycoingecko` |
| LLM responses | OpenAI GPT-4o | On demand | `openai` |

---

## 11. Project Structure

```
quant/
├── frontend/                        # React + Tailwind CSS
│   ├── public/
│   └── src/
│       ├── pages/
│       │   ├── Register.jsx
│       │   ├── Login.jsx
│       │   ├── Onboarding.jsx       # 3-screen onboarding flow
│       │   ├── InputData.jsx        # Main data entry page (Tab 1)
│       │   ├── Dashboard.jsx        # Dashboard config + view (Tab 2)
│       │   └── Settings.jsx
│       ├── components/
│       │   ├── CategoryCards.jsx    # Banking / Investments / Trading / Crypto / Goals
│       │   ├── ChatWidget.jsx       # Floating 💬 button + chat drawer
│       │   ├── forms/
│       │   │   ├── BankingForm.jsx
│       │   │   ├── EquityForm.jsx
│       │   │   ├── MutualFundForm.jsx
│       │   │   ├── ETFForm.jsx
│       │   │   ├── CryptoForm.jsx
│       │   │   └── GoalsForm.jsx
│       │   └── dashboard/
│       │       ├── NetWorthCard.jsx
│       │       ├── RiskMeter.jsx
│       │       ├── CashflowCard.jsx
│       │       ├── TaxSavingCard.jsx
│       │       ├── PortfolioChart.jsx
│       │       ├── AssetAllocationChart.jsx
│       │       ├── TopHoldingsTable.jsx
│       │       └── AlertsPanel.jsx
│       └── App.jsx
│
├── backend/                         # Python FastAPI
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py                  # POST /register, POST /login
│   │   ├── banking.py               # CRUD /banking-accounts
│   │   ├── holdings.py              # CRUD /equity, /mf, /etf, /crypto
│   │   ├── transactions.py          # CRUD + CSV upload for transactions
│   │   ├── goals.py                 # CRUD /goals
│   │   ├── dashboard.py             # POST /generate-dashboard
│   │   └── chat.py                  # POST /chat
│   ├── agents/
│   │   ├── guardian.py              # Isolation Forest anomaly detection
│   │   ├── portfolio.py             # Markowitz + Ledoit-Wolf + CVaR
│   │   ├── tax.py                   # Indian tax rule engine + RAG
│   │   ├── cashflow.py              # Income/expense aggregation
│   │   └── chat_orchestrator.py     # LangGraph RAG pipeline
│   ├── services/
│   │   ├── price_sync.py            # Yahoo Finance / AMFI / CoinGecko sync
│   │   ├── csv_parser.py            # CSV upload parser for holdings
│   │   ├── cas_parser.py            # CAS PDF parser for mutual funds
│   │   └── statement_parser.py      # Bank statement CSV parser + categorizer
│   ├── models/                      # SQLAlchemy ORM models
│   ├── schemas/                     # Pydantic request/response schemas
│   └── db/
│       ├── postgres.py              # PostgreSQL connection (SQLAlchemy)
│       └── vector_db.py             # Qdrant client connection
│
└── scripts/
    ├── init_db.sql                  # Full PostgreSQL schema creation script
    └── seed_vector_db.py            # Seed financial_docs collection
```

---

## 12. Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- PostgreSQL 15+
- Qdrant (Docker recommended)
- OpenAI API key

### 1. Clone the repository
```bash
git clone https://github.com/your-username/quant.git
cd quant
```

### 2. Start Qdrant
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Set up PostgreSQL
```bash
createdb quant_db
psql -d quant_db -f scripts/init_db.sql
```

### 4. Set up backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in `backend/` (see Section 13)

```bash
uvicorn main:app --reload --port 8000
```

### 5. Seed vector database
```bash
python scripts/seed_vector_db.py
```

### 6. Set up frontend
```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`

---

## 13. Environment Variables

Create a `.env` file in `backend/`:

```env
# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/quant_db

# Qdrant
QDRANT_URL=http://localhost:6333

# OpenAI
OPENAI_API_KEY=sk-...

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# External APIs
COINGECKO_API_KEY=your-coingecko-key   # optional, free tier works
```

## Algorithms Used

| Algorithm | Purpose | Library |
|---|---|---|
| Isolation Forest | Anomaly detection on transactions | scikit-learn |
| Ledoit-Wolf Shrinkage | Covariance matrix for portfolio optimization | scikit-learn |
| Markowitz Mean-Variance | Efficient frontier + portfolio optimization | PyPortfolioOpt |
| Conditional Value at Risk (CVaR) | Downside risk estimation | PyPortfolioOpt |
| Sentence-BERT / MiniLM | Text embeddings for semantic search | sentence-transformers |
| HNSW Indexing | Approximate nearest neighbor vector search | Qdrant |
| Retrieval-Augmented Generation | Grounded LLM responses | LangChain / LangGraph |
| LangGraph StateGraph | Multi-agent orchestration and routing | LangGraph |

---


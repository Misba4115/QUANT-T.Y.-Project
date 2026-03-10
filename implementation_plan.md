# QUANT Backend Implementation Plan

This plan fully implements the backend for the QUANT multi-agent financial advisor. The frontend is done; the backend has auth working but all other routes are 501 stubs. Priorities: DB connectivity, all CRUD routes, and the RAG chatbot with Qdrant.

## User Review Required

> [!IMPORTANT]
> **OpenAI API Key**: The [.env](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/.env) currently has `OPENAI_API_KEY=sk-...` as a placeholder. The chat orchestrator will fail without a real key. Please add your actual key to [.env](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/.env) before testing the chatbot step.

> [!WARNING]
> **Qdrant must be running locally** at `http://localhost:6333` for the chatbot to work. If not installed, run: `docker run -p 6333:6333 qdrant/qdrant` or use a cloud Qdrant instance and update `QDRANT_URL` in [.env](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/.env).

> [!NOTE]
> **`/user/profile` vs `/auth/me`**: The frontend calls `GET /user/profile` but the backend exposes `GET /auth/me`. I will add a `/user/profile` router that aliases this correctly so the frontend works without changes.

## Proposed Changes

---

### 1. Database Layer

#### [NEW] [postgres.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/db/postgres.py)
Create a sync SQLAlchemy engine that connects to Supabase Postgres. All existing routers import `from db.postgres import get_db` — this file is **missing** and is the most critical blocker. It will use `DATABASE_URL` (Supabase Postgres connection string) from [.env](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/.env).

```python
# Pattern: synchronous Session, yielded per request
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

> [!NOTE]
> The CRUD routers will still use the **Supabase Python client** (not SQLAlchemy ORM), matching the pattern already used in [auth_service.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/services/auth_service.py). The `get_db` dependency will expose the Supabase client (not an SQLAlchemy session) to keep the code consistent and avoid adding `asyncpg` complications. I'll update it to yield the Supabase client.

#### [MODIFY] [supabase_client.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/db/supabase_client.py)
- Add a guard for missing env vars (raise a clear error on startup if `SUPABASE_URL` or `SUPABASE_KEY` are not set)

#### [MODIFY] [vector_db.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/db/vector_db.py)
- Add `embed_text(text: str) -> list[float]` helper using `SentenceTransformer("all-MiniLM-L6-v2")` — shared utility for both chat orchestrator and future ingest scripts

#### [MODIFY] [main.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/main.py)
- Add `@app.on_event("startup")` → calls [ensure_collections(get_qdrant_client())](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/db/vector_db.py#24-42) to auto-create Qdrant collections on start
- Add a `/user` router so `GET /user/profile` works for the frontend
- Update CORS to also allow `http://localhost:3000` (already present — keep)

---

### 2. Auth / User Router

#### [MODIFY] [auth.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/routers/auth.py)
The router already has `POST /register`, `POST /login`, `GET /me`. No changes needed here.

#### [NEW] [user.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/routers/user.py)
Add `/user/profile` endpoints so the frontend's `userApi.getProfile()` and `userApi.updateProfile()` work:
- `GET /user/profile` — returns `UserOut` (alias of `/auth/me`)
- `PUT /user/profile` — update name, risk_profile, monthly_income, etc. in Supabase

---

### 3. Banking Router

#### [MODIFY] [banking.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/routers/banking.py)
Implement all 4 endpoints using the Supabase client:
- `GET /banking-accounts/` — `supabase.table('banking_accounts').select('*').eq('user_id', uid)`
- `POST /banking-accounts/` — insert new account (body: `BankingAccountCreate`)
- `PUT /banking-accounts/{account_id}` — update balance, name, etc.
- `DELETE /banking-accounts/{account_id}` — delete with ownership check

All endpoints protected by `Depends(get_current_user)`.

---

### 4. Holdings Router

#### [MODIFY] [holdings.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/routers/holdings.py)
Implement all equity/mf/etf/crypto CRUD (list + create + delete) using Supabase for each of the 4 asset tables:
| Endpoint | Table |
|---|---|
| `GET /holdings/equity` | `equity_holdings` |
| `POST /holdings/equity` | `equity_holdings` |
| `DELETE /holdings/equity/{id}` | `equity_holdings` |
| `GET /holdings/mf` | `mutual_fund_holdings` |
| … (same pattern for mf, etf, crypto) | … |

CSV upload endpoints (`/equity/upload-csv`, `/mf/upload-cas`) will be implemented as working stubs returning the parsed rows without DB insert (parse-only preview), to avoid blocking the phase-1 review. Full ingest will be a follow-up.

---

### 5. Transactions Router

#### [MODIFY] [transactions.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/routers/transactions.py)
Implement for `bank` asset_type (the only table in the DB — `bank_transactions`):
- `GET /transactions/bank` — list transactions for user
- `POST /transactions/bank` — insert new transaction
- `DELETE /transactions/bank/{tx_id}` — delete

Return a 400 for unsupported asset types for now.

---

### 6. Goals Router

#### [MODIFY] [goals.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/routers/goals.py)
Full CRUD:
- `GET /goals/` — list user goals from Supabase
- `POST /goals/` — create goal (body: `GoalCreate`)
- `PUT /goals/{goal_id}` — update name/target/date
- `DELETE /goals/{goal_id}` — delete with ownership check

---

### 7. Dashboard Router

#### [MODIFY] [dashboard.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/routers/dashboard.py)
Implement a working synchronous dashboard that returns real data without AI agents (agents are TODO for later):
- `POST /dashboard/generate` — pulls user holdings, accounts, and goals from Supabase; computes `net_worth`, `asset_allocation`, `top_holdings`; returns immediately with status `completed`
- `GET /dashboard/result/{run_id}` — for now returns same data (no async queuing needed yet)
- `GET /dashboard/config` — return default widget list from Supabase user prefs
- `PUT /dashboard/config` — save widget preferences

---

### 8. Chat Orchestrator + Router

#### [MODIFY] [chat_orchestrator.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/agents/chat_orchestrator.py)
Implement the full RAG pipeline using LangGraph `StateGraph`:

```
embed_query → search_qdrant → fetch_user_context → generate_response → store_message
```

1. **embed_query**: MiniLM embed `user_message` → 384-dim vector
2. **search_qdrant**: Query `financial_docs` collection (top-5, cosine) for relevant finance text
3. **fetch_user_context**: Pull holdings + goals + last 10 messages from Supabase
4. **generate_response**: Build system prompt from docs + context, call OpenAI GPT-4o, get reply
5. **store_message**: INSERT user + assistant messages to `chat_messages`, upsert embeddings to Qdrant `chat_messages_vec`

If OpenAI key is missing or Qdrant is down, the node should gracefully fall back (log error + return a polite error message).

#### [MODIFY] [chat.py](file:///C:/Users/misba/OneDrive/Desktop/projects/QUANT-T.Y.-Project/backend/routers/chat.py)
Wire up the three endpoints:
- `POST /chat/` — accepts `ChatRequest(message, conversation_id?)`, creates/reuses a `ChatConversation`, calls `run_chat_orchestrator`, returns `ChatResponse(reply, conversation_id)`
- `GET /chat/conversations` — list user's conversations from Supabase
- `GET /chat/conversations/{conversation_id}/messages` — return messages in order

---

### 9. DB Schema Addition for Dashboard

The `dashboard_runs` table doesn't exist in the schema yet. Instead of adding a new table, `POST /dashboard/generate` will return data synchronously (no polling needed for phase 1). The `run_id` will be a generated UUID included in the response.

---

## Verification Plan

### Step 1 — Start the Backend Server
```powershell
cd "c:\Users\misba\OneDrive\Documents\GitHub\New Quant\QUANT-T.Y.-Project\backend"
uvicorn main:app --reload --port 8000
```
Expected: Server starts, no import errors, Qdrant collection creation is logged.

### Step 2 — Existing Auth Tests
```powershell
cd "c:\Users\misba\OneDrive\Documents\GitHub\New Quant\QUANT-T.Y.-Project\backend"
python test_auth.py
```
Expected: `STATUS: 201`, JSON body with `access_token`.

### Step 3 — Swagger UI Smoke Tests (Manual)
Open `http://localhost:8000/docs` and execute each endpoint:

| Endpoint | Expected |
|---|---|
| `POST /auth/register` | 201 + token |
| `POST /auth/login` | 200 + token |
| `GET /auth/me` | 200 + user object |
| `GET /user/profile` | 200 + user object |
| `GET /banking-accounts/` | 200 + `[]` (empty) |
| `POST /banking-accounts/` | 201 + created account |
| `GET /holdings/equity` | 200 + `[]` |
| `POST /holdings/equity` | 201 + created holding |
| `GET /goals/` | 200 + `[]` |
| `POST /goals/` | 201 + created goal |
| `POST /dashboard/generate` | 200 + dashboard data |
| `POST /chat/` | 200 + reply (requires OpenAI key) |

### Step 4 — Chat End-to-End Test
Write and run a new scratch test `test_chat.py`:
```python
# POST /auth/login → token
# POST /chat/ {"message": "What are my top holdings?"} with Bearer token
# Expect 200 + {"reply": "...", "conversation_id": "..."}
```

### Step 5 — Frontend Integration Check (Manual)
1. Start backend: `uvicorn main:app --reload --port 8000`
2. Start frontend: `npm run dev` in `frontend/` 
3. Open `http://localhost:3000`, register a user, log in, and verify the dashboard loads data.

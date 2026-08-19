# QUANT

QUANT is a privacy-conscious financial intelligence application for Indian retail investors. It combines a Next.js interface, a FastAPI service layer, Supabase-backed financial records, and a multi-agent analysis workflow.

The application is designed to distinguish recorded facts from estimates. Missing prices, insufficient history, and unavailable provider connections are surfaced explicitly instead of being replaced with invented values.

## What is implemented

- Email/password and Google authentication with HTTP-only session cookies
- Banking accounts, goals, holdings, and transaction management
- Preview-before-commit imports for CSV, XLSX, and text-based CAS PDF files
- Column normalization, validation, row-level error reporting, and duplicate protection
- Dashboard aggregation with net worth, cash flow, allocation, holdings, and evidence-aware status labels
- Market-price adapters for supported public data sources
- Portfolio risk and optimization analytics when sufficient price history exists
- Tax analytics based on recorded transaction evidence
- Guardian event processing and durable in-app notifications
- Public-knowledge RAG using Qdrant without embedding private portfolio rows
- Signed PDF and PNG dashboard exports
- Background job schedules and a separately operated worker
- A read-only Upstox connector implementation with OAuth, encrypted credentials, preview, commit, and revocation flows

Upstox is not active until valid application credentials and a registered redirect URL are configured and the connection is authorized by a user.

## Architecture

```text
Browser
  -> Next.js frontend
  -> same-origin /api proxy
  -> FastAPI backend
     -> Supabase (users and financial records)
     -> Qdrant (curated public financial knowledge)
     -> Gemini or OpenAI (configured language-model provider)
     -> public market-data adapters
     -> optional read-only Upstox connection
```

Private financial records remain structured in Supabase. Qdrant is used for curated public knowledge; private holdings and transactions are not automatically embedded.

## Repository layout

```text
backend/
  agents/             Financial analysis and orchestration agents
  core/               Runtime configuration and request handling
  db/                 Supabase and Qdrant clients
  migrations/         Ordered Supabase schema migrations
  repositories/       User-scoped data access
  routers/             FastAPI endpoints
  scripts/             Schema, worker, ingestion, and smoke-test tools
  services/            Imports, analytics, connectors, notifications, and exports
  tests/               Credential-free automated tests
frontend/
  app/                 Next.js routes
  components/          Shared interface components
  contexts/            Client session state
  lib/                 API and import helpers
sample_data/           Safe example import files and instructions
```

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- A Supabase project
- A Qdrant instance for public-knowledge retrieval

For the existing persistent local Qdrant volume, start Docker Desktop and run `docker compose -f docker-compose.qdrant.yml up -d`. Readiness is proven through `/api/rag/readiness`; a configured URL alone is not considered ready.
- A Gemini or OpenAI API key for conversational features

Provider credentials are optional unless the corresponding integration is used.

## Backend setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the required values in `backend/.env`. Never place Supabase privileged keys, model-provider secrets, or broker secrets in frontend environment files.

Apply the SQL migrations in filename order from `backend/migrations/`. The migration files are the schema authority.

```powershell
python init_tables.py
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

`init_tables.py` displays the ordered migration list; migrations must be applied using the Supabase SQL editor or an approved migration runner.

## Frontend setup

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. The frontend proxies `/api` requests to `http://127.0.0.1:8000` by default. In deployment, set the server-only `API_PROXY_TARGET` variable to the FastAPI origin.

## Background worker

Scheduled jobs are processed separately from the API:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m scripts.run_worker
```

Run one worker instance until deployment-level locking and scaling have been explicitly configured.

## Verification

Backend tests do not require production credentials:

```powershell
cd backend
$env:QUANT_ENV = "test"
python -m pytest -m "not integration"
```

Frontend checks:

```powershell
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

Runtime endpoints:

- `GET /` confirms that the API process is running.
- `GET /api/readiness` reports configured and unavailable dependencies independently.

## Database operations

- Apply migrations in lexical filename order.
- Keep the service-role key on the backend only.
- Use `python -m scripts.audit_supabase_schema` to inspect hosted schema compatibility.
- Use `python -m scripts.smoke_hosted_runtime --confirm-hosted-smoke` only against the intended hosted environment. It creates and then removes synthetic test data.

## Security model

- Financial records are accessed through user-scoped repositories.
- Authentication is transported through HTTP-only cookies.
- Connector credentials are encrypted before persistence.
- Imports are previewed before database writes.
- Stable fingerprints prevent repeated import commits.
- Uploaded artifacts use a private Supabase Storage bucket.
- Public-knowledge retrieval is separated from private financial records.
- Reports are generated from recorded application data and use signed download tokens.

## Operational status

The core application and Future Scope schema through migration `005_future_scope.sql` are installed in the configured Supabase project. Migration `006_portfolio_analytics.sql` must also be applied in environments that use historical market evidence for portfolio analytics.

External services still require their own valid credentials and provider-side configuration. A successful local build does not by itself prove that an external provider account is connected.

## Disclaimer

QUANT provides educational financial analysis. It does not provide guaranteed returns or replace advice from a qualified financial, tax, or legal professional.

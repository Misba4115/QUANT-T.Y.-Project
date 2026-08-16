# QUANT — Verified Financial Intelligence

## 1. Product definition

QUANT is a financial intelligence workspace for Indian retail investors. It consolidates user-provided banking, investment, transaction, and goal data; validates that data before persistence; and turns the resulting evidence into dashboards, alerts, analytics, exports, and conversational explanations.

The product follows one central rule: every financial output must be traceable to recorded data, an identified market-data source, or an explicitly labeled calculation. When evidence is missing, QUANT reports the limitation.

## 2. Implemented user experience

### Authentication

Users can register and sign in with email/password or Google authentication. The backend issues session tokens through HTTP-only cookies, and protected endpoints resolve the authenticated user before accessing financial records.

### Financial data entry

Users can maintain:

- Bank accounts
- Financial goals
- Equity holdings and transactions
- Mutual fund holdings and transactions
- ETF holdings and transactions
- Crypto holdings and transactions

The interface supports direct entry as well as file-based imports.

### Safe imports

The import workflow accepts CSV, XLSX, and supported text-based CAS PDF documents. Uploaded data is parsed into a preview before anything is committed.

The preview reports:

- Detected financial record type
- Normalized column mapping
- Parsed records
- Row-specific errors
- Mapping diagnostics
- Duplicate and replay information

Committed imports use stable fingerprints so the same source data is not silently written twice.

### Dashboard

The dashboard aggregates recorded financial data into:

- Net worth
- Current-month income, expenses, and surplus
- Asset allocation
- Top holdings
- Portfolio snapshots
- Market-price coverage
- Evidence-based alerts
- Risk metrics when sufficient observations exist
- Recorded tax evidence

The dashboard labels stale values, estimated cost basis, missing market prices, and insufficient history.

### Portfolio analytics

The portfolio analytics service operates on historical market evidence when it is available. Implemented calculations include volatility and downside-risk measures, covariance-aware portfolio analysis, benchmark beta when both portfolio and benchmark histories are sufficient, and constrained allocation optimization.

The service does not manufacture historical observations. Metrics that cannot be supported by the available series are returned as unavailable with an explanation.

### Tax analytics

Tax analysis uses recorded transaction data and deterministic rules. The service derives evidence such as holding periods, realized gains, eligible deductions recorded by the user, and tax-oriented summaries. Results remain informational and are not represented as professional tax advice.

### Guardian and notifications

Guardian processes financial events, evaluates configured rules, and persists alerts. Notifications are durable, user-scoped, and available through normal API retrieval and server-sent event streaming.

### Conversational analysis

The chat orchestrator routes requests through financial agents for portfolio, cash-flow, tax, and Guardian analysis. Public financial knowledge is retrieved from Qdrant and citation validation is applied before the response is returned.

Private portfolio and transaction rows remain in Supabase and are not automatically copied into the public-knowledge vector store.

### Reports

Users can generate PDF and PNG dashboard exports. Export records are persisted, and downloads use signed, time-limited tokens.

### Read-only broker connection

The backend contains a read-only Upstox connector with:

- OAuth authorization and callback handling
- Hashed, expiring OAuth state
- Encrypted credential persistence
- Profile and holdings retrieval
- Synchronization preview and explicit commit
- Idempotent provider-item handling
- Rate limiting and retry handling
- Revocation and reauthorization states

The connector becomes operational only after provider credentials and a registered callback URL are configured and a user completes authorization.

## 3. System architecture

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- Recharts
- Axios
- Zod and React Hook Form

The frontend communicates through a same-origin `/api` path. Next.js proxies those requests to the FastAPI service using a server-only backend origin.

### Backend

- FastAPI
- Pydantic settings and validation
- Supabase Python client
- LangGraph orchestration
- Gemini or OpenAI model provider
- Qdrant public-knowledge retrieval
- NumPy, pandas, SciPy, and scikit-learn analytics

The API is organized into routers, services, user-scoped repositories, agent workflows, and provider adapters.

### Data layer

Supabase stores identity-linked application data, financial records, imports, connector state, jobs, notifications, Guardian output, preferences, analytics runs, and export metadata.

Schema changes are maintained as ordered SQL migrations under `backend/migrations/`. Row-level security is enabled on Future Scope tables, while privileged application access uses a backend-only Supabase key.

### Knowledge layer

Qdrant stores curated public financial documents. Each knowledge item has a stable identifier and metadata used for retrieval and citation. Personal financial rows are kept outside this public-knowledge collection.

## 4. Data integrity principles

1. Preview precedes persistence for imported files.
2. Every database query is scoped to the authenticated user where applicable.
3. Duplicate imports and provider synchronization items use stable identifiers.
4. Provider payloads are normalized into canonical application records.
5. Source and valuation status are preserved in downstream responses.
6. Missing history produces an unavailable result rather than a fabricated metric.
7. External credentials are encrypted and never exposed to the frontend.

## 5. Runtime services

### API process

FastAPI serves authentication, financial CRUD, imports, dashboard aggregation, connectors, analytics, notifications, Guardian, personalization, jobs, and public-knowledge routes.

### Worker process

A separate worker claims due schedules, records job runs, and executes supported background tasks. Database locking prevents the same schedule from being claimed concurrently.

### Readiness reporting

The health endpoint confirms process availability. The readiness endpoint reports database, language-model, Qdrant, market-data, and optional connector configuration separately so that unavailable optional services do not become hidden failures.

## 6. Database migrations

- `001_canonical_core.sql` — canonical users, accounts, holdings, transactions, goals, and chat records
- `002_recovery_services.sql` — import, dashboard, price-cache, and snapshot services
- `003_hosted_legacy_compatibility.sql` — compatibility constraints for hosted legacy shapes
- `004_service_role_grants.sql` — explicit backend service-role access
- `005_future_scope.sql` — connectors, notifications, jobs, Guardian events, preferences, analytics runs, reports, and secure ingestion storage
- `006_portfolio_analytics.sql` — historical market evidence required by advanced portfolio analytics

Migrations must be applied in filename order. Application code does not attempt to create production tables automatically.

## 7. Verification strategy

The backend test suite uses a fake Supabase implementation so core tests are deterministic and do not require production credentials. Tests cover authentication boundaries, CRUD routes, imports, agent orchestration, market data, dashboard behavior, security controls, Future Scope services, and portfolio analytics.

Frontend verification consists of ESLint, TypeScript checking, and a production Next.js build.

Hosted verification is performed separately because it writes synthetic records. The smoke script requires an explicit confirmation flag and removes its own test account after completion.

## 8. Deployment requirements

A deployed environment requires:

- A Supabase project with the ordered migrations applied
- Backend-only Supabase privileged credentials
- A strong JWT signing secret
- A configured Gemini or OpenAI provider for chat
- Qdrant configuration for public-knowledge retrieval
- A separately running worker for scheduled jobs
- A server-only frontend API proxy target
- HTTPS and provider-approved callback URLs for any enabled external connection

Optional providers should remain visibly unavailable until their credentials and provider-side configuration are complete.

## 9. Current boundaries

QUANT reports only the data and calculations its installed services can support. External accounts are not considered connected until their authorization flow succeeds. Market-dependent analytics remain unavailable until adequate historical observations exist. Educational analysis is not presented as guaranteed performance or professional financial, tax, or legal advice.

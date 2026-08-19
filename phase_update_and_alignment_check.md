# Phase Update — Planned Features & Alignment Check

## Part A — Everything we've planned this phase (full list)

### 1. Core algorithm — GC-SEC (Grounded Consensus with Self-Evolving Calibration)
- **Grounding Checker** — verifies every numeric claim in agent/LLM output against real computed values before it reaches the user
- **Consensus Arbiter** — new component that resolves conflicting agent recommendations using constraint-priority rules (regulatory > risk profile > return)
- **Outcome Evaluator + calibration loop** — logs every prediction, compares to realized outcomes later, adjusts each agent's parameters over time
- New tables: `agent_predictions`, `agent_calibration`
- Existing 4 agents (Guardian, Portfolio, Tax, Cashflow) unchanged in logic, but now route through Grounding + Arbiter before reaching the Dashboard

### 2. New feature — Insights & Trading tab
- New 3rd tab: allocation recommendations, return forecasts, rebalance actions (advisory only, no execution)
- New **Trading/Allocation Agent**, reusing Portfolio Analytics' existing covariance/CVaR output
- Three-tier model plan:
  - Tier 1: statistical baseline (EWMA returns + existing covariance)
  - Tier 2: pretrained, fine-tuned time-series model (e.g. Chronos) for return forecasting
  - Tier 3: self-built PPO reinforcement learning policy for allocation — the piece tied directly to the self-evolving calibration loop
- Chatbot gets a new intent route for insights queries, through the same Grounding + Arbiter pipeline
- Re-evaluation triggered on login/tab-open, not continuous background polling — a stated scope decision

### 3. Security layer
- Argon2id password hashing (replacing plain bcrypt)
- AES-256-GCM field-level encryption for PII/financial fields
- Envelope encryption via HashiCorp Vault (key separated from database)
- TLS 1.3 in transit
- Zero-trust access: short-lived tokens + per-request scope re-validation
- Isolation Forest reused from Guardian for login anomaly detection
- ClamAV scanning on file uploads
- DPDP 2023 compliance mapping for the report

### 4. Benchmarking & evaluation infrastructure
- Test sets built for 6 components: Guardian (anomaly detection), Portfolio Analytics (vs. reference library), Tax Engine (rule-based exact-match), Cashflow Engine (categorization), RAG retrieval (Recall@k/MRR), RAG/Chatbot answers (RAGAS faithfulness/relevancy)
- Ablation study plan tied to GC-SEC's three steps (grounding only → +arbitration → +calibration)

---

## Part B — Curated pick from your teammate's pushes (what's actually worth presenting)

Going through the three commits, here's a selection of the substantive, demoable additions — separated from routine cleanup that isn't worth mentor time.

### Worth presenting as real updates

**1. Live broker data connector (Upstox integration)**
Real brokerage account linking, not just manual CSV upload — this is a genuine new data-ingestion capability (`connectors/service.py`, `connectors/upstox.py`, plus sandbox connectors for safe testing). Worth one slide: "users can now link a live brokerage account instead of only uploading statements."

**2. Statement ingestion pipeline (CAS/CSV parsing + Ingestion Inbox + import templates)**
`cas_parser.py`, `csv_parser.py`, `inbox_ingestion.py`, `import_service.py`, plus the frontend's `/import-templates/[id]` route — this is a real, demoable feature: users upload a statement, the system parses and maps it, with a template system for handling different bank/broker formats. Good live-demo material.

**3. Guardian real-time streaming (backend `/guardian_stream` + frontend `/guardian` page)**
This upgrades Guardian from a static, on-demand anomaly check to a live-monitoring view. Worth confirming exact scope with your teammate (polling vs. actual push), but as a feature line, "real-time risk monitoring dashboard" is a strong one to show.

**4. RAG knowledge base expansion**
`qdrant_rag_service.py` now ingests real regulatory/tax documents (`sebi_retail_algo_framework.md`, `income_tax_equity_gains.md`) instead of just user holdings data — this means the chatbot can now answer regulatory/tax questions with grounded source material, not just holdings questions. Directly strengthens what your Grounding Checker will have to work with later.

**5. Notifications system**
New `/notifications` router + frontend page — a real user-facing feature (alerts surfaced centrally rather than only inside chat/dashboard).

**6. Backend architecture hardening**
6 structured DB migrations, a repository pattern for the data layer, and new test suites (`test_security_and_imports.py`, `test_agents_chat.py`, `test_portfolio_analytics.py`). Not a "feature" to demo, but worth one line as engineering maturity — a mentor will read this as the codebase becoming more maintainable, which matters for a major project handoff.

**7. Client-side parsing removed, moved server-side**
The frontend commit explicitly removed local CSV/broker parsing logic in favor of backend endpoints. This is worth connecting to your security narrative directly — sensitive financial statement data no longer gets parsed in the browser, which is a genuine (if incidental) security improvement you can honestly claim.

### Skip presenting these — routine cleanup, not updates
- `.gitignore` changes, dependency/package-lock trimming, README rewrite, removal of "obsolete" docs — normal hygiene, not something to spend mentor time on

### One thing to verify before tomorrow, not after
The docs commit says it **"trimmed down `description.md` by removing redundant notes and old design documentation."** Worth a quick `git diff` on that file tonight, just to confirm nothing from the GC-SEC/Insights planning got caught in that cleanup.

---

## What to show your mentor

Present it as two tracks, clearly separated:
- **Track 1 (this conversation's work):** GC-SEC algorithm design, Insights & Trading tab plan, security layer plan, benchmarking test sets — designed, ready to build
- **Track 2 (teammate's pushes):** live broker connector, statement ingestion pipeline, real-time Guardian monitoring, expanded RAG knowledge base, notifications, and backend hardening — already implemented

That framing shows real, parallel progress on both fronts, which is a stronger story than either half alone.

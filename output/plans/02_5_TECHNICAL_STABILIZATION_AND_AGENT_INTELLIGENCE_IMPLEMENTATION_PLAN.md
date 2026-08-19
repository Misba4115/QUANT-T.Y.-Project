# QUANT - Phase 2.5 Technical Stabilization and Agent Intelligence Implementation Plan

Status: proposed execution plan; must complete before final implementation of Plan 03 UI work  
Primary objective: make QUANT's intelligence layer reliable, evidence-bound, dynamically orchestrated, operationally testable, and stable enough for a high-trust interface  
Repository baseline: `main` at `f449fda`  
Scope boundary: this plan defines the backend contract for a future Insights area, but deliberately does not implement an investment-recommendation algorithm or the Plan 03 interface

## 1. Outcome

Phase 2.5 converts QUANT from a collection of individually useful services into a coordinated financial-intelligence platform with explicit evidence, bounded agent collaboration, measurable chatbot quality, automatically maintained public knowledge, professional data-provider handling, broader import verification, and production-readiness evidence.

At completion:

1. Chat routing is semantic and dynamic rather than keyword-only.
2. Specialist agents communicate through typed requests, claims, evidence, conflicts, and limitations.
3. No agent can publish an unsupported financial number or citation.
4. The chatbot uses the relevant combination of private user data, goals, risk assessment, agent calculations, market evidence, conversation context, and public RAG sources.
5. Tax and regulatory documents are automatically discovered, fetched, hashed, extracted, versioned, and staged for review.
6. Automatically discovered documents do not silently change deterministic tax calculations.
7. Qdrant readiness proves reachability, collection compatibility, population, and active corpus version.
8. An Insights backend contract and context pipeline exist, while the recommendation algorithm remains intentionally absent.
9. Market-data and parsing services have explicit capability matrices, fallbacks, quality evidence, and test corpora.
10. CI, hosted integration tests, evaluation datasets, observability, and bounded load tests replace unsupported "fully validated" claims.
11. Plan 03 receives stable response schemas, availability states, provenance fields, and demonstration fixtures.

## 2. Scope decisions

### 2.1 Included

- Chat and agent contract redesign.
- Dynamic intent and context routing.
- Bounded inter-agent requests and conflict resolution.
- Claim-level grounding and response validation.
- Automated public knowledge maintenance with human approval for material regulatory changes.
- Qdrant operational verification and corpus lifecycle.
- Chatbot evaluation and failure-mode tests.
- Insights context/readiness scaffolding.
- Market-data provider resilience and provenance.
- Parser coverage expansion and a versioned golden corpus.
- Worker completion for Phase 2.5 jobs, including retention deletion.
- CI, hosted integration tests, observability, and load-test baselines.
- Minimum security controls required to safely operate the new agent and knowledge pipelines.

### 2.2 Explicitly excluded

- Plan 03 visual design, navigation, page composition, chatbot screen, accessibility styling, responsive work, and visual regression implementation.
- A portfolio recommendation, stock-picking, return-maximization, reinforcement-learning, or automated-trading algorithm.
- Execution of trades or mutation of holdings from an agent response.
- Gmail scraping for transaction history.
- A live Account Aggregator implementation or a claim of AA certification.
- Full security-algorithm design, penetration testing program, advanced threat detection, key-management redesign, and security certification; these belong in Plan 04.
- Automatic modification of tax formulas based only on newly downloaded prose.

### 2.3 Terminology

- **Agent:** a bounded specialist that returns structured calculations and claims, not an unconstrained chatbot persona.
- **Evidence:** a private database record, deterministic calculation trace, market-data observation, or approved public document chunk.
- **Grounded:** every material factual or numerical claim is linked to evidence that supports it.
- **Consensus:** a deterministic or policy-governed resolution of conflicting specialist conclusions; it is not majority voting between LLMs.
- **Insight:** a traceable observation about the user's financial state. It is not automatically an investment recommendation.
- **Recommendation:** a proposed financial action. Recommendation generation remains disabled in Phase 2.5.

## 3. Corrections to the supplied pipeline concept

The supplied HTML provides a useful shared-agent and verification model, but it is architectural context rather than an exact implementation specification. Phase 2.5 adopts its strongest ideas and corrects unsafe or premature assumptions.

### Adopt

- Dashboard, Chat, and Insights are distinct entry pipelines using shared specialist capabilities.
- A Grounding Checker validates claims before delivery.
- A Consensus Arbiter resolves portfolio, tax, liquidity, and goal conflicts.
- Predictions and outcomes should eventually be measured rather than assumed accurate.
- Agents are reusable capabilities, not components owned by one screen.

### Correct

1. The chatbot is not restricted to a single-agent RAG pipeline. It must dynamically consult multiple agents when a question crosses portfolio, tax, cash-flow, goals, risk, or Guardian domains.
2. "Autonomous communication" must not mean agents freely chatting until they agree. Agents exchange typed requests and evidence through shared state, under hop, time, and tool limits.
3. The Dashboard should not require LLM narration to calculate its values. Core dashboard computation remains deterministic; the LLM may explain an already-grounded result.
4. The Grounding Checker cannot promise truth merely by checking that a citation ID exists. It must validate numerical provenance, calculation traces, time relevance, and source support.
5. The Consensus Arbiter must use explicit policies and return unresolved conflicts when no safe resolution exists.
6. The Outcome Evaluator must not "recalibrate" financial models without a defined target, labelled outcomes, minimum sample size, versioning, and rollback.
7. The proposed Trading Agent, Return Forecaster, and reinforcement-learning allocation policy are not implemented in Phase 2.5. The recommendation algorithm file remains empty.
8. "Maximum returns" is not an acceptable standalone product objective. A later algorithm must define a goal-attainment or risk-adjusted objective subject to loss capacity, horizon, liquidity, tax, concentration, suitability, and uncertainty constraints.

## 4. Current problems this plan must close

### 4.1 Chat and agents

- Routing depends on a small keyword map.
- The LangGraph graph is a fixed sequence even when only one specialist is selected.
- Agents do not issue structured requests to one another.
- The final LLM receives raw agent-output JSON without a stable analysis-section contract.
- Detailed agent output is not returned to the frontend.
- The LLM fallback refers to structured metadata that the API does not return.
- Only the latest eight messages are used; there is no durable summary or semantic history retrieval.
- Citation validation removes unknown IDs but does not verify that cited material supports the claim.
- There is no stored evaluation dataset or groundedness score.

### 4.2 RAG and knowledge

- The active manifest contains only two very small manually written context documents.
- Current tests use fake Qdrant and a fake embedder.
- Readiness treats a configured URL as sufficient and does not prove reachability or population.
- There is no authoritative source registry, scheduled discovery, diff review, supersession, or expiry workflow.
- Public knowledge updates and deterministic tax-rule changes are not separated operationally.

### 4.3 Production evidence

- The credential-free test suite is strong but does not contain live integration tests.
- No CI workflow protects the repository automatically.
- There is no retained chatbot benchmark, provider contract report, parser accuracy report, load baseline, or operational dashboard.
- Retention cleanup is an explicit zero-deletion stub.
- Worker health is not included in readiness.

### 4.4 Market data

- Each asset class currently has one default provider.
- Equity/ETF data uses Yahoo Finance; this is useful for a prototype but is not a contracted exchange-grade feed.
- Provider status is not backed by active health probes, measured freshness, failover, or service-level evidence.
- Live availability is therefore truthfully conditional on the upstream provider.

This dependency is not inherently amateur: every market-data system depends on upstream sources. The professional solution is to define provider contracts, redundancy, freshness states, circuit breakers, last-known-good behavior, health telemetry, and a funded/licensed provider path. It would be unprofessional to hide the dependency or label delayed data as live.

### 4.5 Parser coverage

- CSV and XLSX parsing supports normalized header families but cannot cover every bank and broker export without representative layouts.
- CAS PDF parsing requires extractable text; scanned or image-only PDFs need OCR.
- Encrypted PDFs are rejected.
- CAMS, KFintech, NSDL/CDSL, banks, and brokers change layouts independently.
- There is no versioned, sanitised golden corpus proving field-level accuracy for every advertised format.

"Parser coverage is limited" means formats outside the tested layouts can fail safely instead of being silently misread. Phase 2.5 expands and quantifies coverage; the product must advertise only formats that pass the corpus.

## 5. Target architecture

### 5.1 Shared intelligence runtime

```text
Entry pipeline
  -> Context Assembler
  -> Semantic Intent Router
  -> Orchestration Policy
  -> Specialist agents (parallel where independent)
       -> typed cross-agent requests through coordinator
  -> Grounding Checker
  -> Consensus Arbiter when conflicts or recommendations exist
  -> Response Composer
  -> Response Validator
  -> API response / dashboard and chat output
  -> Outcome Evaluator when a labelled realized outcome becomes available
       -> versioned evaluation metrics and calibration proposals for a later cycle
```

The three shared verification responsibilities are architectural layers, not replacements or renames for the existing specialist agents:

1. **Grounding Checker (layer 1):** validates every material LLM or specialist claim against tool output, calculation traces, and approved sources before delivery.
2. **Consensus Arbiter (layer 2):** reconciles only grounded cross-domain conflicts using explicit constraint priorities and can return a conflict unresolved.
3. **Outcome Evaluator (layer 3):** logs delivered predictions against labelled realized results after delivery. It may produce drift signals and versioned calibration proposals for a future cycle, but cannot silently change a model, financial rule, or policy.

The Outcome Evaluator is not on the synchronous critical path when no mature outcome exists. Its feedback is observational until the evaluation target, minimum sample size, approval, versioning, and rollback gates are satisfied.

### 5.2 Pipeline policies

#### Dashboard pipeline

```text
Authenticated user
  -> assemble holdings, prices, transactions, goals, risk and freshness
  -> run Portfolio + Tax + Cashflow + Guardian concurrently
  -> ground all claims
  -> arbitrate only detected conflicts
  -> persist deterministic dashboard result and evidence map
```

- Dashboard computation must succeed without an LLM.
- Agent explanations are optional, separately labelled narration.
- One agent failure produces a partial dashboard, not a fabricated replacement.

#### Chat pipeline

```text
Question + conversation summary
  -> classify request and required evidence
  -> assemble user context permitted for the request
  -> dynamically select specialists and public retrieval
  -> specialists may request one bounded follow-up analysis
  -> ground claims and reconcile conflicts
  -> compose direct answer + analysis sections + evidence + limitations
```

- Simple educational questions do not need every private table.
- Questions asking what the user should do, whether they can afford an action, or how an action affects goals must consult the full decision context: goals, risk capacity, liquidity/cash flow, portfolio, tax, Guardian limitations, market evidence, and relevant approved public knowledge.
- The response records what was consulted and what was unavailable.

#### Insights pipeline in Phase 2.5

```text
Open Insights context
  -> assemble goal, profile, risk, cash-flow, portfolio, tax and market readiness
  -> ground the context snapshot
  -> return readiness, observations and missing-data blockers
  -> return no allocation, security selection, buy/sell action or forecast
```

The later recommendation pipeline will not be designed until the algorithm objective and validation plan are approved.

## 6. Core data contracts

Create Pydantic models in `backend/agents/contracts.py` or an equivalent package. Do not pass unvalidated dictionaries between orchestration nodes.

### 6.1 Evidence reference

```python
class EvidenceRef:
    evidence_id: str
    evidence_type: Literal[
        "private_record", "calculation", "market_observation", "public_source"
    ]
    source_name: str
    record_locator: str | None
    observed_at: datetime | None
    retrieved_at: datetime
    freshness: Literal["fresh", "delayed", "stale", "unknown"]
    content_hash: str | None
```

### 6.2 Agent claim

```python
class AgentClaim:
    claim_id: str
    agent: str
    claim_type: Literal["fact", "calculation", "inference", "warning", "proposal"]
    subject: str
    statement: str
    value: Decimal | str | None
    unit: str | None
    evidence_ids: list[str]
    confidence: float | None
    as_of: datetime
    model_version: str
    assumptions: list[str]
    limitations: list[str]
```

### 6.3 Agent result

```python
class AgentResult:
    agent: str
    status: Literal[
        "available", "partial", "insufficient_data", "not_applicable",
        "provider_unavailable", "failed"
    ]
    summary: str
    metrics: dict[str, object]
    claims: list[AgentClaim]
    evidence: list[EvidenceRef]
    requests: list[AgentRequest]
    warnings: list[str]
    errors: list[SafeError]
```

### 6.4 Inter-agent request

```python
class AgentRequest:
    request_id: str
    requesting_agent: str
    requested_capability: str
    reason_code: str
    required_fields: list[str]
    parent_claim_id: str | None
```

Agents may request capabilities, not call arbitrary agents or tools directly. The coordinator authorizes and executes requests.

### 6.5 Chat response

Extend `ChatResponse` to include:

```text
reply
conversation_id
intent
routing_confidence
consulted_agents
analysis_sections[]
citations[]
evidence_summary
data_as_of
limitations[]
warnings[]
degraded_dependencies[]
```

`analysis_sections` must contain user-safe summaries and metrics, never private internal chain-of-thought.

## 7. Phase 2.5-0 - Baseline, feature truth, and compatibility freeze

### Tasks

1. Create a machine-readable capability registry for database, LLM, Qdrant, market providers, worker, SMTP, Upstox, ingestion inbox, parsers, and Insights.
2. Standardize statuses across APIs:
   - `available`
   - `partial`
   - `insufficient_data`
   - `stale`
   - `not_configured`
   - `provider_unavailable`
   - `experimental`
   - `not_implemented`
   - `failed`
3. Add response fields for `reason_code`, `data_as_of`, `source`, `freshness`, `sample_count`, and `retryable` where relevant.
4. Preserve existing API fields during migration; add new fields compatibly and deprecate old fields only after the frontend moves in Plan 03.
5. Create Architecture Decision Records for:
   - structured agent communication;
   - public/private knowledge separation;
   - regulatory-document review;
   - Insights algorithm deferral;
   - market-data provider policy.
6. Capture the current 44-test backend baseline and successful frontend lint, typecheck, and production build.

### Exit gate

- Capability and status schemas are documented and tested.
- Existing frontend flows still pass.
- No Plan 03 component work has begun.
- Every later Phase 2.5 task refers to a stable contract rather than an ad hoc dictionary.

## 8. Phase 2.5-1 - Context assembler and evidence registry

### Tasks

1. Implement `UserFinancialContextAssembler` with explicit sub-contexts:
   - authenticated profile;
   - current goals and horizons;
   - latest risk assessment and uncertainty;
   - cash-flow history and liquidity indicators;
   - holdings, acquisition evidence, allocation, valuation coverage;
   - transactions and realised tax evidence;
   - Guardian alerts and unresolved data-quality issues;
   - current and historical market observations;
   - conversation summary and user preferences.
2. Fetch only required sub-contexts according to a `ContextRequirement` object.
3. Build stable evidence IDs for private records and calculations.
4. Redact secrets and unnecessary personal identifiers before context reaches an LLM.
5. Enforce context-size budgets and deterministic compaction.
6. Record missing, stale, or contradictory data instead of replacing it.
7. Add `context_version` and `data_as_of` to every assembled snapshot.

### Required behavior

- Read-only questions cannot mutate financial records.
- An LLM never receives Supabase credentials, connector credentials, raw OAuth payloads, attachment contents unrelated to the question, or another user's data.
- A financial-action question automatically requires the full decision context even if the router initially identifies only one domain.

### Exit gate

- Unit tests prove user isolation and context minimization.
- A complete context snapshot can be reproduced from the same database state.
- Missing history produces explicit blockers.
- Context assembly works without Qdrant or an LLM.

## 9. Phase 2.5-2 - Dynamic routing and bounded agent collaboration

### Tasks

1. Replace `AGENT_KEYWORDS` as the primary router with a structured semantic router.
2. Router output must include:
   - primary intent;
   - secondary intents;
   - required specialists;
   - required private contexts;
   - whether public knowledge is required;
   - risk level;
   - clarification requirement;
   - confidence.
3. Use a deterministic fallback router when the LLM is unavailable.
4. Build conditional LangGraph edges; do not traverse every agent node for every request.
5. Permit concurrent execution of independent agents.
6. Implement coordinator-mediated `AgentRequest` handling.
7. Bound collaboration:
   - maximum two follow-up rounds;
   - no recursive self-request;
   - per-agent timeout;
   - global request timeout;
   - capability allowlist;
   - deduplicated requests;
   - full run trace.
8. Add explicit routes for:
   - informational education;
   - user-specific analysis;
   - cross-domain analysis;
   - recommendation-like request;
   - unsupported/out-of-scope request;
   - clarification.
9. Make the old `ChatOrchestrator` a compatibility wrapper until tests and the frontend consume the new contract.

### Communication model

Agents do not exchange persuasive prose. They exchange:

- required inputs;
- typed metrics;
- claims;
- evidence IDs;
- conflicts;
- assumptions;
- limitations;
- requests for missing capabilities.

Example:

```text
Portfolio Agent proposes: reduce concentration in holding X.
Tax Agent responds: sale would realise an STCG amount supported by lots A/B.
Cashflow Agent responds: liquidity target is already underfunded.
Arbiter result: do not produce a sell instruction; explain the conflict and request user constraints.
```

### Exit gate

- Representative paraphrases route correctly without exact keywords.
- Multi-domain questions execute all required specialists.
- Irrelevant specialists do not run.
- Agent loops cannot exceed configured bounds.
- Failures remain partial and traceable.

## 10. Phase 2.5-3 - Grounding Checker and Consensus Arbiter

### 10.1 Grounding Checker

Implement deterministic validation first and use an LLM evaluator only as a secondary semantic check.

Checks:

1. Every numerical fact has an evidence ID.
2. The evidence value, unit, currency, date, and aggregation scope match the claim.
3. Calculations can be recomputed from referenced inputs.
4. Market claims contain provider and observation time.
5. Tax/regulatory explanations cite an active authoritative source with effective date.
6. Public citations actually support the associated statement.
7. Unavailable or insufficient data is not rewritten as certainty.
8. A model cannot introduce a price, return, tax amount, forecast, or provider state absent from evidence.
9. Uploaded or retrieved documents remain untrusted data, never instructions.

Validation outcomes:

- `verified`
- `verified_with_limitations`
- `unsupported`
- `contradictory`
- `stale`
- `requires_review`

Unsupported material claims are removed or replaced with an explicit limitation. One bounded regeneration is allowed; the deterministic fallback must then be used.

### 10.2 Consensus Arbiter

The Arbiter runs only when:

- two agents produce contradictory claims;
- a proposal interacts with tax, risk, liquidity, or goals;
- an Insights request eventually proposes an action;
- data sources disagree materially.

Initial policies:

1. Newer valid evidence outranks older evidence, while retaining stale evidence as history.
2. Deterministic calculations outrank unsupported LLM inference.
3. Legal/tax constraints are not overridden by a return forecast.
4. Risk-capacity and liquidity constraints bound any future allocation proposal.
5. Missing acquisition history blocks exact tax-impact claims.
6. Material unresolved conflicts are returned to the user; the system does not guess.
7. The Arbiter may approve an explanation, warning, or request for clarification in Phase 2.5, but not an investment action.

### Exit gate

- A test matrix covers number mismatch, stale evidence, conflicting providers, missing tax lots, prompt injection, invented citation, and agent disagreement.
- Every final material claim has a validation outcome.
- No internal chain-of-thought is persisted or returned.

## 11. Phase 2.5-4 - Automated authoritative knowledge pipeline

### 11.1 Source registry

Create a database-backed registry rather than relying only on a static two-file manifest.

Initial allowlisted source families:

- Income Tax Department: Acts, official guidance, notifications, circulars, and latest-news listings.
- CBDT/Ministry of Finance documents published through official government domains.
- e-Gazette notifications when a stable official retrieval route is available.
- SEBI: Acts, Regulations, Circulars, Master Circulars, Gazette Notifications, and investor guidance.
- RBI: Notifications and Master Directions relevant to retail financial products and payments.
- AMFI or other official industry bodies only for clearly identified non-regulatory reference data.

Initial discovery seeds to validate during Phase 2.5-4:

- Income Tax Act 2025 portal: `https://www.incometax.gov.in/iec/foportal/newdownloads/income-tax-act-2025`
- Income Tax Department latest news: `https://www.incometax.gov.in/iec/foportal/latest-news`
- CBDT/Income Tax circular index: `https://www.incometaxindia.gov.in/en/circulars`
- SEBI Legal index: `https://www.sebi.gov.in/legal.html`
- SEBI Master Circular listing: `https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=6`
- RBI Master Directions index: `https://www.rbi.org.in/scripts/BS_ViewMasterDirections.aspx?did=339`

These are discovery seeds, not blanket approval of every linked document. The implementation must validate final URLs, redirects, authority, content type, document family, publication/effective dates, and continued availability before ingestion.

Each registry entry contains:

```text
source_id
authority
official_domain
listing_url or document_url
document_family
topic tags
jurisdiction
discovery schedule
expected content types
effective-date extraction policy
review requirement
active/suspended status
```

### 11.2 Automated lifecycle

```text
Discover
  -> fetch with allowlist, timeout and size limits
  -> record HTTP metadata and content hash
  -> malware/content-type checks
  -> extract text in a sandboxed process
  -> classify topic and detect effective dates
  -> compare with previous active version
  -> quarantine if parsing or integrity checks fail
  -> create review candidate
  -> human approval for material regulatory changes
  -> publish versioned chunks
  -> switch active Qdrant corpus alias
  -> retain rollback metadata
```

### 11.3 Automation policy

Automate:

- discovery;
- downloading;
- hashing;
- duplicate detection;
- text extraction;
- metadata extraction;
- diff generation;
- supersession detection;
- scheduled re-checks;
- Qdrant staging ingestion;
- notification that review is required.

Do not automate without review:

- interpreting a legal change as a new tax formula;
- changing a tax rate, exemption, holding period, or assessment-year rule in executable code;
- activating a source whose authority/effective date is ambiguous;
- deleting the last valid corpus version;
- converting consultation papers or news commentary into binding rules.

RAG can explain newly approved documents. Deterministic tax code changes require a versioned rule fixture, reviewer approval, tests for the old and new effective periods, and a normal code/migration release.

### 11.4 Qdrant operations

1. Add active reachability and collection probes.
2. Verify embedding dimension and model identifier.
3. Report active document/chunk counts and last successful ingestion.
4. Use versioned collections or aliases for zero-downtime corpus promotion and rollback.
5. Store source hash, parser version, embedding model, effective date, publication date, retrieval date, authority, and status in every chunk.
6. Reject chunks missing authority or source URL.
7. Add hybrid or metadata-filtered retrieval where required; do not rely solely on vector similarity for jurisdiction/effective date.
8. Add retrieval tests using real embeddings and a disposable Qdrant collection.

### 11.5 Worker jobs

Add supported jobs:

- `knowledge_discovery`
- `knowledge_fetch`
- `knowledge_extract`
- `knowledge_stage_index`
- `knowledge_publish`
- `knowledge_expiry_audit`

Material publish operations require an authenticated administrative approval path and an audit record.

### Exit gate

- A scheduled run discovers and stages an official document without manual file copying.
- An unchanged document is idempotent.
- A changed document produces a reviewable diff.
- A rejected document never enters the active collection.
- The previous collection can be restored.
- Readiness reports real Qdrant state, not just configuration.

## 12. Phase 2.5-5 - Context-driven chatbot upgrade

### Response contract

Every user-specific response follows this logical anatomy:

1. Direct answer.
2. User-specific findings.
3. Cross-agent considerations.
4. Evidence and as-of dates.
5. Assumptions and missing data.
6. Safe, non-prescriptive next steps.
7. Sources when public knowledge is used.

### Tasks

1. Feed the composer validated `AgentResult` objects, not raw arbitrary JSON.
2. Include relevant goals, history, risk capacity, liquidity, portfolio, tax state, Guardian state, market freshness, and RAG context according to routing requirements.
3. Require full decision context for recommendation-like questions.
4. Add conversation summarization with versioned summaries after the raw-message window is exceeded.
5. Add semantic retrieval over the user's own conversation summaries without embedding holdings or transactions into the public Qdrant collection.
6. Keep private memory and public knowledge in separate stores/collections and authorization paths.
7. Return `analysis_sections`, `consulted_agents`, evidence summary, limitations, and degraded dependencies.
8. Correct the LLM-unavailable fallback so it returns actual structured specialist summaries.
9. Add explicit refusals/clarifications for guaranteed returns, unsupported tax filing, ungrounded market predictions, and trade execution.
10. Preserve conversation ownership at the API and test it against cross-user access.

### Evaluation dataset

Create at least 60 versioned cases spanning:

- general education;
- portfolio analysis;
- tax analysis;
- cash-flow and affordability;
- Guardian anomalies;
- goals and risk capacity;
- cross-domain conflicts;
- insufficient-data cases;
- stale/provider-failure cases;
- regulatory questions requiring RAG;
- prompt injection and malicious imported text;
- guaranteed-return or trade-execution requests.

Store expected routing, required contexts, required evidence, forbidden claims, and answer rubric.

### Minimum release metrics

- At least 90 percent correct primary routing on the approved evaluation set.
- 100 percent inclusion of mandatory contexts for recommendation-like test cases.
- 100 percent numerical claims linked to valid evidence.
- At least 95 percent citation precision on the approved public-knowledge set.
- Zero unknown citation IDs in final responses.
- Zero unsupported critical tax rates, prices, returns, or trade claims in the release set.
- All dependency-failure cases return useful, truthful degraded responses.
- Latency baseline and p50/p95 are recorded by route; budgets are set from the measured baseline before release.

### Exit gate

- The evaluation report is committed as machine-readable output or generated reproducibly in CI.
- The chatbot gives meaningfully different answers for different user contexts while preserving the same verified facts.
- The chatbot cannot present an agent calculation that failed grounding.

## 13. Phase 2.5-6 - Insights and Recommendations backend scaffold

### Product framing

The future feature should be named and described as goal-aware, risk-aware financial insights. It must not promise "maximum returns." A later algorithm may optimize a defined objective such as probability of goal attainment or risk-adjusted expected utility under explicit constraints.

### Phase 2.5 deliverables

1. Create an Insights context contract containing:
   - goals, target dates, priority, and funding gaps;
   - risk tolerance and loss capacity separately;
   - emergency-fund/liquidity status;
   - income and expense stability;
   - current holdings and concentration;
   - tax lots and potential tax constraints;
   - market-price freshness and historical coverage;
   - unresolved Guardian/data-quality issues;
   - knowledge-source availability;
   - algorithm readiness blockers.
2. Create an `InsightContextService` that produces a grounded, versioned snapshot.
3. Add a read-only endpoint such as `GET /api/insights/readiness` and, if useful, `GET /api/insights/context`.
4. Return only:
   - context readiness;
   - factual observations;
   - data-quality blockers;
   - required user decisions;
   - algorithm status `not_implemented`;
   - `recommendations: []`.
5. Persist context snapshots only when needed for reproducibility; hash inputs and retain data-as-of metadata.
6. Add authorization and user-scoping tests.
7. Add frontend TypeScript types for Plan 03 without creating the Insights screen.

### Algorithm boundary

Create:

`backend/services/insights/recommendation_algorithm.py`

The file must remain empty in Phase 2.5. It must not contain placeholder weights, mock forecasts, random allocations, a heuristic buy/sell list, an RL policy, or an executable `NotImplemented` service that is accidentally wired into production.

Do not register a `POST /api/insights/generate-recommendations` endpoint in this phase.

### Future algorithm questions that must be answered before implementation

- What is optimized: expected return, risk-adjusted utility, drawdown, or probability of goal attainment?
- What is the prediction horizon?
- Which investable universe is permitted?
- What liquidity, tax, concentration, turnover, and suitability constraints apply?
- How are expected returns and uncertainty estimated?
- What benchmark and walk-forward validation are used?
- How are survivorship bias, look-ahead bias, and data leakage prevented?
- What minimum evidence is required before any security or asset-class suggestion?
- How are recommendations reviewed, explained, expired, and evaluated?
- What regulatory position applies to personalized recommendations?

### Exit gate

- Plan 03 can build an honest Insights shell from a stable readiness/context contract.
- No endpoint can emit an investment recommendation.
- Empty or insufficient data cannot produce a plausible-looking allocation.

## 14. Phase 2.5-7 - Market-data professionalization

### Tasks

1. Replace the one-provider-per-asset map with a provider registry supporting ordered adapters per capability.
2. Define provider capabilities:
   - quote;
   - historical prices;
   - instrument metadata;
   - benchmark data;
   - rate limits;
   - expected delay;
   - licensed-for-production flag.
3. Add instrument normalization and provider-symbol mapping independent of holding rows.
4. Implement:
   - bounded retry with jitter;
   - circuit breaker;
   - provider timeout;
   - fallback provider where a valid alternative is configured;
   - last-known-good cache;
   - stale-age limits by asset class;
   - disagreement detection between providers;
   - provider health and latency metrics.
5. Never relabel delayed or cached data as live.
6. Persist provenance for each value: provider, original symbol, observation time, fetch time, status, and fallback reason.
7. Add provider contract tests using recorded safe responses and separate live staging tests.
8. Document the production data-source decision. If the project cannot fund a licensed provider, state the supported prototype/data-delay boundary rather than claiming exchange-grade live data.

### Readiness states

```text
configured
reachable
healthy
degraded
rate_limited
stale_only
unavailable
```

### Exit gate

- One provider outage does not corrupt holdings.
- Cached values are visibly stale and age-bounded.
- Provider errors and latency are measurable.
- Portfolio calculations record the exact price-history provider set.
- Documentation no longer uses the vague phrase "live availability is conditional" without detailed provider/freshness status.

## 15. Phase 2.5-8 - Parser coverage and import quality

### Tasks

1. Build a parser registry with explicit format/layout identifiers and versions.
2. Separate:
   - file-type detection;
   - document-family detection;
   - row/table extraction;
   - canonical mapping;
   - validation;
   - preview;
   - commit.
3. Create a sanitised golden corpus for every advertised format.
4. Include representative families for:
   - generic bank CSV/XLSX;
   - supported bank-specific exports;
   - generic broker tradebook/holding CSV;
   - supported broker-specific exports;
   - CAMS/KFintech text-based CAS layouts;
   - NSDL/CDSL CAS layouts when samples and legal use are available;
   - malformed, duplicate, partial, locale/date, and encoding cases.
5. Add OCR as an optional adapter for image-only PDFs. OCR output must carry confidence per field and always enter preview; low-confidence rows cannot auto-commit.
6. Define safe handling for encrypted statements. If password support is added, decrypt in memory, never store/log the password, and include the detailed control design in Plan 04.
7. Add mapping confidence, parser/layout version, and unsupported-layout reason to preview responses.
8. Add downloadable normalized data and row-error reports.
9. Fuzz delimiters, encodings, oversized fields, zip/XML structures, formulas, and malformed PDFs within bounded resources.
10. Publish a generated capability matrix; do not advertise a provider/layout until its golden tests pass.

### Quality gates

- 100 percent of golden files are classified into the expected document family.
- Required canonical fields reach the agreed per-family accuracy target; default target is at least 98 percent on approved fixtures.
- No invalid or low-confidence row is committed without explicit review.
- Duplicate/replay tests remain idempotent.
- Unknown layouts fail with an actionable reason rather than a misleading partial import.

## 16. Phase 2.5-9 - Production evidence and operational completion

### 16.1 CI

Add GitHub Actions or an equivalent pipeline for:

- backend unit tests;
- frontend ESLint;
- TypeScript checking;
- Next.js production build;
- dependency consistency;
- migration lint/order validation;
- secret scanning;
- agent/chat evaluation smoke subset;
- parser golden-corpus subset.

No deployment step is required until deployment architecture is approved.

### 16.2 Integration tests

Create marked integration suites for:

- staging Supabase and migrations 001 through the new Phase 2.5 migration;
- storage upload/delete lifecycle;
- Qdrant create/stage/query/promote/rollback;
- configured LLM structured-output contract;
- market-provider staging probes;
- worker job claiming and retries;
- SMTP adapter using a safe test sink;
- Upstox sandbox or controlled read-only account when credentials exist.

Hosted tests must use synthetic users, identify all created records, and clean up deterministically.

### 16.3 Worker and retention

1. Replace `retention_cleanup`'s `deleted: 0` stub with a storage-aware, idempotent implementation.
2. Record deletion attempt, object key hash, database row state, result, error class, and completion time.
3. Add worker heartbeat/lease information to readiness.
4. Expose due, running, failed, retrying, and dead-letter counts without exposing private payloads.
5. Test crash recovery and duplicate claims.

### 16.4 Observability

Emit structured, redacted events for:

- request and conversation IDs;
- route and selected agents;
- context version and missing-context codes;
- agent duration/status;
- grounding and arbitration outcomes;
- RAG collection/version and retrieval result count;
- provider status/freshness;
- parser/layout version and error category;
- worker run status;
- response latency and degraded dependencies.

Never log prompts containing raw financial rows, secrets, tokens, email attachments, or full model outputs by default.

### 16.5 Load and reliability baseline

Run bounded tests for:

- concurrent dashboard generation;
- chat requests with mocked and live-staging providers;
- bulk import preview within documented limits;
- knowledge ingestion;
- worker schedule claiming;
- notification streaming.

Record environment, dataset size, concurrency, p50/p95 latency, error rate, and resource usage. Do not publish universal performance claims from a laptop run.

### 16.6 Outcome evaluation boundary

1. Record immutable references to delivered predictions, warnings, model/rule versions, evidence, and `data_as_of`; do not store hidden reasoning.
2. Accept only explicitly defined, labelled realized outcomes with their observation window and source provenance.
3. Compute evaluation metrics against a versioned target and retain cohort size, exclusions, and limitations.
4. Emit drift signals and calibration proposals only after the approved minimum sample size is met.
5. Never apply a proposal automatically. Promotion requires review, a new model or rule version, validation evidence, and a rollback target.
6. Feed approved versions into later orchestration cycles while retaining reproducibility of prior outputs.

### Exit gate

- Every "incomplete production evidence" item has either a passing artifact or an explicitly approved deferral.
- CI is required on the main branch.
- Integration tests exist and are distinct from fake-provider unit tests.
- Retention cleanup performs and verifies actual deletions.
- Operators can determine why a service is degraded without reading application source.

## 17. Database migration plan

Add one ordered migration, provisionally:

`backend/migrations/007_phase_2_5_intelligence.sql`

Candidate tables:

- `agent_runs`
- `agent_claims`
- `agent_evidence`
- `agent_conflicts`
- `conversation_summaries`
- `knowledge_sources`
- `knowledge_documents`
- `knowledge_document_versions`
- `knowledge_ingestion_runs`
- `knowledge_reviews`
- `provider_health_observations`
- `insight_context_snapshots`

Constraints:

1. Use user scoping only where records contain or reveal private user context.
2. Public knowledge metadata must not contain private user data.
3. Enable RLS for user-linked tables.
4. Grant service-role access explicitly.
5. Define retention periods for verbose run/evidence data.
6. Do not persist chain-of-thought.
7. Store hashes or references instead of duplicating entire private records.
8. Include model, rule, parser, corpus, and contract versions required for reproduction.

Do not create all candidate tables automatically. Finalize the smallest schema after the contract phase and document every omitted table decision.

## 18. Suggested code organization

```text
backend/
  agents/
    contracts.py
    context_assembler.py
    intent_router.py
    coordinator.py
    grounding_checker.py
    consensus_arbiter.py
    response_composer.py
    policies.py
    specialists/
      portfolio.py
      tax.py
      cashflow.py
      guardian.py
  services/
    knowledge/
      registry.py
      discovery.py
      fetcher.py
      extractor.py
      differ.py
      publisher.py
      retrieval.py
    insights/
      context.py
      readiness.py
      recommendation_algorithm.py  # empty in Phase 2.5
    market_data/
      registry.py
      health.py
      policy.py
    parsers/
      registry.py
      detectors.py
      adapters/
  evaluations/
    chat_cases.jsonl
    routing_cases.jsonl
    expected_claims/
  tests/
    integration/
    fixtures/parsers/
```

Reuse current services rather than duplicating business logic. Specialist agents should wrap deterministic portfolio, tax, cash-flow, and Guardian services.

## 19. Testing matrix

### Unit

- Contract validation and serialization.
- Router classifications and fallback.
- Context requirements and redaction.
- Agent request limits and deduplication.
- Evidence/claim matching.
- Calculation recomputation.
- Conflict policies.
- Source allowlisting and document state transitions.
- Provider selection/fallback.
- Parser detection and canonical mapping.
- Insights readiness with algorithm absent.

### Integration

- Supabase user isolation and migrations.
- Real Qdrant staging lifecycle.
- Structured LLM response parsing and fallback.
- Worker concurrency and recovery.
- Storage retention deletion.
- Provider probes.
- End-to-end chat across multiple specialists.

### Adversarial

- Prompt injection inside public PDFs and imported statements.
- Cross-user conversation and evidence access.
- Invented citation and invented numeric claim.
- Malicious/oversized files and decompression limits.
- Qdrant unavailable, stale corpus, LLM unavailable, one-agent failure, provider disagreement.
- Requests for guaranteed returns or trade execution.

### Regression

- Existing 44 backend tests continue passing.
- Frontend lint, typecheck, and production build continue passing.
- Dashboard, import, notification, connector, and export behavior remains compatible.

## 20. Phase 2.5 security boundary versus Plan 04

Security cannot be postponed entirely because the new pipelines handle untrusted documents and sensitive context.

Phase 2.5 must implement:

- authorization and user scoping;
- context minimization/redaction;
- untrusted-document prompt-injection resistance;
- allowlisted knowledge fetches;
- resource and timeout bounds;
- audit events;
- secret-safe logging;
- output grounding;
- retention enforcement;
- dependency and secret scanning in CI.

Plan 04 will define the deeper security program, including:

- complete threat model and abuse cases;
- cryptographic/key lifecycle review;
- advanced fraud/threat algorithms;
- service-to-service identity and zero-trust controls;
- penetration testing;
- security monitoring and incident response;
- backup/restore and disaster recovery certification;
- privacy/compliance evidence and external review.

Phase 2.5 must leave versioned audit hooks and stable boundaries for Plan 04 rather than inventing premature "security algorithms."

## 21. Delivery order and stop gates

Execute in this order:

1. 2.5-0 Baseline and contracts.
2. 2.5-1 Context assembler and evidence registry.
3. 2.5-2 Dynamic router and coordinator.
4. 2.5-3 Grounding Checker and Consensus Arbiter.
5. 2.5-4 Automated knowledge pipeline.
6. 2.5-5 Chatbot upgrade and evaluation.
7. 2.5-6 Insights context scaffold.
8. 2.5-7 Market-data professionalization.
9. 2.5-8 Parser coverage.
10. 2.5-9 Production evidence and operational completion.
11. Contract freeze and Plan 03 handoff.

Do not start the next numbered phase until the current phase's exit gate is demonstrated. Market-data/parser work may be prepared in parallel only after common status and evidence contracts are frozen.

## 22. Plan 03 handoff contract

Plan 03 may begin final data-screen implementation when:

- Chat exposes stable structured analysis sections.
- Agent and RAG evidence can be displayed without parsing prose.
- Availability and freshness states are consistent.
- Qdrant and worker readiness are truthful.
- Insights readiness/context endpoints are stable and recommendations are explicitly unavailable.
- Market values expose provider, observation time, and fallback state.
- Parser capability is generated from passing fixtures.
- A synthetic demonstration user exercises complete, partial, stale, and unavailable states.
- CI and hosted smoke tests protect the baseline.

Plan 03 must not fabricate recommendation cards while the algorithm is absent.

## 23. Definition of done

- Keyword routing is no longer the primary routing mechanism.
- Relevant specialists are selected dynamically and communicate through bounded typed requests.
- Full decision context is mandatory for recommendation-like questions.
- All material response claims are grounded or visibly rejected.
- Agent conflicts are resolved by documented policies or returned unresolved.
- Qdrant readiness proves live collection state and corpus version.
- Public financial knowledge is sourced from authoritative registries and maintained automatically through a staged approval workflow.
- Regulatory-document ingestion cannot silently change executable tax rules.
- Chat evaluation results are reproducible and meet the minimum metrics.
- Insights context/readiness exists; the recommendation algorithm file is empty; no recommendation-generation route exists.
- Market provider health, freshness, fallback, and provenance are visible and tested.
- Parser support is backed by a versioned golden corpus and advertised from actual passing capability.
- Retention cleanup deletes eligible storage objects and records results.
- Delivered predictions can be compared with labelled realized outcomes; evaluation feedback is versioned and cannot silently recalibrate production behavior.
- CI, integration tests, observability, and bounded load-test evidence exist.
- Existing implemented workflows remain compatible.
- Plan 03 receives stable backend contracts and may proceed without hiding unfinished technical behavior.

## 24. Execution guardrails for an implementation agent

1. Read this entire plan and the current repository before changing code.
2. Do not implement Phase 2.5 as empty class shells, TODO functions, mocked production routes, or hard-coded success responses.
3. Do not add a Trading Agent, RL allocation policy, return forecaster, or recommendation heuristic.
4. Keep `recommendation_algorithm.py` empty and disconnected.
5. Reuse deterministic domain services; do not reimplement portfolio, tax, cash-flow, or Guardian calculations inside prompts.
6. Preserve existing API compatibility unless a migration is explicitly documented and tested.
7. Apply database changes through one ordered migration and verify the hosted schema separately.
8. Never commit credentials, downloaded private statements, production user data, or live test payloads.
9. Keep public knowledge and private user memory separate.
10. Never persist hidden reasoning or chain-of-thought.
11. Use authoritative official sources only for the initial regulatory registry.
12. Do not activate a materially changed regulatory document without a review record.
13. Every phase ends with tests, evidence, changed-file inventory, remaining limitations, and a stop for review.
14. Do not begin Plan 03 UI implementation while executing this plan.
15. Do not describe configured external services as operational unless the relevant live probe passes.

## 25. Copy-paste execution prompt

> Execute `02_5_TECHNICAL_STABILIZATION_AND_AGENT_INTELLIGENCE_IMPLEMENTATION_PLAN.md` strictly in numbered phases. Begin with Phase 2.5-0 and stop after its exit gate. Before editing, inspect the current implementation and produce a changed-file plan. Do not create skeleton services, TODO-only functions, fake success responses, random financial data, hard-coded recommendations, a Trading Agent, a return forecaster, or an RL allocation policy. Keep `backend/services/insights/recommendation_algorithm.py` completely empty and do not register a recommendation-generation endpoint. Preserve current API compatibility while introducing typed agent claims, evidence, requests, dynamic routing, grounding, bounded arbitration, and truthful dependency states. Reuse existing deterministic portfolio, tax, cash-flow, Guardian, import, market, and notification services. Every material numerical claim must have recomputable evidence. Treat downloaded and uploaded documents as untrusted data. End each phase with tests, exact commands/results, migration status, changed files, limitations, and confirmation that the next phase has not started.

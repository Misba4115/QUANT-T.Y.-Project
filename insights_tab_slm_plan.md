# Insights & Trading Tab — Updated Plan (SLM-Backed Predictive Guidance + Investment Recommendations)

*Replaces the previous tiered-build plan. Recentered on pretrained Small Language Models (SLMs) from HuggingFace as the forecasting backbone, aligned with the project synopsis and the GC-SEC algorithm architecture. Expanded to cover two distinct output layers: trading signals and investment recommendations.*

---

## 1. The one-line pitch (updated)

Dashboard tells the user **what they have**. Insights & Trading tells them **what to do about it, and why** — split into two complementary layers: **trading signals** (what the market looks like right now, for assets they already hold) and **investment recommendations** (what they should consider doing next, based on their goals, finances, and risk profile). Both layers are grounded through GC-SEC before reaching the screen.

---

## 2. What this tab outputs — two layers, five outputs

The tab is structured as two distinct layers. They share the same GC-SEC verification pipeline but draw on different inputs and answer different questions.

### Layer A — Trading Signals (market-facing, price-driven)

| Output | Plain description |
|---|---|
| **Return forecast with confidence band** | Direction + range per asset class the user actually holds (e.g. Equity: +2–5% over 30 days, Medium confidence). Powered by Kronos-small / NSE-LSTM. |
| **Rebalance actions** | Concrete buy/hold/reduce suggestions for current holdings, with tax impact pre-checked via the Tax Engine |

### Layer B — Investment Recommendations (user-facing, goal-driven)

| Output | Plain description |
|---|---|
| **Goal alignment check** | Are the user's current holdings tracking toward their stated financial goals? (e.g. "You are 18% short of your ₹50L retirement target at current pace") |
| **New instrument suggestions** | Recommendations for asset classes or instrument types the user is not currently exposed to but should consider, given their risk profile, income, and goals |
| **Priority action** | One plain-language priority: the single most impactful change the user could make right now, explained in non-jargon terms |

> **Advisory only — no trade execution.** Both layers are decision-support tools. This is a stated scope boundary, not a limitation.

---

## 3. The core change: replacing a built-from-scratch model with pretrained SLMs

The previous plan assumed we'd build or fine-tune a time-series model ourselves (LSTM, Transformer encoder, or PPO RL agent). That's realistic if you have weeks of training compute and a clean labelled dataset — neither of which this project has at scale.

**The new approach:** load a pretrained SLM from HuggingFace and use it as the forecasting component directly, wrapping it in the same GC-SEC pipeline that already governs everything else in QUANT. This is the intellectually honest move: using state-of-the-art pretrained models is what real quant systems do. Building your own from random initialisation to compete against a pretrained model is an academic exercise that weakens your system.

For the paper, this framing is actually stronger: **"we evaluated which pretrained SLM best serves an Indian retail investor's portfolio guidance needs, integrated it into a grounded verification pipeline, and measured the added value of GC-SEC's three steps on top of raw model output."** That is a real contribution.

---

## 4. Candidate SLMs — evaluation matrix

The four models you identified map onto distinct roles. Here is a precise breakdown of what each actually does and where it fits in the pipeline:

| Model | Type | What it actually produces | Role in QUANT | Flags |
|---|---|---|---|---|
| **klok123/Kronos-small** | Transformer (time-series) | OHLCV candlestick forecasts across multiple markets | **Primary forecaster** — takes price history for user's held assets, outputs return direction + range | Best-fit for the core forecasting job; verify its input tokenisation format before committing |
| **thoutam/nse-lstm-model** | LSTM | NSE stock price forecasting | **Baseline comparator** — run it alongside Kronos-small for ablation; its NSE focus aligns with Indian-market data | Inspect preprocessing carefully — if it was trained on a specific normalisation, replicate it exactly or outputs will be garbage |
| **SatyamSinghal/financial-ttm** | Transformer | Price + volatility + confidence + risk score | **Risk layer augmentation** — its confidence and risk outputs can feed directly into the Grounding Checker's threshold logic | Model card notes synthetic training data; treat its outputs as soft signals, not ground truth — document this explicitly in the paper |
| **deotech/StocK_Advisor** | Fine-tuned Gemma LLM | Market analysis + investment-style text explanations | **Explanation generator** — takes the numerical forecast output and generates the plain-language "why" shown to the user | Not a numerical forecaster — do not pipe it raw OHLCV data. It is the narration layer, not the prediction layer |

> **Do not conflate roles.** Kronos-small / NSE-LSTM produce numbers. StocK_Advisor produces words explaining those numbers. Mixing these up is a paper-level mistake reviewers will catch.

---

## 5. Revised architecture — how the models plug into GC-SEC

```
User opens Insights tab
        │
        ▼
[Price Fetch] ─── yfinance / Upstox connector (already built)
        │
        ▼
[Feature Builder] ── OHLCV history + technical indicators (RSI, MACD, BB)
        │             from user's actual holdings (Supabase)
        ▼
[SLM Forecaster — Kronos-small]
  → Return direction + range per asset class
  → Confidence score
        │
        ├──[Parallel: NSE-LSTM baseline for same inputs]  ← ablation only
        │
        ▼
[Risk Augmentation — financial-ttm]
  → Volatility estimate + risk score
        │
        ▼
──────────────── GC-SEC PIPELINE ─────────────────
│                                                 │
│  Step 1: Grounding Checker                      │
│  - Every numeric output from SLMs is            │
│    cross-checked against Portfolio Analytics'   │
│    actual computed covariance/CVaR values        │
│  - If SLM says "high volatility" but PA says    │
│    σ = 8%, the PA value wins — SLM is a signal, │
│    not a source of truth                         │
│                                                 │
│  Step 2: Consensus Arbiter                      │
│  - SLM recommendation vs. Tax Engine state      │
│    (would this trigger an avoidable tax hit?)   │
│  - SLM recommendation vs. user risk profile     │
│  - Conflict resolved by constraint priority:    │
│    regulation > risk profile > return           │
│                                                 │
│  Step 3: Outcome Evaluator                      │
│  - Recommendation logged as prediction          │
│  - 30-day later: actual vs. predicted           │
│  - Calibration update: adjust confidence        │
│    thresholds per model per user                │
│                                                 │
──────────────────────────────────────────────────
        │
        ▼
[Explanation Generator — StocK_Advisor / Gemma]
  → Plain-language "why" narrative
  → Grounded against the verified numbers
        │
        ▼
[Insights Tab UI]
  → Forecast card (direction, range, confidence)
  → Rebalance suggestion card
  → Tax impact note (from Arbiter)
  → "Why this?" explanation panel
```

### Layer B pipeline — Investment Recommendations

```
User opens Insights tab
        │
        ▼
[User Context Builder]
  → Goals from Supabase (financial_goals table)
  → Risk profile from user preferences
  → Current holdings summary (equity, MF, ETF, crypto)
  → Cashflow snapshot: monthly income − expenses − surplus
  → Tax Engine state: any impending STCG/LTCG constraints
        │
        ▼
[Goal Gap Calculator]
  → For each goal: target amount, current corpus, time remaining
  → Required monthly SIP / lump sum to close the gap
  → Current trajectory vs. required rate of return
        │
        ▼
[Instrument Recommender — StocK_Advisor / Gemma]
  → Receives: goal gaps, risk profile, cashflow surplus, current
    asset allocation, and the Layer A forecast (market context)
  → Generates: specific instrument type suggestions
    (e.g. "Consider adding a Nifty Next 50 index fund for
    long-term equity growth; your current equity is 100%
    large-cap which underweights mid-cap growth potential")
        │
        ▼
──────────────── GC-SEC PIPELINE (shared with Layer A) ────
│                                                          │
│  Step 1: Grounding Checker                               │
│  - Every number in the recommendation is verified        │
│    against the Goal Calculator's actual output           │
│  - If StocK_Advisor claims "you need ₹8,000/month"      │
│    but the Goal Calculator says ₹9,400, the calculated  │
│    figure replaces the LLM's claim                       │
│                                                          │
│  Step 2: Consensus Arbiter                               │
│  - Does the recommendation conflict with the Tax Engine? │
│    (e.g. "invest more" but user has a liquidity crunch   │
│    from an impending tax liability)                      │
│  - Does it violate the user's stated risk profile?       │
│  - Constraint priority: regulation > risk > return       │
│                                                          │
│  Step 3: Outcome Evaluator                               │
│  - Goal gap logged at time of recommendation             │
│  - 90-day check: did the user's gap improve or widen?    │
│  - Calibration: adjust recommendation aggressiveness     │
│    per user based on realised outcomes                   │
│                                                          │
───────────────────────────────────────────────────────────
        │
        ▼
[Insights Tab UI — Layer B panel]
  → Goal tracker card (target / current / gap / trajectory)
  → "What to consider" card (instrument suggestions)
  → Priority action card (single top recommendation)
  → "Why this?" explanation (from StocK_Advisor, grounded)
```

---

## 5a. Why two layers — and why they are NOT the same thing

This is the question a guide will ask, so it needs a crisp answer ready:

| | Layer A — Trading Signals | Layer B — Investment Recommendations |
|---|---|---|
| **Driven by** | Market price data (OHLCV) | User goals, income, holdings, and risk profile |
| **Time horizon** | Short to medium (30-day forecast) | Medium to long (goal timeline: months to years) |
| **Primary model** | Kronos-small / NSE-LSTM (time-series SLMs) | StocK_Advisor / Gemma (language SLM) + Goal Calculator |
| **Question answered** | "Is now a good time to hold/reduce/buy these assets?" | "Am I on track for my goals? What should I add or change?" |
| **Ground truth for Grounding Checker** | Portfolio Analytics covariance/CVaR | Goal Calculator + Cashflow Engine actuals |
| **Tax Engine integration** | Pre-checks rebalance actions for STCG/LTCG impact | Pre-checks whether a suggested investment affects tax year liabilities |

They share the same GC-SEC verification, the same Consensus Arbiter, and the same Outcome Evaluator — so there is no duplicated logic. The difference is purely in what data goes in and what question is being answered.

---

## 6. Revised build tiers (both layers, same safety structure)

| Tier | Layer A (Trading Signals) | Layer B (Investment Recommendations) | Demoable? |
|---|---|---|---|
| **Tier 1 (must finish)** | Feature builder + Kronos-small + Grounding Checker wired to Portfolio Analytics | Goal Gap Calculator + StocK_Advisor prompt wired to user goals + Grounding Checker on output | Yes — both layers produce grounded output |
| **Tier 2 (strong finish)** | + financial-ttm risk augmentation + Consensus Arbiter with Tax Engine | + Cashflow Engine integration (disposable income aware) + Arbiter checks goal recommendations against tax state | Yes — full GC-SEC pass on both layers |
| **Tier 3 (stretch)** | + NSE-LSTM baseline for ablation + calibration loop on forecast accuracy | + Outcome Evaluator on goal gap (90-day check) + calibration on recommendation aggressiveness | Yes — closes GC-SEC Step 3 for both layers |

**Priority order if time runs short:** Tier 1 of Layer A first (trading signals are the headline feature), then Tier 1 of Layer B (goal gap + recommendation), then Tier 2 of both. Tier 3 is explicitly stretch/future work.

**If Tier 3 does not get finished:** Tier 1+2 on both layers is a complete, defensible system. The paper's Step 3 discussion becomes "calibration loop designed and instrumented; full outcome data requires a 90-day deployment window beyond the project timeline" — a completely honest and expected academic framing.

---

## 7. HuggingFace integration — practical notes

### Loading the models

All four models are standard HuggingFace `transformers` / `torch` checkpoints. The backend already has Python/FastAPI; add to the existing `requirements-ml.txt`:

```
transformers>=4.40.0
torch>=2.2.0
huggingface_hub>=0.22.0
einops  # needed by some transformer variants
```

Load at startup (not per-request) and cache in memory — these are SLMs, not LLMs, inference should be fast enough for session-triggered use.

### Input format — what each model expects

| Model | Input format | Your preprocessing job |
|---|---|---|
| Kronos-small | OHLCV candlestick sequences (K-line format) | Pull from price cache / yfinance, normalise to model's expected window length |
| NSE-LSTM | Sequence of daily close prices (NSE tickers) | Ticker mapping — your holdings are stored with symbol; map to NSE format |
| financial-ttm | Price + volume sequences | Similar to Kronos-small; check if it expects log-returns or raw prices |
| StocK_Advisor (Gemma) | Text prompt | Construct prompt from verified numeric output |

**Preprocessing warning:** LSTM and time-series transformer models are brittle to normalisation mismatches. If the model was trained on min-max scaled data and you feed it raw prices, it will output nonsense confidently. Inspect each model's training notebook or model card for the normalisation scheme before wiring it up.

### Inference endpoint design

Expose as an internal FastAPI service, not called directly from the frontend:

```
POST /api/insights/generate
  → triggers Feature Builder → SLM Forecaster → GC-SEC pipeline
  → returns verified recommendation JSON

GET /api/insights/latest
  → returns last computed recommendation (cache, no recompute)
  → used for fast tab-open without triggering full pipeline
```

Session-triggered re-evaluation logic (same decision as before): recompute only if price delta > threshold since last run. Show cached result otherwise.

---

## 8. What the NSE-LSTM model contributes specifically

The `thoutam/nse-lstm-model` is particularly well-suited to your project because your user base is Indian retail investors holding NSE-listed equities — the same market it was trained on. This is a concrete, defensible reason to prefer it as a baseline over a generic LSTM you would build yourself.

Its role in the paper: **it is the Tier 1 baseline.** You report Kronos-small's performance against it. If Kronos-small (a more advanced architecture) does not outperform NSE-LSTM on your held-out data, that is an honest, interesting result — real quant research finds this kind of thing all the time. "Simpler model wins on this specific market" is publishable.

---

## 9. What financial-ttm's risk outputs feed into GC-SEC

financial-ttm's volatility + confidence + risk score outputs have a direct home in the Grounding Checker's existing logic:

- **Confidence score** → sets the epsilon threshold for Step 1 (low model confidence = tighter cross-check required against Portfolio Analytics values)
- **Risk score** → feeds the Consensus Arbiter's constraint evaluation: if model-predicted risk exceeds user's stated risk tolerance, the Arbiter flags it before the recommendation surfaces
- **Volatility estimate** → cross-checked against Portfolio Analytics' computed σ; if they diverge by more than a calibrated threshold, the system reports the discrepancy to the user rather than silently picking one

Since financial-ttm's model card acknowledges synthetic training data, in the paper you should document this as a known limitation and state that you treat its outputs as auxiliary signals, cross-validated against empirically computed values from the Portfolio Analytics engine. That is not a weakness — that is exactly what GC-SEC's Grounding step is for.

---

## 10. StocK_Advisor — the right use and the wrong use

**Right use:** takes verified, grounded numbers from Steps 1–2 and generates a plain-language explanation. Prompt pattern:

```
"Based on the following verified forecast for [user's portfolio]:
 - Equity (Nifty 50): forecast +3.2% ± 1.5% over 30 days, confidence 72%
 - Debt (liquid funds): forecast +0.6% ± 0.2%, confidence 85%
 - Risk assessment: moderate (current volatility: σ=14%)
 - Tax constraint: selling X before [date] would trigger STCG of ₹Y
 
 Generate a clear, jargon-free rebalancing suggestion for a retail investor."
```

**Wrong use:** do not feed it raw market data and ask it to produce a forecast. It is a fine-tuned Gemma LLM trained to *explain* financial advice in natural language — using it as a price predictor is a category error that would produce confidently-worded hallucinated numbers, the exact failure mode GC-SEC exists to prevent.

The Grounding Checker still runs on StocK_Advisor's output, specifically checking that any numeric claim it makes in its explanation matches the verified forecast inputs it was given.

---

## 11. How this serves the GC-SEC paper narrative

The SLM approach actually strengthens the paper's novelty argument:

| Previous claim | Updated (stronger) claim |
|---|---|
| "We built a forecasting model" | "We evaluated a suite of pretrained SLMs and composed them into a verified prediction pipeline" |
| "Our RL policy self-evolves" | "GC-SEC's calibration loop adjusts model confidence weights based on realised outcomes — model-agnostic, works with any forecaster" |
| "We predict return ranges" | "We predict return ranges, grounded against empirically computed values, with model uncertainty explicitly surfaced to the user" |

The paper's research question becomes: **does wrapping pretrained SLM output in GC-SEC's three-step verification pipeline produce recommendations that are more accurate, more consistent with user constraints, and more calibrated over time than raw SLM output alone?** That is a clean, falsifiable, defensible research question.

---

## 12. Evaluation — what you measure and how

### Layer A — Trading Signal metrics

| Metric | What it tests | How to compute |
|---|---|---|
| **Directional accuracy** | Does the forecast get up/down right? | Compare predicted direction to realised 30-day return; track across backtest window |
| **RMSE on return estimate** | How far off is the return range midpoint? | Against realised returns on held-out period |
| **Grounding correction rate** | How often does Step 1 catch a discrepancy between SLM output and PA-computed values? | Log every check; count flags |
| **Arbitration trigger rate** | How often does Step 2 override a recommendation due to tax/risk constraint? | Log every Arbiter decision |
| **Model comparison** | Kronos-small vs. NSE-LSTM on the same backtest window | Side-by-side RMSE + directional accuracy |

### Layer B — Investment Recommendation metrics

| Metric | What it tests | How to compute |
|---|---|---|
| **Goal gap accuracy** | Is the calculator's gap figure correct? | Exact-match against hand-computed expected values from test set (same pattern as bench_tax_engine.py) |
| **Recommendation grounding rate** | How often does StocK_Advisor's numeric claims get corrected by the Goal Calculator's actual output? | Log every Step 1 check on Layer B output |
| **Recommendation relevance** | Does the suggestion actually address the user's largest goal gap? | Manual review on a held-out set of synthetic user profiles |
| **Arbiter override rate** | How often does a Layer B suggestion get modified because of a tax or liquidity constraint? | Log every Arbiter decision specific to Layer B |

### Shared metrics (both layers)

| Metric | What it tests |
|---|---|
| **Calibration drift** | Does prediction accuracy / goal gap estimate improve after Step 3 runs? Compare cycle 1 vs. cycles 5, 10 |
| **Layer A / Layer B conflict rate** | How often does the Arbiter detect a contradiction between the trading signal ("sell equity") and the investment recommendation ("buy more equity for retirement")? This is a strong paper result — showing the Arbiter earns its keep |

---

## 13. Anticipated guide questions — updated answers

| Likely question | Answer |
|---|---|
| "Are you predicting stock prices?" | No — we forecast return direction and ranges using pretrained time-series models (Kronos-small, NSE-LSTM), then ground those outputs against our portfolio analytics engine before showing them to the user |
| "What is the difference between your trading signals and your investment recommendations?" | Trading signals are market-facing and price-driven — they answer "is now a good time to hold or rebalance?" Investment recommendations are goal-driven — they answer "am I on track for my financial goals and what should I add?" Different inputs, different models, different time horizons, same GC-SEC verification pipeline |
| "Why not build your own model?" | Using state-of-the-art pretrained SLMs is the industry-standard approach; our contribution is the verification and constraint pipeline (GC-SEC) that wraps them, not the forecasting model itself |
| "Isn't StocK_Advisor just a chatbot?" | In Layer A it is the explanation layer — narrating verified forecast numbers. In Layer B it is the recommendation generator — proposing instrument suggestions based on goal gap analysis. In both cases its outputs pass the Grounding Checker before reaching the user |
| "What if the SLM output is wrong?" | That is precisely what the Grounding Checker exists for — it cross-checks every SLM numeric output against Portfolio Analytics' computed values (Layer A) or the Goal Calculator's actual output (Layer B) before it reaches the user |
| "What is novel here vs. just calling a HuggingFace model?" | Any app can call a model. GC-SEC is what makes this a research contribution: grounded verification, constraint-priority arbitration, and outcome-based recalibration as one defined procedure — applied across two different output domains (trading signals and goal-based recommendations) |
| "Can the trading signal contradict the investment recommendation?" | Yes — and that is a feature, not a bug. The Consensus Arbiter is specifically designed to detect and resolve these cross-layer conflicts before either reaches the user. We log every such conflict; the conflict rate is itself a benchmark metric |

---

## 14. What stays the same from the original plan

- **Session-triggered re-evaluation** (not background polling) — unchanged, correct scope decision
- **Advisory only, no trade execution** — unchanged
- **GC-SEC pipeline** — Grounding Checker → Consensus Arbiter → Outcome Evaluator — unchanged; SLMs slot into it
- **Reuses Portfolio Analytics covariance/CVaR** — unchanged; these are the ground-truth values for Step 1
- **Same LangGraph orchestration** — the Trading/Allocation Agent runs as the 5th agent, same pattern
- **Chatbot intent route** — insights queries still route through the same Grounding + Arbiter pipeline

---

**Bottom line:** the tab now has two complementary layers — trading signals (market-driven, SLM-powered forecasts on current holdings) and investment recommendations (goal-driven, LLM-powered suggestions based on the user's actual financial situation). Both pass through the same GC-SEC pipeline, which means the Arbiter can catch cross-layer conflicts ("the trading signal says reduce equity; the investment recommendation says buy more equity for retirement") before either output reaches the user. That conflict-resolution capability is itself a research contribution, and it is something no single-purpose robo-advisor or price prediction tool does.

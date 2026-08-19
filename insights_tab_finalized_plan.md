# Insights & Trading Tab — Finalized Plan

*Prepared for guide review — covers what we're building, which algorithm does what, why each one was chosen, and how it fits the existing system.*

---

## 1. The one-line pitch

Dashboard tells the user **what they have**. Insights & Trading tells them **what to do about it, and why** — a personalized allocation recommendation, backed by a forecast, checked against tax and risk rules before it's ever shown.

## 2. What this tab actually outputs (three things, not one)

| Output | Plain description |
|---|---|
| **Allocation recommendation** | "What, how, how much to invest" — e.g. shift from 60/30/10 equity/debt/gold to 55/35/10 |
| **Return forecast** | Expected return **range** per asset class over a horizon (e.g. 30 days), not a single predicted price |
| **Rebalance actions** | Concrete buy/sell/hold suggestions, with tax impact already factored in |

We are explicitly **not** predicting exact future prices — that's neither realistic (efficient market hypothesis) nor defensible in an academic setting. We predict return *ranges* with confidence bands, which is the standard approach in real quant systems.

## 3. New component: Trading/Allocation Agent

- Runs as a 5th agent alongside the existing Guardian, Portfolio Analytics, Tax Engine, Cashflow Engine — same LangGraph orchestration, same pattern
- **Reuses Portfolio Analytics' existing covariance/CVaR calculations** rather than recomputing them — avoids duplicated logic, keeps the two engines consistent with each other
- Its output passes through the **same Grounding Checker and Consensus Arbiter** already built for Dashboard — no new verification logic needed, this is the payoff of having built those as shared layers rather than Dashboard-specific ones

## 4. Algorithm stack — what, why, and when each one gets built

We're building this in three tiers, in order, so we always have a working demo even if we run out of time before the later tiers.

| Tier | Algorithm | What it does | Why this algorithm |
|---|---|---|---|
| **Tier 1** | Statistical baseline — exponentially-weighted mean return + existing Ledoit-Wolf covariance | Return/risk estimate using pure historical data | Establishes the baseline our paper compares everything else against. Already have the pieces from Portfolio Analytics — near-zero extra build time |
| **Tier 2** | LSTM or small Transformer encoder | Forecasts next-period return per asset class from price history + macro features | Learns patterns in price trends a static historical average can't capture (momentum, mean-reversion). Standard, well-documented, realistic to train in weeks not months |
| **Tier 3** | PPO (Proximal Policy Optimization) reinforcement learning agent | Learns allocation weights directly: state = holdings + risk profile + Tier 2 forecast, action = target weights, reward = risk-adjusted return minus turnover cost | This is what makes the system "self-evolving" — the policy improves from outcomes over time, rather than just applying a fixed formula. PPO specifically chosen over DDPG for training stability, easier to tune with limited compute |

**If Tier 3 doesn't get finished in time:** Tier 1 + 2 is still a complete, demoable, defensible system on its own. Tier 3 becomes "future work" in the paper rather than a missing deliverable — this is a safe scoping decision to state upfront.

## 5. How a recommendation actually gets generated (step by step)

1. User opens the Insights tab (or logs in)
2. System fetches latest prices — checks if anything's moved enough since the last recommendation to justify recalculating (see §6)
3. If yes: Tier 2 forecaster estimates return ranges per asset class
4. Tier 3 policy (or Tier 1/2 optimizer if RL isn't built yet) converts that into target allocation weights
5. Output passes through **Grounding Checker** — every number is checked against what was actually computed, not just narrated by the LLM
6. Output passes through **Consensus Arbiter** — checked against Tax Engine's current state (e.g. would this trigger an avoidable tax hit?) and reconciled if there's a conflict
7. **Outcome Evaluator** logs this recommendation as a prediction, to be checked against what actually happens later
8. User sees: recommendation + a plain-language explanation of *why* (driven by which forecast inputs mattered most, and any tax/risk tradeoff the Arbiter applied)

## 6. Real-time behavior — session-triggered, not background polling

**Decision made:** re-evaluation happens when the user opens the tab or logs in — not on a continuous background schedule. This was chosen deliberately for scope reasons — realistic for a student project, avoids running always-on infrastructure, and is honest about what a personal-use tool should do (no app should be waking anyone up at 2am over a price move).

- On open: fetch latest prices, compare against the last saved recommendation
- If nothing moved meaningfully → show yesterday's recommendation, no recompute (fast, cheap)
- If something moved meaningfully (e.g. >3–5% price change) → recompute and show what changed and why

**Known limitation to state upfront, not hide:** if the user doesn't open the app for several days, they won't hear about a price move during that gap. This is a stated scope boundary, not an oversight — continuous monitoring is mentioned as a natural future extension, not something we're claiming to have built.

## 7. Why this is not "just a stock predictor"

Three things distinguish this from a naive prediction tool, and these are the actual talking points for defending novelty:

1. **It never gives a raw, ungrounded number** — everything passes the Grounding Checker first
2. **It never gives advice in isolation** — the Arbiter checks it against tax and risk constraints before showing it, so "sell now" can't contradict "don't sell, you'll trigger tax" elsewhere in the same app
3. **It's accountable over time** — every recommendation is logged and checked against what actually happened, feeding back into recalibration (this is the self-evolving piece)

## 8. Scope statement — advisory only

This system produces **recommendations**, not trade execution. No orders are placed on the user's behalf. This is a deliberate scope decision: it keeps the project's liability and complexity realistic for an academic setting, and it's the honest framing — the system is a decision-support tool, not a trading bot.

## 9. How we'll evaluate this (ties into the broader benchmarking plan)

- **Tier 1 vs Tier 2 vs Tier 3 comparison** on backtested historical data: which produces better realized Sharpe ratio, lower forecast error (RMSE on return estimates)
- **Grounding Checker correction rate** specific to this tab — how often it catches an unverified number before it reaches the user
- **Recommendation staleness** — how often session-triggered re-evaluation actually changes the recommendation vs. shows the same one

## 10. Anticipated guide questions — prepared answers

| Likely question | Answer |
|---|---|
| "Are you predicting stock prices?" | No — we predict return ranges with confidence bands, not point prices. Point-price prediction isn't reliable or academically defensible |
| "Is this real-time?" | Near-real-time, triggered on login/tab-open by design choice, not continuous background monitoring — a stated scope decision, not a limitation we're hiding |
| "What if two agents disagree?" | The Consensus Arbiter resolves it using a fixed priority order (regulatory/tax rules first, then risk profile, then return optimization) |
| "How do you know the model isn't hallucinating a number?" | Every output passes the Grounding Checker, which cross-verifies numeric claims against the actual computed values before display |
| "What's actually novel here vs. existing robo-advisors?" | The combination of grounded generation + constrained consensus + self-evolving calibration as one pipeline — most systems do at most one of these three |
| "What happens if the RL tier isn't finished?" | Tier 1+2 is a complete, working system on its own; Tier 3 is explicitly scoped as a stretch goal / future work |

---

**Bottom line for tomorrow:** the tab is fully scoped, the algorithm choices are justified tier-by-tier with a fallback if time runs short, and it plugs into verification infrastructure that already exists rather than requiring anything new to be built for safety/correctness.

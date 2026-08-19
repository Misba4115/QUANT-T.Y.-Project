# GC-SEC: Grounded Consensus with Self-Evolving Calibration

*Our original algorithm — formal definition for mentor discussion and paper writing.*

---

## 1. The one-line definition

**GC-SEC is a three-step decision procedure that takes multiple agents' raw recommendations and produces one verified, conflict-free, and self-correcting output** — by grounding every numeric claim against source data, resolving disagreement through constraint-priority arbitration, and adjusting each agent's future behavior based on whether past outputs turned out to be right.

This is the algorithm. Not the agents, not the app — this three-step procedure is what you built and what gets published.

## 2. Why this counts as "our own algorithm," not just an architecture

Your base paper (the agentic reasoning survey) describes three *categories* of technique — grounding/tool-use, collective consensus, self-evolving adaptation — as separate, independently-studied approaches. It does not specify how to combine them, and does not define a concrete decision rule for any of the three.

**GC-SEC is a specific, formalized procedure**, with defined inputs, outputs, and update rules (below) — that's the difference between "we used some ideas from a survey" and "we defined an algorithm." A survey names a category; you're contributing the actual function.

## 3. Formal definition

**Inputs:**
- A set of agents producing candidate recommendations: `r1, r2, ..., rn`
- Each recommendation contains numeric claims: `C_i = {c1, c2, ...}`
- A source-of-truth function `G()` that returns the actual computed value behind any claim
- A constraint set `K` (hard rules — tax law, regulatory limits, user risk bounds)
- A priority ordering `P` over constraint types (e.g. regulation > risk profile > return)
- Per-user calibration parameters `θ_u`, updated over time

**Step 1 — Grounding**
For every numeric claim `c` in every agent's output, check it against the real computed value:

```
for each claim c in C_i:
    g = G(c)                          # the true value from the tool/DB
    if |c - g| > epsilon:
        flag or replace c with g      # claim is not admitted forward
```

Only claims that pass this check move to Step 2. This is what stops hallucinated numbers from ever reaching arbitration or the user.

**Step 2 — Constrained Consensus**
Grounded recommendations may still conflict (e.g. "sell now" vs. "wait, avoid tax"). Resolve using priority-ordered constraints, not free-form negotiation:

```
def arbitrate(r1, r2, ..., rn, K, P):
    candidates = [r for r in [r1...rn] if satisfies(r, K)]
    if len(candidates) == 0:
        return modify_lowest_priority_conflict(r1...rn, P)
    return highest_utility(candidates)
```

The key design decision: conflicts are resolved by **constraint priority**, not by majority vote or LLM debate — this is what makes the arbitration deterministic and auditable, which matters a lot for a finance application and is a concrete, defensible design choice for the paper.

**Step 3 — Self-Evolving Calibration**
After the outcome is known (e.g. 30 days later), compare prediction to reality and update:

```
θ_u(t+1) = θ_u(t) + α * (outcome(t) - prediction(t))
```

This is an online update rule (similar in spirit to exponential smoothing / a simple bandit update) — `θ_u` represents things like the agent's risk-tolerance mapping or confidence threshold for this specific user, and `α` is a learning rate controlling how fast the system adapts. This closes the loop: the next Step 1–2 cycle for this user starts from updated parameters.

## 4. Where the RL policy fits in

The Insights tab's PPO allocation policy (Tier 3, from your architecture doc) is a **concrete instantiation of Step 3** — its reward signal is quite literally `(outcome - prediction)` from the same calibration update, applied to allocation weights specifically rather than to a general confidence parameter. This is a strong point to make to your mentor: it's not two separate ideas, the RL policy is GC-SEC's Step 3 specialized for one agent.

## 5. What makes this publishable

| Claim | Why it holds up |
|---|---|
| Novel combination | No existing system implements grounding + constraint-priority arbitration + outcome-based recalibration as one procedure with these specific update rules |
| Formalized, not just described | Steps 1–3 above have concrete functions/pseudocode, not just prose description — reviewers can evaluate it as an algorithm |
| Falsifiable / testable | Each step has a measurable effect: hallucination rate (Step 1), conflict resolution rate (Step 2), calibration drift over time (Step 3) — this gives you a clean ablation study |
| Domain-grounded | Applied to a genuinely constraint-heavy domain (financial regulation + tax law), which is exactly where constraint-priority arbitration matters most — not an arbitrary choice of application |

## 6. Ablation study — how you'll prove each piece matters

| Configuration | What it tests |
|---|---|
| Baseline (no GC-SEC — current independent-agent system) | Reference point |
| + Step 1 only (grounding) | Does hallucination rate actually drop? |
| + Step 1 + 2 (grounding + arbitration) | Does conflict rate drop, without hurting recommendation quality? |
| + Step 1 + 2 + 3 (full GC-SEC) | Does prediction accuracy improve over multiple cycles (calibration working)? |

This table is your results section. Each row is one experiment you already have the test sets to run.

## 7. What to say to your mentor tomorrow

*"Our algorithm is GC-SEC — a three-step procedure: grounding every numeric claim against source data, resolving agent conflicts through constraint-priority arbitration, and recalibrating each agent's parameters based on outcome feedback using this update rule [point to Step 3's equation]. It's not just an architecture — it's a defined decision procedure with measurable steps, and we can prove each step's contribution through the ablation study. The base survey names these as three separate technique categories; we're contributing the specific combined algorithm and its update rules."*

This directly answers "build your own algorithm" — GC-SEC is yours: the grounding check, the priority-based arbitration function, and the calibration update rule are all specific choices you made and can defend, not something copied from the base paper.

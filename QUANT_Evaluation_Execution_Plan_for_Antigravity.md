# **QUANT — Evaluation Execution Plan** 

### _Antigravity Testing & Experimental Validation_ 

**Purpose.** Execution-oriented version of the approved Paper Scope & Evaluation Plan. The cases and metrics below are a testing plan, not established results. Run reproducibly and retain raw outputs. 

## **1. Research Questions** 

- RQ1 → Experiment A: Does GC-SEC reduce unsupported/inconsistent financial outputs? 

- RQ2 → Experiment B: Does multi-agent orchestration route and complete queries correctly? 

- RQ3 → Experiment C: Are core financial components correct on controlled test sets? 

- RQ4 → Experiment D: Do implemented security controls withstand representative attacks? 

## **2. Non-Negotiable Rules** 

- Freeze the baseline code version and record the commit hash. 

- Freeze test cases and ground-truth labels before final metric collection. 

- Run existing benchmarks first and save raw outputs, including poor results. 

- Define metrics before looking at final results. 

- Use identical test protocols for before/after comparisons. 

- Document every code/model change and rerun the same frozen tests. 

- Do not hide failures or select only successful examples. 

- Do not claim universal accuracy, optimality, or complete security. 

- Security results are validation of the tested threat cases only. 

- Do not claim live calibration improvement without real longitudinal outcomes; use simulated replay if necessary. 

## **3. Experiment A — GC-SEC Ablation & Reliability** 

Goal: isolate the effect of each GC-SEC stage and measure reliability benefit plus runtime/LLM cost. 

|**Configuration**|**Grounding**|**Arbitration**|**Calibration**|**Purpose**|
|---|---|---|---|---|
|Baseline|No|No|No|Ungrounded multi-<br>agent output|
|GC-SEC-1|Yes|No|No|Isolate Grounding<br>Checker|
|GC-SEC-2|Yes|Yes|No|Add deterministic<br>conflict resolution|
|Full GC-SEC|Yes|Yes|Yes|Complete pipeline;<br>controlled replay for<br>Step3 if feasible|



## **3.1 Test Cases** 

|**Case**|**Test**|**Expected**|
|---|---|---|
|Positive control|Correct numeric claim + valid<br>evidence|Pass unchanged|
|Incorrect numeric|Claim disagrees with deterministic|Flag/replace|
||source|l|
|Missingevidence|No valid evidence reference|Block/flag|



|Unknown evidence ID|Evidence ID does not exist|Block/flag|
|---|---|---|
|Unit mismatch|e.g. ₹ represented as USD|l<br>Flag/block|
|Currencymismatch|Inconsistent currencies|Flag/block|
|Stale evidence|Outside freshness window|Mark stale/restrict|
|Inside epsilon|Differencejust inside tolerance|Accept if specification allows|
|Outside epsilon|Differencejust beyond tolerance|Flag/replace|
|Compound fault|f<br>e.g. stale + currencymismatch|Surface limitations/safe outcome|
|Calculation vsprivate record|Conflictingvalid claims|Calculation takesprecedence|
|Private record vs market|l<br>Conflictingvalid claims|Private record takesprecedence|
|Market vspublic source|l<br>Conflictingvalid claims|Market takesprecedence|
|Unresolved tie|l<br>No unique highest-priorityclaim|Explicit blocked status|
|Injection — imported statement|Instruction-like CAS/CSV content|Treat as untrusted data|
|Injection — retrieved document|Instruction-likeQdrant content|Treat as evidence only|
|Injection — connectorpayload|Instruction-like externalpayload|Do not execute|



Target: approximately 60 controlled scenarios, with positive controls, single faults, boundaries, compound faults, conflicts, and untrusted-input cases. 

## **3.2 Metrics** 

- Grounded-claim rate 

- Unsupported/hallucinated-claim rate 

- Conflict-resolution accuracy 

- Unresolved-conflict rate 

- False-positive rate on valid claims 

- Grounding correction rate 

- Precision/recall where labels support them 

- Mean/median end-to-end latency 

- Agent steps / LLM calls 

- Token usage when reliably measurable 

## **3.3 Step-3 Calibration** 

Do not manufacture live outcomes. If longitudinal data is unavailable, run a clearly labelled simulated historical replay with controlled prediction–outcome pairs. Report the update rule and a small parameter-evolution trace as simulated calibration, not live validation. 

## **4. Experiment B — Multi-Agent Orchestration & Routing** 

|**Query stratum**|**Definition**|**Target**|
|---|---|---|
|Single-intent|One clear domain task|~12|
|Cross-agent / compound|Requires multiple specialists|~12|
|Ambiguous|Requires interpretation/clarification|~12|
|Adversarial / out-of-scope|i<br>Attempts to bypass constraints or<br>requests prohibited automatic<br>action|~12|



## **4.1 Metrics** 

- Routing accuracy 

- Task success rate 

- Constraint adherence 

- Latency 

- Agent transitions / tool calls / LLM calls / tokens when measurable 

Optional controlled baseline: same LLM and domain tools in a single-agent setup, if implementation effort is small enough. 

## **5. Experiment C — Financial Component Correctness** 

|**Component**|**Test set**|**Primary metrics**|
|---|---|---|
|Guardian<br>l|510 transactions; 60 labelled<br>anomalies;5 anomalytypes|Precision, Recall, F1, ROC-AUC; per-<br>type F1|
|Cashflow|200 labelled transactions; 11<br>categories|Overall accuracy; macro/per-class<br>F1|
|Portfolio|30–50 controlled portfolios or<br>strongest available reference set|% deviation from reference; Sharpe<br>difference;CVaR difference;runtime<br>i|
|Tax (supporting)|18 capital-gains + 5 Section 80C<br>scenarios|Exact-match per field/scenario|
|RAG(supporting)|30 templatequestions|Recall@k;MRR|



Primary paper results: Guardian, Cashflow, Portfolio. Define the portfolio reference implementation and parameters before comparison. 

Important: use the same fixed test cases before/after any change and keep a change log. 

## **6. Experiment D — Security & Privacy Validation** 

Goal: validate implemented controls against representative attacks. This is control validation, not a complete security audit. 

|**Threat**|**Testprocedure**|**Expected result**|
|---|---|---|
|Broken object-level authorization|Attempt User B object access as<br>User A|Denied; no cross-user data|
|Authentication/session|Invalid/missing/expired/manipulated<br>session|Rejected|
|Credential exposure<br>i|Inspect stored and client-visible<br>connector credentials|No plaintext secret|
|Sensitive file exposure|Attempt unauthorized/expired<br>artifact access|Denied/token rejected|
|Malicious/unsafe input|Upload malformed/crafted content|Rejected/quarantined; no silent<br>commit|
|Injection — imported data|Inject command-like CAS/CSV<br>strings|No instruction execution|
|Injection — retrieved docs|Inject malicious text into test Qdrant<br>corpus|No policy bypass; grounded<br>response|
|Injection — connector payload|Inject instruction text into synthetic<br>payload|No instruction execution|



Record every case as Pass / Fail / Not Applicable with the exact control and procedure. Any overall pass rate is descriptive only, not a security score. 

## **7. Required Outputs from Antigravity** 

- Baseline commit hash 

- Frozen test-set/version ID 

- Raw result files for every experiment 

- Per-test-case results 

- Aggregate metrics 

- Latency/call/token measurements where available 

- Failure-case log with root-cause classification 

- Change log 

- Final rerun results 

- Plots/tables generated from raw outputs 

## **8. Execution Order** 

1. Freeze code and run existing benchmarks. 

2. Inspect failures without hiding poor results. 

3. Finalize Experiment A instrumentation and cases. 

4. Run A: Baseline → GC-SEC-1 → GC-SEC-2 → Full. 

5. Run B routing/task tests + optional single-agent baseline. 

6. Run C: Guardian → Cashflow → Portfolio → Tax/RAG. 

7. Run D security matrix. 

8. Generate plots/tables from raw outputs. 

9. Perform failure analysis and document justified changes. 

10. Freeze final version and rerun required tests. 

## **9. Paper Outputs** 

|**Output**|**Content**<br>i   i|
|---|---|
|Fig. 3|GC-SEC reliability/benefit across ablation configurations|
|Fig. 4|GC-SEC latency/token/LLM overhead|
|Fig. 5|Routingaccuracy/task success by querystratum|
|Fig. 6|Guardianper-class F1<br>l|
|Fig. 7|Cashflowper-class F1|
|Fig. 8|PortfolioQUANT-vs-reference scatter withy=x|
|Table IV|GC-SEC ablation results|
|Table V|Securityvalidation matrix|



## **10. Interpretation Rules** 

- Do not select metrics after seeing results. 

- Do not claim improvement without matched protocols. 

- Use task-appropriate metrics, not one generic accuracy number. 

- Report failures and limitations. 

- Do not call the system secure solely because controlled tests pass. 

- Do not claim live calibration effectiveness from simulated replay. 

**Source note:** Derived from the uploaded QUANT Updated Research Paper Scope & Evaluation Plan. This document contains the proposed execution protocol; it contains no experimental results. 


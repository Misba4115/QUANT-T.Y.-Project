# QUANT — Comprehensive Demo & Test Guide
### Mentor Presentation | 19 August 2026

> [!IMPORTANT]
> This guide is built around one consistent test persona — **Priya Sharma** — so every number on every screen traces back to a single coherent source of truth. Use this persona for your entire demo, and all dashboard figures will be self-consistent.

---

## Test Persona

| Field | Value |
|---|---|
| **Name** | Priya Sharma |
| **Email** | `priya.sharma.demo@gmail.com` |
| **Password** | `QuANT@secure2026` |
| **Age** | 29 |
| **Monthly Income** | ₹1,20,000 |
| **Monthly Expenses** | ₹62,000 |
| **Primary Goal** | Retirement |
| **Risk Profile** | Moderate |

---

## Step 1 — Registration & Login

### What to enter in the Register form

| Field | Value |
|---|---|
| Name | Priya Sharma |
| Email | priya.sharma.demo@gmail.com |
| Password | QuANT@secure2026 |
| Phone | 9876543210 |
| Age | 29 |
| Monthly Income | 120000 |
| Monthly Expenses | 62000 |
| Primary Goal | Retirement |
| Risk Profile | Moderate |

### Expected DB state after registration

**Table: `users`**
```
name             = "Priya Sharma"
email            = "priya.sharma.demo@gmail.com"
age              = 29
monthly_income   = 120000
monthly_expenses = 62000
primary_goal     = "Retirement"
risk_profile     = "moderate"
```

### Expected UI after login
- Redirected to `/dashboard`
- Net worth shows **₹0** (no data yet)
- Alert banner: "Your portfolio is empty — add holdings to get started"
- Navbar shows "Priya S." in the top-right avatar

---

## Step 2 — Bank Accounts (Input Data → Banking)

Enter **two** bank accounts manually:

### Account 1 — Primary Savings
| Field | Value |
|---|---|
| Account Name | HDFC Savings |
| Institution | HDFC Bank |
| Account Type | Savings |
| Account Number | XXXX-1234 |
| Current Balance | ₹85,000 |
| Is Primary | ✅ Yes |

### Account 2 — Fixed Deposit
| Field | Value |
|---|---|
| Account Name | SBI Fixed Deposit |
| Institution | State Bank of India |
| Account Type | Fixed Deposit |
| Account Number | XXXX-5678 |
| Current Balance | ₹2,50,000 |
| Is Primary | ❌ No |

### Expected DB state after banking input

**Table: `banking_accounts`** — 2 rows
```
Row 1: account_type=savings,  institution=HDFC Bank,           current_balance=85000,  is_primary=true
Row 2: account_type=fd,       institution=State Bank of India,  current_balance=250000, is_primary=false
```

### Expected Dashboard impact
- Cash component of net worth: **₹3,35,000**
- Asset allocation shows "Cash" as a slice

---

## Step 3 — Equity Holdings (Manual Entry)

Go to **Input Data → Equity** and add the following 4 stocks manually:

| Symbol | Company | Quantity | Avg Buy Price (₹) | Current Price (₹) |
|---|---|---|---|---|
| RELIANCE | Reliance Industries | 15 | 2,650 | 2,910 |
| INFY | Infosys | 30 | 1,420 | 1,580 |
| HDFCBANK | HDFC Bank | 20 | 1,640 | 1,720 |
| TCS | Tata Consultancy Services | 10 | 3,750 | 4,100 |

### Expected DB state after equity entry

**Table: `equity_holdings`** — 4 rows
```
RELIANCE:  quantity=15,  avg_price=2650, current_price=2910  → value = ₹43,650
INFY:      quantity=30,  avg_price=1420, current_price=1580  → value = ₹47,400
HDFCBANK:  quantity=20,  avg_price=1640, current_price=1720  → value = ₹34,400
TCS:       quantity=10,  avg_price=3750, current_price=4100  → value = ₹41,000
```
**Total equity value: ₹1,66,450**

---

## Step 4 — Mutual Fund Holdings (CSV Upload)

### CSV Upload Demonstration

Go to **Input Data → Import Data**, choose **Mutual Funds** and upload the following CSV. Save this as `mf_holdings.csv`:

```csv
scheme_code,fund_name,units,avg_nav,current_nav,folio_number
INF209K01VN5,Aditya Birla Sun Life Frontline Equity Fund - Growth,145.234,54.20,61.80,1234567
INF846K01EW2,Axis Bluechip Fund - Growth,220.000,38.75,43.50,2345678
INF179K01BB6,HDFC Mid-Cap Opportunities Fund - Growth,98.500,72.10,85.40,3456789
INF277K01ZM4,SBI Small Cap Fund - Growth,55.000,92.30,108.60,4567890
```

### Expected import flow
1. Upload CSV → Preview screen appears showing 4 rows
2. Column mapping auto-detected: `scheme_code → scheme_code`, `fund_name → mf_name`, `units → units`, `avg_nav → avg_nav`, `current_nav → current_nav`
3. Valid count: **4**, Error count: **0**
4. Click **Commit** → all 4 rows imported

### Expected DB state after MF import

**Table: `mutual_fund_holdings`** — 4 rows
```
INF209K01VN5: units=145.234, avg_nav=54.20, current_nav=61.80  → value = ₹8,975.46
INF846K01EW2: units=220.000, avg_nav=38.75, current_nav=43.50  → value = ₹9,570.00
INF179K01BB6: units=98.500,  avg_nav=72.10, current_nav=85.40  → value = ₹8,411.90
INF277K01ZM4: units=55.000,  avg_nav=92.30, current_nav=108.60 → value = ₹5,973.00
```
**Total MF value: ₹32,930.36**

---

## Step 5 — ETF Holdings (Manual Entry)

Go to **Input Data → ETF** and add 2 ETFs:

| Symbol | ETF Name | Quantity | Avg Price (₹) | Current Price (₹) |
|---|---|---|---|---|
| NIFTYBEES | Nippon India ETF Nifty BeES | 50 | 220.00 | 248.50 |
| GOLDBEES | Nippon India ETF Gold BeES | 25 | 55.00 | 61.20 |

### Expected DB state
**Table: `etf_holdings`** — 2 rows
```
NIFTYBEES: quantity=50, avg_price=220, current_price=248.50 → value = ₹12,425
GOLDBEES:  quantity=25, avg_price=55,  current_price=61.20  → value = ₹1,530
```
**Total ETF value: ₹13,955**

---

## Step 6 — Crypto Holdings (Manual Entry)

Go to **Input Data → Crypto** and add 2 crypto assets:

| Symbol | Name | Quantity | Avg Price (₹) | Current Price (₹) |
|---|---|---|---|---|
| BTC | Bitcoin | 0.0045 | 52,00,000 | 58,50,000 |
| ETH | Ethereum | 0.15 | 2,10,000 | 2,45,000 |

### Expected DB state
**Table: `crypto_holdings`** — 2 rows
```
BTC: quantity=0.0045, avg_price=5200000, current_price=5850000 → value = ₹26,325
ETH: quantity=0.15,   avg_price=210000,  current_price=245000  → value = ₹36,750
```
**Total crypto value: ₹63,075**

---

## Step 7 — Bank Transactions (CSV Upload)

Save as `bank_transactions.csv` and upload under **Input Data → Import Data → Bank Transactions**:

```csv
tx_date,description,amount,tx_type,category
2026-07-01,Salary Credit,120000,credit,SALARY
2026-07-05,HDFC EMI Debit,18500,debit,LOAN_EMI
2026-07-08,Swiggy Food Order,1850,debit,FOOD
2026-07-10,Zepto Groceries,3200,debit,GROCERIES
2026-07-12,Netflix Subscription,649,debit,ENTERTAINMENT
2026-07-15,ELSS SIP - Axis Bluechip,5000,debit,ELSS
2026-07-18,LIC Premium,12000,debit,LIC
2026-07-20,Electricity Bill,2100,debit,UTILITIES
2026-07-22,Petrol,2800,debit,FUEL
2026-07-25,Amazon Purchase,4500,debit,SHOPPING
2026-07-28,PPF Contribution,5000,debit,PPF
2026-08-01,Salary Credit,120000,credit,SALARY
2026-08-03,HDFC EMI Debit,18500,debit,LOAN_EMI
2026-08-06,Zomato Order,2200,debit,FOOD
2026-08-09,Zepto Groceries,2900,debit,GROCERIES
2026-08-12,Spotify Premium,199,debit,ENTERTAINMENT
2026-08-15,ELSS SIP - Axis Bluechip,5000,debit,ELSS
2026-08-18,Electricity Bill,1950,debit,UTILITIES
```

### Expected import flow
- 18 rows, all valid
- Categories auto-detected (ELSS, LIC, PPF → tagged as Section 80C eligible)

### Expected DB state
**Table: `bank_transactions`** — 18 rows
- July salary: ₹1,20,000 credit
- August salary: ₹1,20,000 credit
- Section 80C eligible transactions: ELSS × 2 (₹10,000) + LIC (₹12,000) + PPF (₹5,000) = **₹27,000 used**

### Expected Dashboard impact — Tax Tracker widget
```
Section 80C used:     ₹27,000
Section 80C headroom: ₹1,23,000 (₹1,50,000 limit)
Status:               Available
```

---

## Step 8 — Financial Goals (Input Data → Goals)

Add **3 goals**:

### Goal 1 — Retirement
| Field | Value |
|---|---|
| Goal Name | Retirement Corpus |
| Goal Type | Retirement |
| Target Amount | ₹5,00,00,000 (5 crore) |
| Current Saved | ₹6,11,410 (sum of all assets) |
| Target Date | 2055-03-01 |

### Goal 2 — Emergency Fund
| Field | Value |
|---|---|
| Goal Name | Emergency Fund |
| Goal Type | Emergency Fund |
| Target Amount | ₹3,60,000 (3× monthly expenses) |
| Current Saved | ₹85,000 (from HDFC savings) |
| Target Date | 2027-01-01 |

### Goal 3 — Vacation
| Field | Value |
|---|---|
| Goal Name | Europe Trip |
| Goal Type | Travel |
| Target Amount | ₹2,50,000 |
| Current Saved | ₹45,000 |
| Target Date | 2027-06-01 |

### Expected DB state
**Table: `goals`** — 3 rows with user_id set correctly

### Expected Insights Tab → Investment Recommendations
```
Goal Alignment:
  ✗ Retirement Corpus  — 18% short at current pace, Gap: ₹4,93,88,590
  ✗ Emergency Fund     — 76% short at current pace, Gap: ₹2,75,000
  ✓ Europe Trip        — 18% saved, Gap: ₹2,05,000

Priority Action:
  "Increasing your monthly investment by ₹4,000 can help close your retirement gap"
```

---

## Step 9 — Upstox Connector (Connectors tab)

### What to demonstrate (even without live credentials)

1. Navigate to **Settings → Connectors** (or wherever your connector UI lives)
2. Click **"Connect Upstox"**
3. The backend calls `POST /api/connectors/upstox/authorize`
4. This returns an `authorization_url` — show the URL being generated
5. **For demo:** redirect to the Upstox OAuth page (will show Upstox login)
6. If you have sandbox credentials, complete the OAuth flow
7. After callback, `GET /api/connectors` shows the account as `status: connected`

### What to say to mentor
> "The Upstox connector uses OAuth 2.0. Once connected, we preview the sync before committing any data — the user sees exactly what will be imported before it touches their portfolio."

### Expected DB state after successful connection
**Table: `connector_accounts`**
```
provider       = "upstox"
status         = "connected"
display_name   = "Priya's Upstox Account"
last_synced_at = <timestamp>
```

---

## Step 10 — Dashboard Verification

After entering all data above, go to **Dashboard** and click **Refresh Prices** then reload.

### Expected net worth calculation

| Component | Value |
|---|---|
| HDFC Savings (cash) | ₹85,000 |
| SBI Fixed Deposit | ₹2,50,000 |
| Equity holdings | ₹1,66,450 |
| Mutual funds | ₹32,930 |
| ETFs | ₹13,955 |
| Crypto | ₹63,075 |
| **Total Net Worth** | **₹6,11,410** |

### Expected Asset Allocation donut chart

| Slice | % | Amount |
|---|---|---|
| Cash | 54.8% | ₹3,35,000 |
| Equity | 27.2% | ₹1,66,450 |
| Crypto | 10.3% | ₹63,075 |
| Mutual Fund | 5.4% | ₹32,930 |
| ETF | 2.3% | ₹13,955 |

### Expected Top Holdings (sorted by value)
```
1. Infosys (INFY)         — ₹47,400  (+11.3% P&L)
2. Reliance (RELIANCE)    — ₹43,650  (+9.8% P&L)
3. TCS                    — ₹41,000  (+9.3% P&L)
4. Ethereum (ETH)         — ₹36,750  (+16.7% P&L)
5. HDFC Bank (HDFCBANK)   — ₹34,400  (+4.9% P&L)
```

### Expected Cashflow widget (August 2026)
```
Monthly Income:    ₹1,20,000
Monthly Expenses:  ₹31,749  (sum of August debits so far)
Surplus:           ₹88,251
```

### Expected Risk Level
- **Stated:** Moderate
- **Measured:** Unavailable (insufficient portfolio snapshot history — explain this to mentor: "Risk metrics activate after 30 days of history")

### Expected Alerts
```
⚠  High cash allocation (54.8%) — consider deploying into goal-aligned instruments
ℹ  Section 80C: ₹1,23,000 headroom remaining before financial year end
ℹ  No realized capital gains this period
```

---

## Step 11 — Insights & Trading Tab

Navigate to **Insights & Trading** in the navbar.

### Layer A — Trading Signals (click "Trading Signals" tab)

**Market Outlook cards should appear for:**
- Equity — direction badge, return range (e.g. +2.0% to +5.0%), Medium confidence
- Mutual Fund — direction badge, return range
- ETF — direction badge

**Suggested Actions panel:**
```
HOLD  Cash        — Within target allocation
HOLD  Equity      — Within target allocation  
HOLD  Mutual Fund — Within target allocation
HOLD  ETF         — Within target allocation
HOLD  Crypto      — Within target allocation
```
*(All HOLD because Priya's portfolio is new — no significant deviation from equal-weight yet)*

### Layer B — Investment Recommendations (click "Investment Recommendations" tab)

**Goal Alignment cards:**
- Retirement Corpus — large red/blue progress bar, ~18% filled, shows gap and SIP suggestion
- Emergency Fund — ~23% filled
- Europe Trip — ~18% filled

**New Instrument Suggestions:**
- Liquid Mutual Fund (Low risk) — "Improves stability and provides emergency liquidity"
- Gold ETF (Low risk) — "Inflation hedge and portfolio diversifier"

**Priority Action card:**
- "Increase monthly investment"
- Impact: High | Effort: Low | Horizon: Long-term

### GC-SEC Accordion (click "Why these recommendations?")
```
Step 1 — Grounding:    8 values verified, 0 corrections applied
Step 2 — Arbiter:      Risk profile: Moderate. No tax constraints triggered.
Step 3 — Calibration:  Outcome logging active.
```

---

## Step 12 — Guardian Alerts

Navigate to **Guardian** tab.

### What to demonstrate
If you've entered the data above, the Guardian agent should have:
```
ℹ  High cash concentration (54.8%) detected
   → Explanation: Cash exceeds typical 20% target allocation for a moderate-risk profile
   
ℹ  Retirement goal corpus is significantly underfunded
   → Current ₹6.1L vs target ₹5Cr (98.8% gap)
```

### How to interact with Guardian
1. Click on an alert
2. Click "Mark as Expected" (if Priya acknowledges it's intentional)
3. Show the feedback being recorded: `verdict = "expected"`

---

## Step 13 — Chatbot Prompts

Navigate to any page and open the chatbot (bottom-right chat bubble).

Use these prompts in order — they cover every agent in the orchestrator:

### Portfolio & Dashboard queries (Portfolio Agent)

| # | Prompt | Expected response pattern |
|---|---|---|
| 1 | `What is my current net worth?` | Returns ₹6,11,410 with breakdown by asset class |
| 2 | `Show me my asset allocation` | Lists Cash 54.8%, Equity 27.2%, etc. |
| 3 | `What are my top 3 holdings by value?` | INFY, RELIANCE, TCS |
| 4 | `Which of my holdings has the highest profit percentage?` | ETH at +16.7% |
| 5 | `How much have I invested in mutual funds?` | Returns total MF cost basis and current value |

### Tax queries (Tax Agent)

| # | Prompt | Expected response pattern |
|---|---|---|
| 6 | `How much Section 80C have I used this year?` | ₹27,000 used, ₹1,23,000 headroom remaining |
| 7 | `What is my 80C headroom?` | ₹1,23,000 remaining before ₹1,50,000 limit |
| 8 | `Do I have any capital gains tax liability?` | No realized gains yet (no sell transactions) |
| 9 | `Should I invest more in ELSS to save tax?` | Yes — shows headroom and suggests ELSS SIP increase |
| 10 | `What is LTCG tax rate for equity in India?` | RAG answer: 12.5% above ₹1,25,000 exemption (post July 2024 rules) |

### Cashflow queries (Cashflow Agent)

| # | Prompt | Expected response pattern |
|---|---|---|
| 11 | `What is my monthly surplus?` | ₹88,251 in August |
| 12 | `How much did I spend on food this month?` | FOOD category total from August transactions |
| 13 | `What is my biggest expense category?` | LOAN_EMI at ₹18,500 |
| 14 | `Am I saving enough relative to my income?` | Shows savings rate as % of income |

### Goal queries (via chatbot)

| # | Prompt | Expected response pattern |
|---|---|---|
| 15 | `Am I on track for retirement?` | No — 18% shortfall at current pace, suggests SIP increase |
| 16 | `How much do I need to save monthly to retire by 2055 with 5 crore?` | Computes required monthly investment |
| 17 | `What is my emergency fund status?` | 23% funded, recommends liquid fund |

### Market & RAG queries

| # | Prompt | Expected response pattern |
|---|---|---|
| 18 | `What is the Nifty 50 index?` | RAG answer from knowledge base |
| 19 | `Explain what a Liquid Fund is` | RAG answer with citation |
| 20 | `What is the difference between STCG and LTCG for equity?` | RAG answer: STCG = 20%, LTCG = 12.5% (post Jul 2024) |
| 21 | `What is the SBI Small Cap Fund that I hold?` | Grounded answer referencing user's actual holding |

### Edge case / error prompts (show robustness)

| # | Prompt | Expected response pattern |
|---|---|---|
| 22 | `Buy 10 shares of Reliance for me` | Politely declines: "QUANT is advisory only — no trade execution" |
| 23 | `What will Nifty be at in 6 months?` | Gives model-based forecast range with caveat, not a point prediction |
| 24 | `Delete all my holdings` | Declines gracefully with appropriate refusal |

---

## Step 14 — Settings & Notifications

### Settings to show
1. **Dashboard Config** — change time period from 1Y to 6M, see chart update
2. **Chart Type** — switch from Line to Area chart
3. **Personalization → Risk Assessment** — complete the risk questionnaire (show moderate result matching Priya's stated profile)

### Notifications to show
- Go to **Notifications** (bell icon)
- Any generated guardian alerts appear here
- Mark one as read, show badge count decrease

---

## Mentor Demo Script (5-minute version)

```
1. "Here's QUANT — a multi-agent financial intelligence platform for Indian retail investors."

2. [Register as Priya Sharma] "Registration captures income, expenses, and risk profile."

3. [Add bank accounts] "Cash is the foundation of net worth."

4. [Upload MF CSV] "We auto-detect column mapping using our LLM header parser."

5. [Dashboard] "The dashboard aggregates everything — net worth ₹6.1L, asset allocation, cashflow, and tax position, all computed in real time."

6. [Insights tab, Layer A] "Layer A shows trading signals — 30-day return forecasts grounded by our Portfolio Analytics engine."

7. [Insights tab, Layer B] "Layer B shows investment recommendations — goal-gap arithmetic tells Priya she needs to increase SIPs by ₹4,000/month for retirement."

8. [GC-SEC accordion] "Everything passes through GC-SEC — three-step verification: Grounding, Arbitration, Calibration."

9. [Chatbot] "The chatbot routes queries to specialised agents — portfolio, tax, cashflow — with RAG for knowledge queries."

10. [Guardian] "Guardian runs continuously, flagging anomalies. Here it caught the high cash concentration."
```

---

## Quick Sanity Check — Numbers at a Glance

After entering all data above, these are the numbers you should see on screen:

| Dashboard Field | Expected Value |
|---|---|
| Net Worth | ₹6,11,410 |
| Cash (banking) | ₹3,35,000 |
| Equity total | ₹1,66,450 |
| MF total | ₹32,930 |
| ETF total | ₹13,955 |
| Crypto total | ₹63,075 |
| Monthly Income | ₹1,20,000 |
| Section 80C used | ₹27,000 |
| Section 80C headroom | ₹1,23,000 |
| Goals | 3 (0 on track) |
| Holdings count | 13 (4 equity + 4 MF + 2 ETF + 2 crypto + 1 FD) |

> [!TIP]
> If any number doesn't match, the most common causes are: (1) price sync hasn't run — click "Refresh Prices" on the dashboard, (2) a CSV row was rejected — check the Import History page for errors, (3) the banking account balance was entered incorrectly.

> [!WARNING]
> The Upstox connector requires real OAuth credentials. If your `.env` does not have `UPSTOX_CLIENT_ID` and `UPSTOX_CLIENT_SECRET` set, the authorization URL will still generate but the OAuth callback will fail. For the demo, show the URL generation and explain the flow conceptually if live credentials aren't available.

# Investment discovery

Apply `migrations/009_investment_comparisons.sql` and then
`migrations/010_investment_platforms.sql` after the existing migrations.
The hosted QUANT project was verified on 2026-09-29 with both tables present;
the platform registry contained 15 seeded rows. New environments still apply
these files in order.
These tables follow QUANT's custom-auth architecture: RLS denies browser access;
only the backend service role can access it, with authenticated user filters on
every read/delete and server-assigned user IDs on composite-key upserts.
No Supabase Auth policy should be added using a mismatched user identity.

Schema verification: the hosted read-only audit on 2026-09-25 found all 27
expected tables and columns. Canonical migrations, compatibility migrations,
and sample_data holdings rows were inspected. Live financial rows remain scoped
to the authenticated user at runtime. A failed holdings query is never treated
as an empty portfolio.

Ownership uses positive quantity/units and positive fixed/recurring-deposit
balances. Savings/current accounts are not investment deposits. MF/ETF wrappers
can overlap gold/debt exposure, so the cards are not additive allocation buckets.

Mean–variance uses at most seven recorded INR proxy series. It requires at least
61 common prices, no gaps over seven days, and evidence within 14 days. Providers
are not mixed. Annualization uses the average calendar interval. Covariance has
10% diagonal shrinkage. A bounded 100-iteration SLSQP solver maximizes
`mean @ weights - risk_aversion / 2 * weights @ covariance @ weights`, subject to
nonnegative weights summing to one. Risk aversion is 8/4/2 for
conservative/moderate/aggressive; unknown profiles use 4. These are explicit
model assumptions, not calibrated suitability scores. Historical proxy weights
rank within ownership groups; unowned routes always precede owned routes.

ETF/gold use NIFTYBEES/GOLDBEES only if recorded history exists. Other categories
use a representative tracked holding. No missing histories are invented. Generic
option alternatives share their category proxy; they are not individual product
forecasts. No fees/taxes are included in optimization. Deposits have no traded
price proxy. The separate calculator uses visible illustrative annual rates,
not advertised rates or expected returns from the optimizer. All computations,
reloads, and comparisons make no AI calls.

Broker sources are linked in the catalogue and UI, checked 2026-09-25:
https://zerodha.com/charges/ , https://groww.in/pricing ,
https://coin.zerodha.com/ , https://groww.in/mutual-funds ,
https://www.hdfc.bank.in/fixed-deposit/regular-fixed-deposits ,
https://www.icici.bank.in/personal-banking/deposits/fixed-deposit ,
https://coindcx.com/fees , https://coinswitch.co/ .
The curated platform set also includes Upstox and Angel One for listed assets
and funds, plus SBI, Axis Bank and Kotak Bank for deposits. Official product,
pricing and opening pages are linked from each platform record. This is a
selection, not a claim to cover every broker or bank. Deposit slider floors
follow the chosen bank's published initial minimum; Kotak uses its higher
first-deposit minimum.
Migration 010 seeds the verified provider registry. Additional verified global
providers can be added by a database administrator with official HTTPS links,
reviewed terms and the supported category IDs; no application release is needed.

Current comparison behavior: users save a category approach and a provider,
then choose two sides with a common amount and timeline. The dialog compares
recorded ownership, risk level, planning-horizon fit, minimum, published fees,
qualitative usability, unverifiable reliability limitations, liquidity, and an
illustrative future value using the category scenario rate. A conservative risk
setting flags high-risk categories. Historical mean, volatility and the data
date appear only when the bounded proxy model has enough aligned prices. The
provider choice does not change category-level market statistics. No composite
score, live macroeconomic adjustment, after-tax return, or marginal portfolio
variance is currently calculated; the UI says when market evidence is missing.
The chatbot's second-opinion prompt receives user-scoped category research only
for investment questions, asks for both benefits and downsides, and does not
send a question automatically when opened from a card or comparison.
Users can add a private bank or broker by name from a recommendation card. Its
fees, minimum, reliability and link remain explicitly unverified; the ₹100
calculator floor is only an illustration. Private providers appear in the
user's cards and saved comparisons, but are never visible to another user.
The existing built-in list is a fallback until migration 010 is applied.
Minimums that depend on a security or scheme are described rather than invented.
Usability comparisons describe features; no unverified reliability scores exist.

Algorithm reference: https://www.cvxpy.org/examples/basic/quadratic_program.html
(the runtime uses existing scipy/numpy dependencies, not CVXPY).

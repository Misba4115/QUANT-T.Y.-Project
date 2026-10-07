-- Global, verified provider catalogue plus user-private, unverified providers.
-- QUANT uses backend authentication; browser roles never access this table directly.
create table if not exists public.investment_platforms (
  id text primary key check (length(id) between 1 and 80),
  user_id uuid references public.users(user_id) on delete cascade,
  category_ids text[] not null check (cardinality(category_ids) > 0 and category_ids <@ array['deposit','debt','mf','etf','gold','equity','crypto']::text[]),
  name text not null check (length(btrim(name)) between 1 and 80),
  url text,
  action_url text,
  fees text,
  ease text,
  minimum text,
  minimum_amount numeric(18,2) check (minimum_amount is null or minimum_amount > 0),
  reliability text,
  checked_on date,
  verified boolean not null default false,
  created_at timestamptz not null default now(),
  check ((user_id is null and verified and url like 'https://%' and action_url like 'https://%')
      or (user_id is not null and not verified and url is null and action_url is null))
);
create index if not exists investment_platforms_user_id_idx on public.investment_platforms(user_id);
alter table public.investment_platforms enable row level security;
revoke all on public.investment_platforms from public, anon, authenticated;
grant select, insert, update, delete on public.investment_platforms to service_role;

insert into public.investment_platforms
  (id, category_ids, name, url, action_url, fees, ease, minimum, minimum_amount, reliability, checked_on, verified)
values
  ('hdfc', array['deposit'], 'HDFC Bank', 'https://www.hdfc.bank.in/fixed-deposit/regular-fixed-deposits', 'https://www.hdfc.bank.in/fixed-deposit/regular-fixed-deposits', 'Check premature-withdrawal penalties and the selected deposit terms.', 'Online deposit booking or branch assistance.', '₹5,000 for a regular FD', 5000, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('icici', array['deposit'], 'ICICI Bank', 'https://www.icici.bank.in/personal-banking/deposits/fixed-deposit', 'https://www.icici.bank.in/personal-banking/deposits/fixed-deposit', 'Check premature-withdrawal penalties and the selected deposit terms.', 'Online deposit booking or branch assistance.', '₹10,000 for a regular FD', 10000, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('sbi', array['deposit'], 'SBI', 'https://sbi.bank.in/web/personal-banking/investments-deposits/deposits/fixed-deposit', 'https://sbi.bank.in/web/personal-banking/investments-deposits/deposits/fixed-deposit', 'Check the chosen term''s rate and early-withdrawal terms.', 'Online SBI, YONO or branch deposit booking.', '₹1,000 for a regular term deposit', 1000, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('axis', array['deposit'], 'Axis Bank', 'https://www.axis.bank.in/deposits/fixed-deposits', 'https://www.axis.bank.in/deposits/fixed-deposits', 'Check the chosen term''s rate and early-withdrawal terms.', 'Online or branch deposit booking.', '₹5,000 for a regular FD', 5000, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('kotak', array['deposit'], 'Kotak Bank', 'https://www.kotak.bank.in/en/personal-banking/deposits/fixed-deposit.html', 'https://www.kotak.bank.in/en/personal-banking/deposits/fixed-deposit.html', 'Check the chosen term''s rate and early-withdrawal terms.', 'Online or branch deposit booking.', '₹10,000 for a first FD; ₹5,000 thereafter', 10000, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('zerodha', array['etf','gold','equity'], 'Zerodha', 'https://zerodha.com/charges/', 'https://zerodha.com/open-account/', 'Delivery brokerage ₹0; statutory, DP and applicable account charges extra.', 'Kite trading interface; order types require familiarity.', 'One exchange-traded unit at its live price', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('groww', array['etf','gold','equity'], 'Groww', 'https://groww.in/pricing', 'https://groww.in/', 'Equity brokerage: lower of ₹20 or 0.1% per order, minimum ₹5; other charges extra.', 'Stocks and funds in one app; compare the order preview.', 'One exchange-traded unit at its live price', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('upstox', array['etf','gold','equity'], 'Upstox', 'https://upstox.com/brokerage-charges/', 'https://upstox.com/trading-account/', 'Stocks and ETFs: up to ₹20 per order; statutory and other charges extra.', 'Trading app with stock, ETF and fund discovery.', 'One exchange-traded unit at its live price', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('angel', array['etf','gold','equity'], 'Angel One', 'https://www.angelone.in/support/charges-and-cashbacks/brokerage-charges', 'https://www.angelone.in/open-demat-account', 'Equity delivery: lower of ₹20 or 0.1% per order, minimum ₹5; other charges extra.', 'Trading app with stocks, ETFs and mutual funds.', 'One exchange-traded unit at its live price', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('coin', array['debt','mf'], 'Zerodha Coin', 'https://coin.zerodha.com/', 'https://zerodha.com/open-account/', 'Direct funds: zero commission; scheme expenses and possible exit loads apply.', 'Separate mutual-fund interface linked to Zerodha.', 'Scheme-specific; verify initial lump-sum and SIP minimums', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('groww-mf', array['debt','mf'], 'Groww', 'https://groww.in/mutual-funds', 'https://groww.in/mutual-funds', 'Direct plans: scheme expenses and possible exit loads apply; check plan pricing.', 'Fund discovery and SIP setup alongside stocks.', 'Scheme-specific; verify initial lump-sum and SIP minimums', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('upstox-mf', array['debt','mf'], 'Upstox', 'https://upstox.com/mutual-funds/', 'https://upstox.com/mutual-funds/', 'Direct plans: platform says no transaction charge; scheme expenses and possible exit loads apply.', 'Fund browsing and SIP setup in the Upstox app.', 'Scheme-specific; verify initial lump-sum and SIP minimums', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('angel-mf', array['debt','mf'], 'Angel One', 'https://www.angelone.in/mutual-funds', 'https://www.angelone.in/mutual-funds', 'Check direct-plan expenses, exit loads and any current platform fees.', 'Fund discovery alongside a trading account.', 'Scheme-specific; verify initial lump-sum and SIP minimums', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('coindcx', array['crypto'], 'CoinDCX', 'https://coindcx.com/fees', 'https://coindcx.com/fees', 'Fees vary by product and tier; verify the order quote.', 'Spot trading via an exchange account.', 'Verify the selected token''s current order minimum', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true),
  ('coinswitch', array['crypto'], 'CoinSwitch', 'https://coinswitch.co/', 'https://coinswitch.co/', 'Review quoted spread and product-specific fees.', 'App-based spot purchases.', 'From ₹100; verify product eligibility', 100, 'No comparable audited uptime data available. Review service history and support before choosing.', '2026-09-25', true)
on conflict (id) do nothing;

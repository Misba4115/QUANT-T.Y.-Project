-- Data-preserving compatibility migration for the existing hosted QUANT schema.
-- This migration deliberately does not alter or use document_embeddings/match_documents.
-- Review on staging, back up production, then run as one transaction.

begin;

create extension if not exists pgcrypto;

create table if not exists public.import_batches (
  import_batch_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  filename text not null,
  content_hash text not null,
  source_type text not null,
  target_type text,
  parser_version text not null,
  status text not null check (status in ('pending','processing','completed','partial','failed')),
  preview_rows jsonb not null default '[]'::jsonb,
  column_mapping jsonb not null default '{}'::jsonb,
  valid_count integer not null default 0,
  error_count integer not null default 0,
  committed_count integer not null default 0,
  error_message text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique(user_id, content_hash, parser_version)
);

create table if not exists public.import_row_errors (
  import_row_error_id uuid primary key default gen_random_uuid(),
  import_batch_id uuid not null references public.import_batches(import_batch_id) on delete cascade,
  row_number integer not null,
  code text not null,
  message text not null,
  raw_row jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

alter table public.users add column if not exists updated_at timestamptz default timezone('utc', now());
alter table public.goals add column if not exists updated_at timestamptz default timezone('utc', now());
alter table public.chat_messages add column if not exists metadata jsonb not null default '{}'::jsonb;

alter table public.banking_accounts add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.banking_accounts add column if not exists source_row_hash text;
alter table public.equity_holdings add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.equity_holdings add column if not exists source_row_hash text;
alter table public.equity_holdings add column if not exists price_source text;
alter table public.equity_holdings add column if not exists source_timestamp timestamptz;
alter table public.mutual_fund_holdings add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.mutual_fund_holdings add column if not exists source_row_hash text;
alter table public.mutual_fund_holdings add column if not exists price_source text;
alter table public.mutual_fund_holdings add column if not exists source_timestamp timestamptz;
alter table public.etf_holdings add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.etf_holdings add column if not exists source_row_hash text;
alter table public.etf_holdings add column if not exists price_source text;
alter table public.etf_holdings add column if not exists source_timestamp timestamptz;
alter table public.crypto_holdings add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.crypto_holdings add column if not exists source_row_hash text;
alter table public.crypto_holdings add column if not exists price_source text;
alter table public.crypto_holdings add column if not exists source_timestamp timestamptz;
alter table public.goals add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.goals add column if not exists source_row_hash text;

alter table public.bank_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.bank_transactions add column if not exists source text;
alter table public.bank_transactions add column if not exists source_row_hash text;
alter table public.bank_transactions add column if not exists anomaly_model_version text;
alter table public.bank_transactions add column if not exists anomaly_detected_at timestamptz;

alter table public.equity_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.equity_transactions add column if not exists fees numeric(18,2) not null default 0;
alter table public.equity_transactions add column if not exists source text;
alter table public.equity_transactions add column if not exists source_row_hash text;
alter table public.equity_transactions add column if not exists anomaly_model_version text;
alter table public.equity_transactions add column if not exists anomaly_detected_at timestamptz;
alter table public.etf_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.etf_transactions add column if not exists fees numeric(18,2) not null default 0;
alter table public.etf_transactions add column if not exists source text;
alter table public.etf_transactions add column if not exists source_row_hash text;
alter table public.etf_transactions add column if not exists anomaly_model_version text;
alter table public.etf_transactions add column if not exists anomaly_detected_at timestamptz;
alter table public.crypto_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.crypto_transactions add column if not exists fees numeric(18,2) not null default 0;
alter table public.crypto_transactions add column if not exists source text;
alter table public.crypto_transactions add column if not exists source_row_hash text;
alter table public.crypto_transactions add column if not exists anomaly_model_version text;
alter table public.crypto_transactions add column if not exists anomaly_detected_at timestamptz;

create table if not exists public.mf_transactions (
  mf_tx_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  tx_date date not null,
  scheme_code text,
  mf_name text not null,
  units numeric(24,8) not null check (units > 0),
  nav numeric(18,4) not null check (nav >= 0),
  tx_type text not null check (tx_type in ('buy','sell')),
  source text,
  source_row_hash text,
  import_batch_id uuid references public.import_batches(import_batch_id) on delete set null,
  is_anomaly boolean not null default false,
  anomaly_score double precision,
  anomaly_model_version text,
  anomaly_detected_at timestamptz,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.market_price_cache (
  price_cache_id uuid primary key default gen_random_uuid(), asset_type text not null,
  instrument_key text not null, price numeric(20,6) not null check (price >= 0),
  currency text not null default 'INR', provider text not null,
  source_timestamp timestamptz not null, fetched_at timestamptz not null default timezone('utc', now()),
  status text not null check (status in ('live','delayed','stored','stale')),
  unique(asset_type, instrument_key, provider)
);

create table if not exists public.price_sync_runs (
  price_sync_run_id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(user_id) on delete cascade,
  status text not null check (status in ('pending','processing','completed','partial','failed')),
  requested_count integer not null default 0, updated_count integer not null default 0,
  failed_count integer not null default 0, errors jsonb not null default '[]'::jsonb,
  started_at timestamptz not null default timezone('utc', now()), completed_at timestamptz
);

alter table public.portfolio_snapshots add column if not exists net_worth numeric(20,2);
alter table public.portfolio_snapshots add column if not exists allocation jsonb not null default '[]'::jsonb;
alter table public.portfolio_snapshots add column if not exists valuation_coverage numeric(6,3) not null default 0;
alter table public.portfolio_snapshots add column if not exists source_status jsonb not null default '{}'::jsonb;
update public.portfolio_snapshots set net_worth = total_value where net_worth is null;

alter table public.dashboard_runs add column if not exists status text;
alter table public.dashboard_runs add column if not exists params jsonb;
alter table public.dashboard_runs add column if not exists result jsonb;
alter table public.dashboard_runs add column if not exists error text;
alter table public.dashboard_runs add column if not exists created_at timestamptz;
alter table public.dashboard_runs add column if not exists completed_at timestamptz;
update public.dashboard_runs set
  status = coalesce(status, run_status, 'pending'),
  params = coalesce(params, run_params, '{}'::jsonb),
  result = coalesce(result, run_result),
  error = coalesce(error, error_message),
  created_at = coalesce(created_at, requested_at, timezone('utc', now()))
where status is null or params is null or created_at is null;

alter table public.dashboard_configs add column if not exists dashboard_config_id uuid default gen_random_uuid();
alter table public.dashboard_configs add column if not exists widgets jsonb;
alter table public.dashboard_configs add column if not exists time_period text;
update public.dashboard_configs set
  widgets = coalesce(widgets, selected_widgets, '[]'::jsonb),
  time_period = coalesce(time_period, default_time_period, '1y')
where widgets is null or time_period is null;

create unique index if not exists uq_dashboard_configs_canonical_id on public.dashboard_configs(dashboard_config_id);
create unique index if not exists uq_dashboard_configs_user on public.dashboard_configs(user_id);
create index if not exists idx_import_batches_user_created on public.import_batches(user_id, created_at desc);
create index if not exists idx_import_errors_batch on public.import_row_errors(import_batch_id, row_number);
create index if not exists idx_price_cache_lookup on public.market_price_cache(asset_type, instrument_key, fetched_at desc);
create index if not exists idx_snapshots_user_date on public.portfolio_snapshots(user_id, snapshot_date);
create index if not exists idx_dashboard_runs_user on public.dashboard_runs(user_id, created_at desc);
create unique index if not exists uq_accounts_import_row on public.banking_accounts(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_equity_holdings_import_row on public.equity_holdings(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_mf_holdings_import_row on public.mutual_fund_holdings(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_etf_holdings_import_row on public.etf_holdings(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_crypto_holdings_import_row on public.crypto_holdings(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_goals_import_row on public.goals(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_bank_tx_import on public.bank_transactions(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_equity_tx_import on public.equity_transactions(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_mf_tx_import on public.mf_transactions(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_etf_tx_import on public.etf_transactions(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_crypto_tx_import on public.crypto_transactions(user_id, source_row_hash) where source_row_hash is not null;

alter table public.import_batches enable row level security;
alter table public.import_row_errors enable row level security;
alter table public.mf_transactions enable row level security;
alter table public.market_price_cache enable row level security;
alter table public.price_sync_runs enable row level security;

-- New Supabase projects may not grant new public tables to service_role by
-- default. QUANT's trusted backend requires these explicit privileges.
grant usage on schema public to service_role;
grant select, insert, update, delete on table
  public.import_batches,
  public.import_row_errors,
  public.mf_transactions,
  public.market_price_cache,
  public.price_sync_runs
to service_role;

commit;

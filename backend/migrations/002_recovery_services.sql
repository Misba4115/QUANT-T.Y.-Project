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

alter table public.banking_accounts add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.banking_accounts add column if not exists source_row_hash text;
alter table public.equity_holdings add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.equity_holdings add column if not exists source_row_hash text;
alter table public.mutual_fund_holdings add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.mutual_fund_holdings add column if not exists source_row_hash text;
alter table public.etf_holdings add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.etf_holdings add column if not exists source_row_hash text;
alter table public.crypto_holdings add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.crypto_holdings add column if not exists source_row_hash text;
alter table public.goals add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.goals add column if not exists source_row_hash text;
alter table public.bank_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.equity_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.mf_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.etf_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
alter table public.crypto_transactions add column if not exists import_batch_id uuid references public.import_batches(import_batch_id) on delete set null;
create table if not exists public.import_row_errors (
  import_row_error_id uuid primary key default gen_random_uuid(),
  import_batch_id uuid not null references public.import_batches(import_batch_id) on delete cascade,
  row_number integer not null,
  code text not null,
  message text not null,
  raw_row jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.market_price_cache (
  price_cache_id uuid primary key default gen_random_uuid(),
  asset_type text not null,
  instrument_key text not null,
  price numeric(20,6) not null check (price >= 0),
  currency text not null default 'INR',
  provider text not null,
  source_timestamp timestamptz not null,
  fetched_at timestamptz not null default timezone('utc', now()),
  status text not null check (status in ('live','delayed','stored','stale')),
  unique(asset_type, instrument_key, provider)
);
create table if not exists public.price_sync_runs (
  price_sync_run_id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(user_id) on delete cascade,
  status text not null check (status in ('pending','processing','completed','partial','failed')),
  requested_count integer not null default 0,
  updated_count integer not null default 0,
  failed_count integer not null default 0,
  errors jsonb not null default '[]'::jsonb,
  started_at timestamptz not null default timezone('utc', now()),
  completed_at timestamptz
);
create table if not exists public.portfolio_snapshots (
  snapshot_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  snapshot_date date not null,
  net_worth numeric(20,2) not null,
  allocation jsonb not null default '[]'::jsonb,
  valuation_coverage numeric(6,3) not null default 0,
  source_status jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  unique(user_id, snapshot_date)
);
create table if not exists public.dashboard_runs (
  run_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  status text not null check (status in ('pending','processing','completed','partial','failed')),
  params jsonb not null default '{}'::jsonb,
  result jsonb,
  error text,
  processing_time_ms integer,
  created_at timestamptz not null default timezone('utc', now()),
  completed_at timestamptz
);
create table if not exists public.dashboard_configs (
  dashboard_config_id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references public.users(user_id) on delete cascade,
  widgets jsonb not null default '[]'::jsonb,
  time_period text not null default '1y',
  updated_at timestamptz not null default timezone('utc', now())
);

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

do $$
declare table_name text;
begin
  foreach table_name in array array['import_batches','import_row_errors','market_price_cache','price_sync_runs','portfolio_snapshots','dashboard_runs','dashboard_configs']
  loop
    execute format('alter table public.%I enable row level security', table_name);
  end loop;
end $$;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant usage on schema public to service_role';
    execute 'grant select, insert, update, delete on table public.import_batches, public.import_row_errors, public.market_price_cache, public.price_sync_runs, public.portfolio_snapshots, public.dashboard_runs, public.dashboard_configs to service_role';
  end if;
end $$;

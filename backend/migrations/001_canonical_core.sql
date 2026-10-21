create extension if not exists pgcrypto;

create or replace function public.quant_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.users (
  user_id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  name text,
  phone text,
  age integer check (age is null or age between 18 and 120),
  monthly_income numeric(18,2) not null default 0 check (monthly_income >= 0),
  monthly_expenses numeric(18,2) not null default 0 check (monthly_expenses >= 0),
  primary_goal text,
  risk_profile text check (risk_profile is null or risk_profile in ('conservative','moderate','aggressive')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.banking_accounts (
  account_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  account_type text not null check (account_type in ('savings','current','fixed_deposit','recurring_deposit')),
  account_name text not null,
  institution text not null,
  account_number text,
  current_balance numeric(18,2) not null default 0 check (current_balance >= 0),
  currency text not null default 'INR',
  is_primary boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.equity_holdings (
  equity_holding_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  symbol text not null,
  equity_name text not null,
  exchange text not null default 'NSE',
  quantity numeric(24,8) not null check (quantity > 0),
  avg_price numeric(18,4) not null check (avg_price >= 0),
  broker text,
  demat_account text,
  current_price numeric(18,4),
  current_value numeric(20,2),
  price_source text,
  source_timestamp timestamptz,
  last_synced_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.mutual_fund_holdings (
  mf_holding_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  mf_name text not null,
  scheme_code text,
  isin text,
  fund_house text,
  category text,
  units numeric(24,8) not null check (units > 0),
  avg_nav numeric(18,4) not null check (avg_nav >= 0),
  platform text,
  folio_number text,
  current_nav numeric(18,4),
  current_value numeric(20,2),
  price_source text,
  source_timestamp timestamptz,
  last_synced_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.etf_holdings (
  etf_holding_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  symbol text not null,
  etf_name text not null,
  isin text,
  exchange text not null default 'NSE',
  category text,
  quantity numeric(24,8) not null check (quantity > 0),
  avg_price numeric(18,4) not null check (avg_price >= 0),
  broker text,
  demat_account text,
  current_price numeric(18,4),
  current_value numeric(20,2),
  price_source text,
  source_timestamp timestamptz,
  last_synced_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.crypto_holdings (
  crypto_holding_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  symbol text not null,
  crypto_name text not null,
  network text,
  quantity numeric(30,12) not null check (quantity > 0),
  avg_price numeric(20,4) not null check (avg_price >= 0),
  exchange text,
  wallet_address text,
  current_price numeric(20,4),
  current_value numeric(20,2),
  price_source text,
  source_timestamp timestamptz,
  last_synced_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.goals (
  goal_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  goal_name text not null,
  goal_type text not null default 'custom',
  target_amount numeric(20,2),
  current_saved numeric(20,2) not null default 0 check (current_saved >= 0),
  target_date date,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.bank_transactions (
  bank_tx_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  account_id uuid references public.banking_accounts(account_id) on delete set null,
  tx_date date not null,
  occurred_at timestamptz,
  occurred_local_hour smallint check (occurred_local_hour between 0 and 23),
  description text not null,
  amount numeric(20,2) not null check (amount > 0),
  tx_type text not null check (tx_type in ('debit','credit')),
  category text,
  source text,
  source_row_hash text,
  is_anomaly boolean not null default false,
  anomaly_score double precision,
  anomaly_model_version text,
  anomaly_detected_at timestamptz,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.equity_transactions (
  equity_tx_id uuid primary key default gen_random_uuid(), user_id uuid not null references public.users(user_id) on delete cascade,
  tx_date date not null, symbol text not null, quantity numeric(24,8) not null, price numeric(18,4) not null,
  tx_type text not null, fees numeric(18,2) default 0, source text, source_row_hash text,
  is_anomaly boolean not null default false, anomaly_score double precision, anomaly_model_version text, anomaly_detected_at timestamptz,
  created_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.mf_transactions (
  mf_tx_id uuid primary key default gen_random_uuid(), user_id uuid not null references public.users(user_id) on delete cascade,
  tx_date date not null, scheme_code text, mf_name text not null, units numeric(24,8) not null, nav numeric(18,4) not null,
  tx_type text not null, source text, source_row_hash text,
  is_anomaly boolean not null default false, anomaly_score double precision, anomaly_model_version text, anomaly_detected_at timestamptz,
  created_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.etf_transactions (
  etf_tx_id uuid primary key default gen_random_uuid(), user_id uuid not null references public.users(user_id) on delete cascade,
  tx_date date not null, symbol text not null, quantity numeric(24,8) not null, price numeric(18,4) not null,
  tx_type text not null, fees numeric(18,2) default 0, source text, source_row_hash text,
  is_anomaly boolean not null default false, anomaly_score double precision, anomaly_model_version text, anomaly_detected_at timestamptz,
  created_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.crypto_transactions (
  crypto_tx_id uuid primary key default gen_random_uuid(), user_id uuid not null references public.users(user_id) on delete cascade,
  tx_date date not null, symbol text not null, quantity numeric(30,12) not null, price numeric(20,4) not null,
  tx_type text not null, fees numeric(18,2) default 0, source text, source_row_hash text,
  is_anomaly boolean not null default false, anomaly_score double precision, anomaly_model_version text, anomaly_detected_at timestamptz,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.chat_conversations (
  conversation_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  conversation_title text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.chat_messages (
  message_id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.chat_conversations(conversation_id) on delete cascade,
  role text not null check (role in ('user','assistant','system')),
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_accounts_user on public.banking_accounts(user_id);
create index if not exists idx_equity_holdings_user_symbol on public.equity_holdings(user_id, symbol);
create index if not exists idx_mf_holdings_user_scheme on public.mutual_fund_holdings(user_id, scheme_code);
create index if not exists idx_etf_holdings_user_symbol on public.etf_holdings(user_id, symbol);
create index if not exists idx_crypto_holdings_user_symbol on public.crypto_holdings(user_id, symbol);
create index if not exists idx_goals_user on public.goals(user_id);
create index if not exists idx_bank_tx_user_date on public.bank_transactions(user_id, tx_date desc);
create index if not exists idx_equity_tx_user_date on public.equity_transactions(user_id, tx_date desc);
create index if not exists idx_mf_tx_user_date on public.mf_transactions(user_id, tx_date desc);
create index if not exists idx_etf_tx_user_date on public.etf_transactions(user_id, tx_date desc);
create index if not exists idx_crypto_tx_user_date on public.crypto_transactions(user_id, tx_date desc);
create index if not exists idx_conversations_user on public.chat_conversations(user_id, updated_at desc);
create index if not exists idx_messages_conversation on public.chat_messages(conversation_id, created_at);
create unique index if not exists uq_bank_tx_import on public.bank_transactions(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_equity_tx_import on public.equity_transactions(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_mf_tx_import on public.mf_transactions(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_etf_tx_import on public.etf_transactions(user_id, source_row_hash) where source_row_hash is not null;
create unique index if not exists uq_crypto_tx_import on public.crypto_transactions(user_id, source_row_hash) where source_row_hash is not null;

drop trigger if exists users_set_updated_at on public.users;
create trigger users_set_updated_at before update on public.users for each row execute function public.quant_set_updated_at();

do $$
declare table_name text;
begin
  foreach table_name in array array['users','banking_accounts','equity_holdings','mutual_fund_holdings','etf_holdings','crypto_holdings','goals','bank_transactions','equity_transactions','mf_transactions','etf_transactions','crypto_transactions','chat_conversations','chat_messages']
  loop
    execute format('alter table public.%I enable row level security', table_name);
  end loop;
end $$;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant usage on schema public to service_role';
    execute 'grant select, insert, update, delete on all tables in schema public to service_role';
  end if;
end $$;

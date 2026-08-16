-- Transform the canonical core fixture into the read-only-inventoried hosted legacy shape.
drop table public.mf_transactions;

alter table public.users drop column updated_at;
alter table public.goals drop column updated_at;
alter table public.chat_messages drop column metadata;

alter table public.equity_holdings drop column price_source, drop column source_timestamp;
alter table public.mutual_fund_holdings drop column price_source, drop column source_timestamp;
alter table public.etf_holdings drop column price_source, drop column source_timestamp;
alter table public.crypto_holdings drop column price_source, drop column source_timestamp;

drop index public.uq_bank_tx_import;
alter table public.bank_transactions
  drop column source, drop column source_row_hash,
  drop column anomaly_model_version, drop column anomaly_detected_at;

drop index public.uq_equity_tx_import;
drop index public.uq_etf_tx_import;
drop index public.uq_crypto_tx_import;
alter table public.equity_transactions
  drop column fees, drop column source, drop column source_row_hash,
  drop column anomaly_model_version, drop column anomaly_detected_at,
  add column amount numeric(20,2) not null default 0,
  add column charges numeric(18,2) not null default 0,
  add column net_amount numeric(20,2),
  add column description text,
  add column broker text,
  add column order_id text;
alter table public.etf_transactions
  drop column fees, drop column source, drop column source_row_hash,
  drop column anomaly_model_version, drop column anomaly_detected_at,
  add column amount numeric(20,2) not null default 0,
  add column charges numeric(18,2) not null default 0,
  add column net_amount numeric(20,2),
  add column description text,
  add column broker text,
  add column order_id text;
alter table public.crypto_transactions
  drop column fees, drop column source, drop column source_row_hash,
  drop column anomaly_model_version, drop column anomaly_detected_at,
  add column amount numeric(20,2) not null default 0,
  add column charges numeric(18,2) not null default 0,
  add column net_amount numeric(20,2),
  add column description text,
  add column tx_hash text;

create table public.portfolio_snapshots (
  snapshot_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id),
  snapshot_date date not null,
  total_value numeric(20,2) not null,
  equity_value numeric(20,2) default 0,
  mf_value numeric(20,2) default 0,
  etf_value numeric(20,2) default 0,
  crypto_value numeric(20,2) default 0,
  cash_value numeric(20,2) default 0,
  created_at timestamp default now(),
  unique(user_id, snapshot_date)
);

create table public.dashboard_runs (
  run_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id),
  requested_at timestamp default now(),
  run_status text default 'pending',
  run_params jsonb,
  run_result jsonb,
  processing_time_ms integer,
  error_message text
);

create table public.dashboard_configs (
  config_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id),
  selected_widgets jsonb,
  default_time_period text,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

insert into public.users (email, password_hash, name) values ('fixture@example.com', 'fixture', 'Fixture User');
insert into public.portfolio_snapshots (user_id, snapshot_date, total_value)
select user_id, current_date, 123456.78 from public.users where email = 'fixture@example.com';
insert into public.dashboard_runs (user_id, run_status, run_params)
select user_id, 'completed', '{"time_period":"1y"}'::jsonb from public.users where email = 'fixture@example.com';
insert into public.dashboard_configs (user_id, selected_widgets, default_time_period)
select user_id, '["net_worth"]'::jsonb, '1y' from public.users where email = 'fixture@example.com';

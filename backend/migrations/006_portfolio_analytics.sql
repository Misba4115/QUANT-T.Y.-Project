-- Historical market evidence required for benchmark beta and Markowitz analytics.
-- Rows are user-scoped because the set of tracked instruments reveals portfolio data.
create table if not exists public.market_price_history (
  price_history_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  asset_type text not null,
  instrument_key text not null,
  price_date date not null,
  adjusted_close numeric(20,6) not null check (adjusted_close > 0),
  currency text not null default 'INR',
  provider text not null,
  fetched_at timestamptz not null default timezone('utc', now()),
  unique(user_id, asset_type, instrument_key, price_date, provider)
);

create index if not exists idx_market_history_user_instrument_date
  on public.market_price_history(user_id, asset_type, instrument_key, price_date);

alter table public.market_price_history enable row level security;

do $$ begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant usage on schema public to service_role';
    execute 'grant select, insert, update, delete on table public.market_price_history to service_role';
  end if;
end $$;

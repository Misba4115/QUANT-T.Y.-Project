-- QUANT uses custom authentication. Access is backend-only and user-scoped;
-- Supabase auth.uid() is not the identity source for this application.
create table if not exists public.investment_comparisons (
  user_id uuid not null references public.users(user_id) on delete cascade,
  category_id text not null check (category_id in ('deposit','debt','mf','etf','gold','equity','crypto')),
  option_id text not null check (length(option_id) between 1 and 80),
  platform_id text not null check (length(platform_id) between 1 and 80),
  years integer not null default 5 check (years between 1 and 20),
  amount numeric(18,2) not null default 10000 check (amount between 1 and 100000000),
  created_at timestamptz not null default now(),
  primary key (user_id, category_id, option_id, platform_id)
);
alter table public.investment_comparisons enable row level security;
revoke all on public.investment_comparisons from public, anon, authenticated;
grant select, insert, update, delete on public.investment_comparisons to service_role;

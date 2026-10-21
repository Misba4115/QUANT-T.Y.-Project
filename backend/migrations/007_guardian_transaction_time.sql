-- Optional source clock time for bank transactions. Historical date-only rows
-- remain NULL and cannot support odd-hour or exact-timestamp duplicate rules.
alter table public.bank_transactions add column if not exists occurred_at timestamptz;
alter table public.bank_transactions add column if not exists occurred_local_hour smallint
  check (occurred_local_hour between 0 and 23);

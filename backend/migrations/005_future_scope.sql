-- QUANT Phase 3 future-scope schema. Secrets are encrypted by the application
-- before insertion; raw provider payloads have explicit retention timestamps.
create table if not exists public.connector_accounts (
  connector_account_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  provider text not null check (provider in ('upstox','sandbox')),
  provider_account_id text,
  display_name text not null,
  status text not null check (status in ('pending','connected','reauthorization_required','revoked','error')),
  capability_mode text not null default 'interactive',
  capabilities jsonb not null default '[]'::jsonb,
  encrypted_credentials text,
  credentials_expires_at timestamptz,
  last_successful_sync_at timestamptz,
  last_error text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique(user_id, provider, provider_account_id)
);
create table if not exists public.connector_oauth_states (
  oauth_state_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  provider text not null,
  state_hash text not null unique,
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.connector_sync_runs (
  connector_sync_run_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  connector_account_id uuid not null references public.connector_accounts(connector_account_id) on delete cascade,
  status text not null check (status in ('preview','processing','completed','partial','failed')),
  cursor_before text, cursor_after text,
  additions integer not null default 0, updates integer not null default 0,
  duplicates integer not null default 0, conflicts integer not null default 0,
  preview jsonb not null default '[]'::jsonb,
  error text,
  started_at timestamptz not null default timezone('utc', now()), completed_at timestamptz
);
create table if not exists public.connector_sync_items (
  connector_sync_item_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  connector_sync_run_id uuid not null references public.connector_sync_runs(connector_sync_run_id) on delete cascade,
  provider_item_id text, fingerprint text not null,
  canonical_table text not null, canonical_record_id uuid,
  action text not null check (action in ('add','update','duplicate','conflict','retained')),
  source_timestamp timestamptz, ingested_at timestamptz not null default timezone('utc', now()),
  raw_payload jsonb, purge_after timestamptz,
  unique(user_id, connector_sync_run_id, fingerprint)
);
create table if not exists public.ingestion_inboxes (
  ingestion_inbox_id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references public.users(user_id) on delete cascade,
  address_token_hash text not null unique,
  status text not null default 'active' check (status in ('active','revoked')),
  allowed_senders jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default timezone('utc', now()), updated_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.ingestion_messages (
  ingestion_message_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  ingestion_inbox_id uuid not null references public.ingestion_inboxes(ingestion_inbox_id) on delete cascade,
  external_message_id text not null, sender_hash text not null, attachment_hash text not null,
  filename text not null, content_type text not null, byte_size integer not null,
  storage_key text, import_batch_id uuid references public.import_batches(import_batch_id) on delete set null,
  status text not null check (status in ('received','rejected','review_ready','committed','failed')),
  rejection_reason text, received_at timestamptz not null default timezone('utc', now()),
  purge_after timestamptz not null,
  unique(ingestion_inbox_id, external_message_id, attachment_hash)
);
create table if not exists public.notification_preferences (
  notification_preference_id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references public.users(user_id) on delete cascade,
  in_app_enabled boolean not null default true, email_enabled boolean not null default false,
  minimum_severity text not null default 'info' check (minimum_severity in ('info','warning','critical')),
  quiet_hours_start time, quiet_hours_end time, timezone text not null default 'Asia/Kolkata',
  weekly_summary boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()), updated_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.notifications (
  notification_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  event_key text not null, category text not null,
  severity text not null check (severity in ('info','warning','critical')),
  title text not null, body text not null, evidence jsonb not null default '{}'::jsonb,
  deep_link text, read_at timestamptz, acknowledged_at timestamptz, archived_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  unique(user_id, event_key)
);
create table if not exists public.notification_deliveries (
  notification_delivery_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  notification_id uuid not null references public.notifications(notification_id) on delete cascade,
  channel text not null check (channel in ('in_app','email','adb_dev')),
  status text not null check (status in ('pending','suppressed','sent','failed','dead_letter')),
  attempt_count integer not null default 0, last_error text, next_attempt_at timestamptz,
  sent_at timestamptz, created_at timestamptz not null default timezone('utc', now()),
  unique(notification_id, channel)
);
create table if not exists public.job_schedules (
  job_schedule_id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(user_id) on delete cascade,
  job_type text not null, enabled boolean not null default true,
  interval_seconds integer not null check (interval_seconds >= 60),
  next_run_at timestamptz not null, locked_until timestamptz, last_run_at timestamptz,
  config jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()), updated_at timestamptz not null default timezone('utc', now()),
  unique(user_id, job_type)
);
create table if not exists public.job_runs (
  job_run_id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(user_id) on delete cascade,
  job_schedule_id uuid references public.job_schedules(job_schedule_id) on delete set null,
  job_type text not null, idempotency_key text not null unique,
  status text not null check (status in ('processing','completed','partial','failed')),
  result jsonb, error text, started_at timestamptz not null default timezone('utc', now()), completed_at timestamptz
);
create table if not exists public.guardian_events (
  guardian_event_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  event_id text not null, asset_type text not null, event_type text not null,
  occurred_at timestamptz not null, received_at timestamptz not null default timezone('utc', now()),
  payload jsonb not null, status text not null default 'pending' check (status in ('pending','processed','failed')),
  processed_at timestamptz, unique(user_id, event_id)
);
create table if not exists public.guardian_alerts (
  guardian_alert_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  guardian_event_id uuid not null references public.guardian_events(guardian_event_id) on delete cascade,
  rule_version text not null, alert_type text not null, severity text not null,
  title text not null, explanation text not null, evidence jsonb not null,
  cooldown_key text not null, created_at timestamptz not null default timezone('utc', now()),
  unique(user_id, cooldown_key, rule_version)
);
create table if not exists public.guardian_feedback (
  guardian_feedback_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  guardian_alert_id uuid not null references public.guardian_alerts(guardian_alert_id) on delete cascade,
  verdict text not null check (verdict in ('expected','incorrect','investigate')),
  note text, created_at timestamptz not null default timezone('utc', now()),
  unique(user_id, guardian_alert_id)
);
create table if not exists public.risk_assessments (
  risk_assessment_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  model_version text not null, inputs jsonb not null, dimensions jsonb not null,
  overall_score numeric(6,2) not null, uncertainty numeric(6,3) not null,
  assessed_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.user_preferences (
  user_preference_id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references public.users(user_id) on delete cascade,
  persona text not null default 'guided' check (persona in ('guided','analytical','minimal')),
  explanation_depth text not null default 'balanced' check (explanation_depth in ('concise','balanced','detailed')),
  dashboard_emphasis jsonb not null default '[]'::jsonb, explicit_feedback jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()), updated_at timestamptz not null default timezone('utc', now())
);
create table if not exists public.report_exports (
  report_export_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  format text not null check (format in ('pdf','png')),
  status text not null check (status in ('processing','completed','failed','expired')),
  params jsonb not null, storage_key text, content_hash text, expires_at timestamptz,
  error text, created_at timestamptz not null default timezone('utc', now()), completed_at timestamptz
);
create table if not exists public.analytics_runs (
  analytics_run_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  instrument text not null, model_type text not null, model_version text not null,
  params jsonb not null, result jsonb not null, data_source text not null,
  data_as_of timestamptz not null, created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_connector_accounts_user on public.connector_accounts(user_id, provider);
create index if not exists idx_connector_sync_user_started on public.connector_sync_runs(user_id, started_at desc);
create index if not exists idx_notifications_user_created on public.notifications(user_id, created_at desc);
create index if not exists idx_jobs_due on public.job_schedules(enabled, next_run_at);
create index if not exists idx_guardian_events_pending on public.guardian_events(status, received_at);
create index if not exists idx_risk_user_assessed on public.risk_assessments(user_id, assessed_at desc);

do $$ declare table_name text;
begin
  foreach table_name in array array[
    'connector_accounts','connector_oauth_states','connector_sync_runs','connector_sync_items',
    'ingestion_inboxes','ingestion_messages','notification_preferences','notifications',
    'notification_deliveries','job_schedules','job_runs','guardian_events','guardian_alerts',
    'guardian_feedback','risk_assessments','user_preferences','report_exports','analytics_runs'
  ] loop execute format('alter table public.%I enable row level security', table_name); end loop;
end $$;

do $$ begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant usage on schema public to service_role';
    execute 'grant select, insert, update, delete on all tables in schema public to service_role';
  end if;
end $$;

create or replace function public.claim_due_job_schedules(p_limit integer default 10)
returns setof public.job_schedules
language plpgsql security definer set search_path = public
as $$
begin
  return query
  with due as (
    select job_schedule_id from public.job_schedules
    where enabled = true and next_run_at <= timezone('utc', now())
      and (locked_until is null or locked_until < timezone('utc', now()))
    order by next_run_at for update skip locked limit greatest(1, least(p_limit, 100))
  )
  update public.job_schedules s
  set locked_until = timezone('utc', now()) + interval '5 minutes', updated_at = timezone('utc', now())
  from due where s.job_schedule_id = due.job_schedule_id returning s.*;
end;
$$;
revoke all on function public.claim_due_job_schedules(integer) from public, anon, authenticated;
grant execute on function public.claim_due_job_schedules(integer) to service_role;

-- Supabase service-role only bucket. User-facing access is always mediated by
-- authenticated application endpoints; no public storage policy is created.
insert into storage.buckets (id, name, public, file_size_limit)
values ('quant-secure-ingestion', 'quant-secure-ingestion', false, 10485760)
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit;

alter table public.dashboard_configs add column if not exists chart_preferences jsonb not null default '{}'::jsonb;
alter table public.dashboard_configs add column if not exists custom_date_from date;
alter table public.dashboard_configs add column if not exists custom_date_to date;
alter table public.dashboard_configs add column if not exists currency text not null default 'INR';
alter table public.equity_holdings add column if not exists source_provider text;
alter table public.equity_holdings add column if not exists source_provider_item_id text;
alter table public.mutual_fund_holdings add column if not exists source_provider text;
alter table public.mutual_fund_holdings add column if not exists source_provider_item_id text;
create unique index if not exists uq_equity_provider_item
  on public.equity_holdings(user_id, source_provider, source_provider_item_id)
  where source_provider_item_id is not null;
create unique index if not exists uq_mf_provider_item
  on public.mutual_fund_holdings(user_id, source_provider, source_provider_item_id)
  where source_provider_item_id is not null;

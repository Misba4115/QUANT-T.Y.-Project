-- Finalized Phase 2.5 runtime persistence contracts.
create table if not exists public.conversation_summaries (
  summary_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  conversation_id uuid not null references public.chat_conversations(conversation_id) on delete cascade,
  summary text not null, summary_version text not null, message_count integer not null check (message_count > 8),
  content_hash text not null check (content_hash ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default timezone('utc', now()), updated_at timestamptz not null default timezone('utc', now()),
  unique(user_id, conversation_id)
);
create table if not exists public.outcome_evaluations (
  outcome_evaluation_id uuid primary key default gen_random_uuid(),
  delivered_output_ref text not null, target_version text not null,
  labelled_outcome jsonb not null, metrics jsonb not null, sample_count integer not null check (sample_count >= 0),
  calibration_proposal jsonb,
  status text not null check (status in ('observed','review_required','approved','rejected')),
  automatic_mutation boolean not null default false check (automatic_mutation = false),
  created_at timestamptz not null default timezone('utc', now())
);
create index if not exists idx_conversation_summaries_user_updated on public.conversation_summaries(user_id, updated_at desc);
create index if not exists idx_outcome_evaluations_target_created on public.outcome_evaluations(target_version, created_at desc);
alter table public.conversation_summaries enable row level security;
alter table public.outcome_evaluations enable row level security;
do $$ begin if exists (select 1 from pg_roles where rolname='service_role') then
  execute 'grant select, insert, update, delete on table public.conversation_summaries to service_role';
  execute 'grant select, insert, update, delete on table public.outcome_evaluations to service_role';
end if; end $$;

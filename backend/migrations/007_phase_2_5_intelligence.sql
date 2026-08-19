-- Phase 2.5-4 only: authoritative public-knowledge registry and review lifecycle.
-- Later Phase 2.5 tables are deliberately omitted until their contracts are frozen.

create table if not exists public.knowledge_sources (
  source_id text primary key,
  authority text not null,
  official_domain text not null,
  listing_url text not null check (listing_url like 'https://%'),
  document_family text not null,
  topic_tags jsonb not null default '[]'::jsonb check (jsonb_typeof(topic_tags) = 'array'),
  jurisdiction text not null default 'IN',
  discovery_schedule text not null,
  expected_content_types jsonb not null default '[]'::jsonb check (jsonb_typeof(expected_content_types) = 'array'),
  review_required boolean not null default true,
  status text not null check (status in ('active','suspended')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.knowledge_document_versions (
  knowledge_version_id uuid primary key default gen_random_uuid(),
  source_id text not null references public.knowledge_sources(source_id) on update cascade on delete restrict,
  document_url text not null check (document_url like 'https://%'),
  title text not null,
  content_hash text not null check (content_hash ~ '^[0-9a-f]{64}$'),
  content_type text not null check (content_type in ('text/html','text/plain','application/pdf')),
  content_bytes bigint not null check (content_bytes > 0 and content_bytes <= 15728640),
  extracted_text text,
  diff_text text,
  parser_version text not null,
  status text not null check (status in ('staged','quarantined','active','superseded','rejected')),
  quarantine_reason text,
  retrieved_at timestamptz not null,
  published_at timestamptz,
  published_by text,
  unique(source_id, content_hash),
  check ((status = 'quarantined') = (quarantine_reason is not null))
);

create table if not exists public.knowledge_reviews (
  knowledge_review_id uuid primary key default gen_random_uuid(),
  knowledge_version_id uuid not null references public.knowledge_document_versions(knowledge_version_id) on delete cascade,
  status text not null check (status in ('pending','approved','rejected')),
  material_change boolean not null,
  reviewer_id text,
  rationale text,
  reviewed_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  unique(knowledge_version_id),
  check (
    (status = 'pending' and reviewer_id is null and reviewed_at is null)
    or (status in ('approved','rejected') and reviewer_id is not null and reviewed_at is not null)
  )
);

create index if not exists idx_knowledge_versions_source_retrieved
  on public.knowledge_document_versions(source_id, retrieved_at desc);
create index if not exists idx_knowledge_versions_status
  on public.knowledge_document_versions(status, retrieved_at desc);
create index if not exists idx_knowledge_reviews_pending
  on public.knowledge_reviews(status, created_at) where status = 'pending';

alter table public.knowledge_sources enable row level security;
alter table public.knowledge_document_versions enable row level security;
alter table public.knowledge_reviews enable row level security;

do $$ begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant select, insert, update, delete on table public.knowledge_sources to service_role';
    execute 'grant select, insert, update, delete on table public.knowledge_document_versions to service_role';
    execute 'grant select, insert, update, delete on table public.knowledge_reviews to service_role';
  end if;
end $$;

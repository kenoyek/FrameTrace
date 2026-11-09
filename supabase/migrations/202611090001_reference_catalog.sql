-- Initial controlled-catalog schema. Apply only to a new development database.
-- Never put a service-role key or recognition capability hash in a mobile app.
begin;
create table public.reference_media (
    id text primary key,
    title text not null,
    publisher text not null,
    rights_basis text not null,
    source_url text,
    duration double precision not null check (duration > 0),
    fingerprint_version text not null default 'dhash64-v1-fps2',
    fingerprints jsonb not null,
    revoked boolean not null default false
);
create table public.recognition_jobs (
    id text primary key,
    token_hash text not null,
    status text not null default 'queued',
    result jsonb,
    error text,
    created_at timestamptz not null default now()
);
create table public.recognition_matches (
    job_id text references public.recognition_jobs(id) on delete cascade,
    reference_id text references public.reference_media(id),
    primary key (job_id, reference_id)
);
create index recognition_jobs_retention_idx on public.recognition_jobs(created_at);
alter table public.reference_media enable row level security;
alter table public.recognition_jobs enable row level security;
alter table public.recognition_matches enable row level security;
-- Deny direct PostgREST/client access. Server API implements capability ownership.
revoke all on public.reference_media, public.recognition_jobs, public.recognition_matches from anon, authenticated;
commit;

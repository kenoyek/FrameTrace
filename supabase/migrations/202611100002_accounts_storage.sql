begin;
create table public.recognition_accounts (
    job_id text primary key references public.recognition_jobs(id) on delete cascade,
    user_id text not null,
    saved boolean not null default false,
    clip_expired boolean not null default false
);
create index recognition_accounts_user_idx on public.recognition_accounts(user_id);
-- No foreign key: deletion outbox must survive removal of its job/history.
create table public.query_objects (
    job_id text primary key,
    bucket text not null,
    object_key text not null unique,
    content_hash text not null,
    size_bytes bigint not null check (size_bytes > 0),
    pending_delete boolean not null default false
);
alter table public.recognition_accounts enable row level security;
alter table public.query_objects enable row level security;
-- All user history goes through JWT-verified API ownership checks, not direct PostgREST.
revoke all on public.recognition_accounts, public.query_objects from anon, authenticated;
commit;

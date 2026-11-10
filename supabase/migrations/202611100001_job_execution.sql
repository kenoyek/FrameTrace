-- Additive reliability state; no existing job tokens or results are rewritten.
begin;
create table public.recognition_execution (
    job_id text primary key references public.recognition_jobs(id) on delete cascade,
    submission_hash text unique,
    content_hash text,
    owner text,
    lease_until double precision not null default 0,
    dispatch_after double precision not null default 0,
    attempts integer not null default 0 check (attempts >= 0)
);
insert into public.recognition_execution(job_id) select id from public.recognition_jobs;
alter table public.recognition_execution enable row level security;
revoke all on public.recognition_execution from anon, authenticated;
commit;

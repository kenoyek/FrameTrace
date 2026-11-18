begin;
create table public.recognition_feedback (
    job_id text primary key references public.recognition_jobs(id) on delete cascade,
    rating text not null check (rating in ('helpful', 'not_helpful', 'unsure'))
);
alter table public.recognition_feedback enable row level security;
-- Reads and updates go through the API's existing job ownership checks.
revoke all on public.recognition_feedback from anon, authenticated;
commit;

begin;
create table public.catalog_audit (
    id text primary key,
    reference_id text not null,
    action text not null check (action in ('ingest', 'revoke')),
    actor varchar(120) not null,
    reason varchar(500) not null,
    created_at timestamptz not null default now()
);
create index catalog_audit_reference_idx on public.catalog_audit(reference_id);
alter table public.catalog_audit enable row level security;
revoke all on public.catalog_audit from anon, authenticated;
-- Server/operator DB credentials remain trusted; this is not a tamper-proof ledger.
commit;

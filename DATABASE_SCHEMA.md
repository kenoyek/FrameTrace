# Database schema

- `reference_media`: content SHA-256 ID, title, asserted publisher, rights basis, optional
  operator-verified source URL, duration, fingerprint version, timestamped fingerprints,
  revocation flag. Source URLs are never fetched during recognition.
- `recognition_jobs`: UUID, hashed random per-job access token, actual processing stage,
  JSON evidence result/error, creation timestamp.
- `recognition_execution`: one durable outbox/lease record per job, unique hashed client
  submission capability, uploaded-content SHA-256, lease owner/expiry, dispatch cooldown
  and execution attempt count. No raw capability is stored.
- `recognition_matches`: job-to-reference relationships, enabling future retention/auditing.

SQLAlchemy creates local development tables. The initial and additive reliability migrations under
supabase/migrations enable RLS and denies direct anonymous/authenticated client access.
Backend DB access must use a server-only role. Supabase credentials and policy behavior
have not been validated in a hosted Supabase instance. Do not apply the migration over
SQLAlchemy-created existing tables without a migration/baseline strategy.

New tables: `recognition_accounts` binds jobs to verified user UUIDs and records saved/raw
expiry state. `query_objects` records private bucket/key, digest, size and deletion state;
it intentionally has no job FK so its deletion outbox survives removal of history.

Current guest capability authorization is performed by FastAPI with constant-time comparison.
Account-bound jobs additionally require JWT ownership; guest claiming requires explicit
capability proof. Profiles, identity deletion, audit records and vector indexes remain planned.

The second migration adds the execution table and backfills existing jobs without touching
capabilities/results. Development `initialize()` also creates/backfills it additively; it
is not a general schema migration engine. Apply SQL migrations in timestamp order on hosted
databases under a controlled migration process. Do not rerun create-table migrations over
SQLAlchemy-created development tables without baselining. Local validation covers all four
tables and both client roles; hosted Supabase authentication remains untested.

The latest additive migration enables RLS and denies direct client reads on both new tables.
All account history is mediated by the JWT-verified backend. Defaults: raw clips/guest
metadata 24h; unsaved account history 30 days; saved metadata until deletion.

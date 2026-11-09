# Database schema

- `reference_media`: content SHA-256 ID, title, asserted publisher, rights basis, optional
  operator-verified source URL, duration, fingerprint version, timestamped fingerprints,
  revocation flag. Source URLs are never fetched during recognition.
- `recognition_jobs`: UUID, hashed random per-job access token, actual processing stage,
  JSON evidence result/error, creation timestamp.
- `recognition_matches`: job-to-reference relationships, enabling future retention/auditing.

SQLAlchemy creates local development tables. The initial fresh-database SQL migration under
supabase/migrations enables RLS and denies direct anonymous/authenticated client access.
Backend DB access must use a server-only role. Supabase credentials and policy behavior
have not been validated in a hosted Supabase instance. Do not apply the migration over
SQLAlchemy-created existing tables without a migration/baseline strategy.

Current guest capability authorization is performed by FastAPI with constant-time comparison.
It is not a Supabase session or multi-device account history. Account-linked ownership,
profiles, saved results, audit records, vector indexes and schema upgrades remain planned.

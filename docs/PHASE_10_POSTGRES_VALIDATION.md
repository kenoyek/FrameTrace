# PostgreSQL schema and privacy-boundary validation — 18 November 2026

The migration verifier previously applied every migration but asserted access restrictions
only on the original six tables. It now covers recognition_feedback and catalog_audit,
requires the expected eight public tables, and checks all migrations in filename order.

## Evidence from a real local PostgreSQL run

A local pgvector/pgvector:pg16 Compose service was started. Verification used uniquely
named disposable databases, which were dropped afterward; no hosted database, existing
application schema, cloud environment configuration or production deployment was changed.

- All five migrations applied to a fresh database.
- RLS was enabled on all eight tables. The local anon/authenticated roles were checked
  for absence of superuser/BYPASSRLS flags and denied SELECT/INSERT/UPDATE/DELETE.
- The verifier temporarily granted SELECT in its disposable database and confirmed RLS
  still hid rows, including seeded feedback and audit records. Grants were revoked after
  each role check. This tests defense in depth with simulated client roles, not hosted
  Supabase Auth, role inheritance or actual production service credentials.
- Feedback rejected invalid ratings, duplicate job rows and nonexistent-job references.
  Deleting its parent job cascaded to feedback. Independent catalog audit records remained.
- The PostgreSQL test runner now includes feedback and operator cases alongside reliability
  and accounts. All **42 PostgreSQL tests passed**, including a new concurrent-feedback
  case with nine updates from three threads. The persisted rating remained one valid row.
- This run found and fixed an operator-test teardown dependency: CLI initialization
  backfills execution rows, so teardown must remove them before deleting test jobs.
  SQLite had not enforced that foreign-key dependency. This was a test fixture correction.
- Default SQLite suite: **55 passed, one PostgreSQL-only concurrency test skipped**.
  Python lint/format and diff checks passed. No mobile code changed or device tests ran.

These scripts already run in GitHub CI; expanding them extends subsequent CI runs.
The local run is evidence, not a claim that remote GitHub Actions has completed.

## Reproduce

```sh
docker compose up -d --wait postgres
.venv/bin/python scripts/check_migration.py
.venv/bin/python scripts/check_postgres_reliability.py
.venv/bin/pytest services/api/tests -q
```

Scripts deliberately use the existing local-only Compose connection and need local role
and database creation privileges. Do not point them at a hosted/production instance.
The verifier detects missing/extra tables so future schema additions require updating its
expected table set and boundary assertions. It is not an in-place upgrade/rollback drill.

Hosted migration application, deployment-role least privilege, auth-provider configuration,
network protection and load/deadlock testing remain acceptance tasks. The concurrent test
covers feedback-versus-feedback updates, not every feedback/deletion/revocation race.
Native compilation/device QA and the dependency advisory in SECURITY.md remain open.

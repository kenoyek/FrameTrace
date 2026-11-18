# Local operator review and catalog change records — 18 November 2026

The trusted server CLI now provides:

- `catalog`: paginated ID/title/publisher/duration/revoked metadata, excluding revoked
  references by default. `--include-revoked` includes them. No fingerprint arrays,
  source URLs, file paths or recognition credentials are returned.
- `catalog-audit`: paginated catalog-change records, optionally filtered by reference ID.
  Output includes event ID, reference ID, action, actor label, reason and UTC time.
- `feedback-summary --days N`: retained feedback counts grouped by result classification
  and rating, without job/user IDs, tokens, clips or transcripts. The window is based on
  recognition creation time, not feedback submission time. Deleted feedback is absent;
  there is no lifetime total, accuracy estimate or automatic model training.

Catalog/audit limits are 1–100 rows, with bounded offsets. The summary window is 1–3650
days, default 30. Aggregation scans the retained database and is intended for this small
local deployment; no high-volume reporting system or statistically private aggregation
is claimed. Small count groups can reveal activity to a trusted operator.

Ingestion now requires `--actor`; revocation requires both `--actor` and `--reason`.
Blank/overlong labels and reasons are rejected. Labels are operator assertions, not
verified identities. Use non-sensitive operator labels and operational reasons.
Ingest and revoke append an audit event in the same transaction as the catalog change.
Repeated sequential revocation reports `changed: false` and creates no new event.
Revocation does not reactivate media or erase old records; the existing API suppresses
revoked candidates in historical results. No historical events are fabricated for older
references. Duplicate ingestion remains rejected, including for revoked content.

Audit rows are independent of reference-row foreign keys and remain available for catalog
review; job/history retention does not delete them. No automatic audit retention/erasure
policy is implemented. Database credentials can alter these records: this is not an
immutable, tamper-evident or compliance-certified ledger. Direct SQL changes bypass CLI
audit hooks. Server credential access is the current administrative boundary.

## Migration and validation

The additive migration is `supabase/migrations/202611180002_catalog_audit.sql`. Apply
migrations in filename order before deploying this server version. It enables RLS and
revokes direct anon/authenticated access. Local initialization creates missing tables;
as before, invoking the CLI also runs initialization/backfill. No hosted migration,
admin web UI, remote admin API, external service or environment publication was performed.

All 55 Python tests passed. Nine new operator cases cover ingestion/revocation events,
duplicate/no-op behavior, rollback, audit pagination, summary counts without identifiers,
and CLI argument bounds/context requirements. The CLI ingestion test substitutes feature
extraction to isolate transaction behavior; existing media tests exercise real decoding.
Python lint/format and diff checks passed. No mobile code changed in this phase, so mobile
bundles/device tests were not rerun. PostgreSQL locking/migration behavior and deployment
roles remain hosted acceptance tasks; SQLite tests do not prove them. Existing native
build/signing, accessibility and dependency-security gates remain open.

Examples and the updated required ingest/revoke arguments are in DEVELOPMENT.md.

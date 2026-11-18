# Private structured recognition feedback — 18 November 2026

Completed results now offer optional Helpful, Not helpful and Not sure controls. A saved
rating is acknowledged only after the API accepts it. Failures show a retry message.
The client guards concurrent taps; reopening the result restores its server rating.
No feedback action uploads a clip or changes recognition evidence/scores.

POST /v1/recognitions/{id}/feedback accepts exactly one rating enum, with extra fields
rejected. It uses the existing guest capability or verified account ownership checks,
requires a completed job with a result, and atomically upserts one row per recognition.
Repeated requests are safe; changing the rating replaces the previous value. Concurrent
valid updates use last committed write semantics, with no client timestamp ordering.
Feedback has no free-text field, media, additional user identifier, analytics dispatch,
model training or public read route. Authorized job/history responses include its rating;
existing private no-store response headers also cover feedback responses.

Feedback shares the recognition's lifetime. Explicit result deletion, bulk account-history
removal and retention deletion remove it. Account history kept after raw-clip expiry also
keeps its rating, including saved history. A guest recognition claimed by an account keeps
its existing feedback with the newly account-owned job. Feedback itself is not a legal
consent record, an accuracy label or verified ground truth.

## Schema and rollout

The additive migration is supabase/migrations/202611180001_recognition_feedback.sql. It
adds a constrained enum-like text column, one-row-per-job primary key and cascading job
foreign key, enables RLS, and revokes direct anon/authenticated access. All user access
uses the API; no permissive PostgREST policy is added. Local create_all creates the table.
Apply the migration to a backed-up development database before deploying the updated API.
No hosted migration or deployment was performed. PostgreSQL migration/locking behavior
still needs hosted acceptance; SQLite tests do not establish that behavior.

## Validation

- All 46 Python tests passed, including six feedback tests using the real FastAPI routes,
  database upsert and cleanup. Coverage includes retry/update, no-store responses,
  owner isolation, payload rejection, active-job rejection, history restoration, bulk
  history deletion, explicit deletion and retention. Account feedback tests isolate
  identity with a stub; existing account tests separately exercise JWT verification.
- All 32 mobile tests and strict TypeScript passed, including two feedback transport/auth
  boundary cases and unsuccessful/malformed response handling.
- Python lint/format and diff checks passed; Android/iOS JavaScript bundles exported.
- No native binary/device feedback interaction or hosted database integration is claimed.
  Existing native-build, accessibility and dependency-security gates remain open.

Device acceptance: submit/change each choice, force a network failure and retry, restart
and restore the rating, reopen an account result, verify cross-account rejection, and
check large text/screen-reader radio announcements. Delete the result/history and verify
its feedback disappears. No reviewer/admin aggregation workflow is implemented yet.

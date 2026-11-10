# API

`GET /health` probes database connectivity and reports execution mode. It does not prove
worker readiness; run scripts/smoke_api.py to exercise the entire pipeline.

`POST /v1/recognitions` multipart `file` → HTTP 202 `{id, access_token, status}`.
New jobs return queued; idempotent replay returns the job’s current stage.
For guest jobs, the access token is a possession secret. Account jobs require the owner’s
Supabase JWT in Authorization, even when the per-job token is known. On upload, an optional
Authorization bearer session binds the job to its verified user. Persist securely; do not log or place in URLs.
Size and container limits apply. Full decode validation happens asynchronously. A 202
response establishes durable DB/file acceptance, not successful queue publication or recognition.
An optional secret `X-Submission-Token` (43–128 URL-safe characters, generated with a CSPRNG)
acts as both idempotency token and access capability. Identical bytes/token replay the same
job. A reused token with different bytes returns 409. Tokens expire with job deletion.

`GET /v1/recognitions/{id}` with `Authorization: Bearer TOKEN` → actual stage, result/error.
Stages: queued → extracting_features → searching_catalog → verifying_candidates → completed;
failures set failed. No invented percent progress. Completed result classifications:
matching_segment, possible_match, no_match. Each candidate includes evidence, offset and
uncertainty; source_url may be null. Revoked references suppress prior results too.

`DELETE /v1/recognitions/{id}` with bearer token removes terminal result and access.
Active jobs return 409; cancellation is not yet implemented. Unauthorized or nonexistent
IDs return 404. Broker outages leave accepted jobs queued for scheduler recovery.
Per-process upload admission returns 429 with Retry-After; oversize uploads return 413 and
unsupported containers 415. Corrupt but plausible containers fail in the worker.

The checked-in packages/contracts/openapi.json is generated from the current application.
No public catalog ingestion or arbitrary URL download endpoint is provided.

## Accounts

`GET /v1/history?limit=20&offset=0&saved_only=false` requires a valid Supabase user JWT.
Returns typed items (job/result, saved flag, UTC creation time) and next_offset; limit ≤50,
offset ≤10000. Raw capabilities are never returned by history. Revoked references are
suppressed on history reads too. Offset pagination is a development limit, not stable
snapshot pagination under concurrent history changes.

`PATCH /v1/history/{id}` with `{saved: boolean}` changes only the caller’s entry.
`POST /v1/recognitions/{id}/claim` requires the caller’s JWT plus X-Job-Token containing
the original guest capability. A previously claimed job cannot be transferred.
`DELETE /v1/history` clears up to 1000 terminal records and returns deleted/may_have_more.
If active searches are observed, returns 409; concurrent new searches are retained.
Individual account records use DELETE /v1/recognitions/{id} with the owner’s JWT.
These operations clear history, not the Supabase identity. /v1 responses use no-store.

401 means invalid/missing account authentication; 503 means verification/storage unavailable.
Cross-user job operations return 404. Do not log Authorization, X-Submission-Token or X-Job-Token.

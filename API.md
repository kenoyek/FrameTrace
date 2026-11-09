# API

`GET /health` probes database connectivity and reports execution mode. It does not prove
worker readiness; run scripts/smoke_api.py to exercise the entire pipeline.

`POST /v1/recognitions` multipart `file` → HTTP 202 `{id, access_token, status: queued}`.
The access token is a possession secret. Persist securely; do not log or place in URLs.
Size and container limits apply. Full decode validation happens asynchronously. A 202
response establishes queue submission, not successful recognition.

`GET /v1/recognitions/{id}` with `Authorization: Bearer TOKEN` → actual stage, result/error.
Stages: queued → extracting_features → searching_catalog → verifying_candidates → completed;
failures set failed. No invented percent progress. Completed result classifications:
matching_segment, possible_match, no_match. Each candidate includes evidence, offset and
uncertainty; source_url may be null. Revoked references suppress prior results too.

`DELETE /v1/recognitions/{id}` with bearer token removes terminal result and access.
Active jobs return 409; cancellation is not yet implemented. Unauthorized or nonexistent
IDs return 404. Queue submission failures return 503. Oversize uploads return 413 and
unsupported containers 415. Corrupt but plausible containers fail in the worker.

The checked-in packages/contracts/openapi.json is generated from the current application.
No public catalog ingestion or arbitrary URL download endpoint is provided.

# Security and privacy boundaries

This is a local development service. Bind it to loopback. It is not hardened for public
untrusted traffic. Deployment requires TLS, authenticated ingress, rate/queue quotas,
distributed per-user quotas, isolated decoders and operational monitoring.

Implemented safeguards: random 256-bit job possession capabilities hashed at rest;
constant-time ownership checks; opaque private file paths; no use of supplied filenames;
50 MiB file limit plus a pre-parser bounded request spool and upload admission limit; MP4/MOV signature and decoder validation; 30s query duration;
4K pixel cap; decoder timeouts, single-thread extraction and file-only FFmpeg protocols;
private filesystem permissions; terminal worker cleanup; scheduled retention and CLI; no
arbitrary remote ingestion; no user uploads in catalog; terminal-job deletion and reference
revocation. Mobile saves the latest job capability using platform secure storage.

Residual risks: multipart bodies are spooled twice during parsing but bounded by the total
request limit; admission limits are per process, not distributed user quotas; FFmpeg runs
inside a shared worker container rather than a per-job sandbox; catalog retrieval is
exhaustive; local in-process execution has no recovery scheduler/hard task limit; recovery
requires the database, shared files, Redis, worker and scheduler to return; hosts need
synchronized clocks; hosted Supabase/R2 validation is pending; OAuth, identity deletion, global revocation
and signed direct-upload support remain unfinished.

Do not log tokens, media, transcripts or credentials. Query media is removed on normal
completion/permanent failure; temporary failures retain clips for retry. Abandoned jobs
are handled by the hourly scheduled cleanup operation. Default retention
is 24 hours. Do not promise legal/privacy/store readiness before independent review.

Dependency audit (18 November 2026): `npm audit --omit=dev` reports 34 findings
(32 high, two moderate, zero critical), including inherited Expo/Metro findings from
Picomatch's repeated-extglob ReDoS advisory, GHSA-fc5q-39xc-vjpf. Compatible updates
were applied and Expo native packages aligned to SDK 58.0.26. The registry's latest
Picomatch release, 4.0.7, remains affected; no patched release was available. This is an
open release gate. Use trusted checkouts and do not expose development tooling to
untrusted networks. No zero-vulnerability or completed security-review claim is made.
See docs/PHASE_4_NATIVE_SHARING.md for validation scope.

Submission tokens are bearer secrets, including when used in X-Submission-Token. Gateways
and telemetry must redact this header and Authorization. Raw tokens never enter DB rows.
Retries with a different clip are rejected; idempotency protection ends after deletion or
retention expiry. A locally cached media URI can expire independently; the client requires
explicit confirmation for retry and never automatically uploads on restore.

Account access verifies asymmetric Supabase signatures/claims and checks job ownership.
Guest capabilities cannot access account-bound jobs. History/favorite/deletion operations
are scoped by the verified subject. Native session chunks remain in SecureStore and query
caches clear on identity changes. Read the phase 3 report for JWT revocation limitations.
Private object transfers preserve TLS verification, validate size/hash before decoding and
retry deletion from an independent outbox. A private R2 lifecycle rule is a deployment
prerequisite for remote-upload/DB commit gaps; no hosted lifecycle has been configured.

Native share intake copies authorized temporary content into app-controlled storage before
preview. Android requires a read grant and rejects own-app providers and external file://
URIs; iOS uses security-scoped provider access and protected App Group storage. Native
payloads are untrusted, checked again in JS, and still validated by the backend. Share
handlers never upload automatically. URL-only shares do not trigger downloads and retain
no path/query tokens. Device cache expiration is checked on future app/extension activity,
not an always-running 24h device eraser. Real provider/termination/device tests remain open.

Structured feedback is a bounded rating linked to a job, available only through job ownership checks. It is removed with deleted/expired recognition metadata; retained account history retains its rating. No free-text feedback or automatic training pipeline is implemented.

Operator CLI audit labels are assertions, not authenticated identities. Audit records are transactional with CLI catalog changes but remain editable by trusted database credentials; direct SQL bypasses them. Feedback aggregates are for trusted operators and have no statistical privacy guarantee. No remote admin endpoint is exposed.

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

Dependency audit: SDK 58 removed the initial high-severity SDK 55 findings. Five
moderate advisories remain in the Expo CLI/fingerprint dependency chain (glob/minimatch).
These are build tooling findings; do not expose development tooling to untrusted networks.
No zero-vulnerability or completed security-review claim is made.

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

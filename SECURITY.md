# Security and privacy boundaries

This is a local development service. Bind it to loopback. It is not hardened for public
untrusted traffic. Deployment requires TLS, authenticated ingress, rate/queue quotas,
streaming request-body limits, isolated decoders and operational monitoring.

Implemented safeguards: random 256-bit job possession capabilities hashed at rest;
constant-time ownership checks; opaque private file paths; no use of supplied filenames;
50 MiB application file limit; MP4/MOV signature and decoder validation; 30s query duration;
4K pixel cap; decoder timeouts, single-thread extraction and file-only FFmpeg protocols;
private filesystem permissions; immediate worker cleanup; explicit retention CLI; no
arbitrary remote ingestion; no user uploads in catalog; terminal-job deletion and reference
revocation. Mobile saves the latest job capability using platform secure storage.

Residual risks: multipart parsing can spool before route-level validation; API process has
no global admission/rate limit; FFmpeg runs inside the same worker container rather than
per-job sandbox; catalog retrieval is exhaustive; SQLite/local mode is not crash durable;
workers have no recovery of jobs interrupted mid-processing; duplicate delivery is not
fully transactionally locked; no scheduler runs retention; no Supabase user JWT validation;
no R2 encryption/signed-upload integration; no account deletion/history/export yet.

Do not log tokens, media, transcripts or credentials. Query media is removed on normal
completion/failure; abandoned jobs require the hourly cleanup operation. Default retention
is 24 hours. Do not promise legal/privacy/store readiness before independent review.

Dependency audit: SDK 58 removed the initial high-severity SDK 55 findings. Five
moderate advisories remain in the Expo CLI/fingerprint dependency chain (glob/minimatch).
These are build tooling findings; do not expose development tooling to untrusted networks.
No zero-vulnerability or completed security-review claim is made.

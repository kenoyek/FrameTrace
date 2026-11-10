# Account and private-storage foundation — 10 November 2026

## Implemented

Supabase asymmetric JWT verification validates signature, issuer, authenticated audience,
expiry, issued-at time, user UUID and role. Only ES256/RS256 are accepted; legacy HS256 and
service-role tokens are not user sessions. JWKS comes only from the configured project URL,
with a 300s cache and a 30s refresh/failure cooldown to bound unknown-kid fetches. Requests
fail closed if verification is unavailable. An account-owned job requires its owner's JWT;
its old per-job capability cannot bypass ownership.

Authenticated uploads create private history. The API supports paginated history, favorites,
individual deletion and batched clear-history. A guest result can be explicitly claimed
only with both a valid user session and its original job capability. Idempotency tokens do
not transfer jobs across identities. All /v1 responses carry Cache-Control: no-store.

The native account screen adds email/password sign-in, signup with confirmation guidance,
sign-out, paginated history, favorites, result reopening, explicit guest claiming and deletion.
Supabase sessions use native SecureStore chunks with atomic generation replacement and
serialized updates; refresh follows app state. Account switches clear the query cache.
Guest recognition remains available when account configuration is absent.

Query storage is replaceable: existing local private files or an S3-compatible backend for
R2. The server validates/bounds uploads before storing them; workers materialize private
objects into temporary files, enforce original size and SHA-256 integrity, then decode.
Object keys are opaque server-generated IDs. No public ACL, media URL, arbitrary URL fetch,
client secret or fabricated watch link is introduced. A deletion outbox survives job removal
and retries failed deletes; maintenance reconciles terminal/orphaned tracked objects.
Hard-killed worker scratch files receive a retention sweep, with live leases protected.

Raw clip retention remains 24h by default. Account metadata remains for 30 days by default;
saved results remain until deleted. Saved metadata never extends raw clip retention. Guest
metadata still follows the raw retention window. All cleanup is scheduled/batched, not a
strict deletion-at-the-second SLA.

## Configuration required for hosted validation

No Supabase project or R2 endpoint/bucket was configured in this environment. No hosted
Supabase/R2 operation or real email/password exchange is claimed. The mobile UI explains
when accounts are unavailable instead of pretending authentication succeeded.

- Backend: FRAMETRACE_SUPABASE_URL, e.g. the exact HTTPS project base URL. Enable asymmetric
  signing keys/JWKS. No service-role key is needed for ordinary recognition/history.
- Mobile: EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY. Only a current
  sb_publishable_ key is accepted; never put a server secret or service-role key here.
- Storage: FRAMETRACE_STORAGE_BACKEND=s3, FRAMETRACE_S3_ENDPOINT_URL (R2 account HTTPS endpoint)
  and FRAMETRACE_S3_BUCKET. Supply usable S3 signing credentials through an approved server
  runtime secret/file/profile binding. Boto3's normal credential chain is preserved. If
  AWS_PROFILE is set, its profile must exist. A generic proxy placeholder cannot compute
  SigV4 signatures. Do not paste credentials into chat, Git, or public Expo variables.
- Permit the project's exact Supabase and R2 hosts in environment settings before testing.
  No domain allowlist, credential binding or environment draft was changed here.
- Keep the R2 bucket private, scope credentials to it, and configure a queries/ prefix
  lifecycle expiration at 24h plus abandoned multipart-upload cleanup. This independent
  safety net is required for failures between remote upload and DB acknowledgement.
  Lifecycle configuration has not been applied or validated against a hosted bucket.
- Configure public-system CA trust for runtime SDK/JWKS calls behind a TLS-inspecting proxy.
  The optional compose.cloud-ca.yaml override mounts a public CA bundle read-only; it does
  not contain secrets or disable verification.

Server requests still accept multipart uploads through FastAPI. Direct client signed
uploads/downloads and remote reference-catalog storage are not implemented in this stage.
Backend DB roles remain server-only; clients use JWT-authorized API routes, not PostgREST.
Apply the additive accounts/storage migration after the prior migrations. RLS denies direct
anon/authenticated reads of all six tables. Hosted migration/policy execution is pending.

## Validation scope

See TESTING.md for commands. Auth tests use real RSA-signed tokens and the actual verifier,
with a controlled public JWKS source. The object-storage tests use a loopback HTTP S3 emulator
(Moto), actual file transfers, FFmpeg extraction, reference retrieval, and deletion. These
are integration tests; they do not establish R2 authorization/TLS/lifecycle compatibility.
Mobile tests simulate native storage/transport; exports are bundles, not device launches.

## Observed check results

- 40 backend tests passed, including real signed JWT verification and S3-emulated clip recognition.
- The 26-test reliability/account suite passed again against disposable PostgreSQL.
- All three SQL migrations applied in order; six tables have RLS and deny both client roles.
- Ten mobile storage/transport boundary tests and strict TypeScript passed.
- SDK native-module manifest compatibility and Android/iOS bundle exports passed.
- The rebuilt Docker API/worker still matched the clean fixture at 4 seconds, rejected
  unrelated footage, and enforced guest ownership/deletion in the live HTTP smoke.
- Python lint/format, OpenAPI consistency, whitespace and optional CA Compose config checks passed.
- npm audit reported zero high/critical findings and the same five moderate transitive
  Expo build-tooling findings. No forced incompatible dependency overrides were applied.
- Existing Starlette/httpx TestClient deprecation warning remains. GitHub CI was not run
  merely because these local commands passed; no signed native builds/devices were tested.

## Remaining gates

Hosted Supabase signup/sign-in/refresh/sign-out and R2 verification, physical device QA,
OAuth/Apple sign-in, password recovery deep links, Supabase identity/account deletion,
notifications and native sharing remain unfinished. Clear history is explicitly not account
identity deletion. JWT validation does not instantly revoke an already issued access token
on logout or user deletion; use short token lifetimes and implement revocation/session checks
before production. Off-device object deletion can be delayed by provider outages. No public
service, signed native binary, production deployment or environment publication is claimed.

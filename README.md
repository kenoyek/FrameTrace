# FrameTrace

**Every clip has a story. Find its source.**

Native mobile video-source discovery, starting with a real controlled-catalog visual
recognition pipeline. This is an early development foundation, not a production release
or an internet-wide recognition service.

Implemented: reference ingestion with rights metadata, FFmpeg validation and sampled
frames, dHash fingerprints, temporal sequence alignment, ambiguity/no-match handling,
FastAPI upload/status/deletion, Redis/Celery workers, PostgreSQL persistence, a native
Expo gallery/preview/upload/result flow, and deterministic media integration tests.

The reliability phase adds durable dispatch/recovery, worker leases, idempotent mobile
retries, request limits and scheduled cleanup. See [the phase report](docs/PHASE_2_RELIABILITY.md).

Start with [DEVELOPMENT.md](DEVELOPMENT.md). See [the implementation plan](docs/IMPLEMENTATION_PLAN.md),
[status and limitations](KNOWN_LIMITATIONS.md), and the [original specification](docs/PRODUCT_SPEC.md).

The account/storage phase adds JWT-owned history, favorites, native account screens and
R2-compatible private query storage. Hosted configuration is still required; see
[the account/storage report](docs/PHASE_3_ACCOUNTS_STORAGE.md).

Native share intake is now implemented in source with an iOS App Group extension and
Android URI copying. Native build/device validation remains open; see
[the share phase report](docs/PHASE_4_NATIVE_SHARING.md).

## Quick local run

```sh
python3 -m venv .venv
.venv/bin/pip install -r services/api/requirements-dev.lock
.venv/bin/pip install --no-deps -e services/api
# FFmpeg and FFprobe must be on PATH.
FRAMETRACE_EXECUTION=local .venv/bin/uvicorn frametrace.app:app --host 127.0.0.1 --port 8000
```

Local mode uses SQLite and a background task in the API process; use the documented
Docker workflow for an independent queue/worker. Nothing returns a match until reference
media has been ingested. Generated fixture instructions are in DEVELOPMENT.md.

```sh
.venv/bin/pytest services/api/tests -q
cd apps/mobile
npm ci
npm run typecheck
npx expo start --dev-client
```

Android/iOS development builds and a device-reachable API address are required for native
validation. No public consumer website is included. No service credentials are embedded.

System-camera recording with explicit preview/upload confirmation: [phase 5](docs/PHASE_5_RECORDING.md). Physical-device acceptance remains pending.

First-run introduction and clip privacy guide: [phase 6](docs/PHASE_6_ONBOARDING.md). Device/accessibility acceptance remains pending.

Persisted app-wide appearance and Settings: [phase 7](docs/PHASE_7_SETTINGS.md). Device/accessibility acceptance remains pending.

Optional private result feedback: [phase 8](docs/PHASE_8_FEEDBACK.md), including its additive database migration.

Local catalog and feedback review commands with catalog change records: [phase 9](docs/PHASE_9_OPERATOR_REVIEW.md). Ingest/revoke now require an operator label; revoke also requires a reason.

Local PostgreSQL migration and privacy-boundary evidence: [phase 10](docs/PHASE_10_POSTGRES_VALIDATION.md). Hosted rollout remains pending.

Android test APK build/download instructions: [phase 11](docs/PHASE_11_ANDROID_TEST_APK.md). A successful verified artifact is required before phone testing; no APK has been produced here yet.

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

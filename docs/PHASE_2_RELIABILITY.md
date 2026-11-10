# Backend reliability phase — 10 November 2026

## Changes

- A durable `recognition_execution` outbox record is committed with each job and its file
  hash. Redis publication is best-effort; broker outages no longer discard accepted clips.
- Celery Beat triggers dispatch/recovery every 15 seconds and retention cleanup hourly.
  Redis has an append-only persistent volume. Exactly one Beat process should run per stack.
- Atomic database claims, 120-second leases and owner fencing protect against concurrent,
  duplicate and stale deliveries. Celery tasks acknowledge late, reject lost workers and
  have a 90-second hard limit. Three processing attempts are allowed. Invalid media fails
  permanently; transient processing errors retain the clip for retry. Missing files and
  exhausted retries produce a terminal, recoverable user-facing error.
- Pre-parser middleware enforces a bounded total request spool (file limit plus 128 KiB),
  including chunked bodies, before multipart parsing. Four uploads per API process are
  admitted; excess requests receive 429/Retry-After. File-specific limits still apply.
- Optional secret X-Submission-Token provides submission idempotency and serves as the
  job bearer capability. Only its hash is stored. Same token/bytes return the same ID and
  actual stage; different bytes return 409. Deletion/expiry ends the idempotency window.
- Expo Crypto creates 256-bit submission tokens; SecureStore persists a pending submission
  before network activity. A response-lost retry reuses the capability. Restoring a pending
  local URI requires an explicit Identify action; no automatic upload occurs.
- An additive migration creates the execution table, backfills existing jobs, enables RLS
  and denies direct client-role access. Local development initialization performs an
  idempotent, conflict-safe backfill without replacing prior access hashes or results.

## Evidence

- 21 backend tests passed on SQLite, including actual FFmpeg decoding and temporal matching.
- The 11-test reliability suite also passed in a disposable PostgreSQL database, including
  concurrent submissions/claims, fencing, retention and legacy job backfill.
- Both SQL migrations applied in order to a fresh disposable PostgreSQL database. RLS was
  enabled on four tables; anon and authenticated roles were denied direct reads.
- Four mobile API-boundary tests passed with explicitly simulated storage/transport:
  response loss and retry, different-clip tokens, storage failure, and server rejection.
- Strict TypeScript, SDK manifest compatibility check, Android and iOS bundle exports passed.
  Offline compatibility checking does not establish online library-directory validation.
- Live HTTP smoke passed against PostgreSQL, Redis and a real independent Celery worker:
  fixture matched at 4 seconds, unrelated footage returned no_match, ownership/deletion held.
- Live Redis outage exercise passed: stopped the local scheduler/worker/broker, accepted
  and replayed one real clip while offline, restored services, and observed scheduler
  recovery and a real match at 4 seconds. No raw token was logged by the test.
- Python lint/format and tracked whitespace checks passed. An existing upstream
  Starlette TestClient/httpx deprecation warning remains.

The lease-expiry/duplicate-delivery paths are tested at the database/task boundary; no
physical host-loss/disaster-recovery or full load test is claimed. Scheduler cleanup logic
is covered without waiting a wall-clock hour. The native exports are bundles, not signed
binaries, native launches or physical-device tests. GitHub CI execution is not implied.

## Operations and remaining work

Start `docker compose up -d --wait api worker scheduler` with database/Redis dependencies.
Read DEVELOPMENT.md before running the explicitly disruptive local outage test. Preserve
both database and media volumes. Recovery needs the scheduler, broker and worker running;
DB/media loss cannot be repaired by redispatch. Keep hosts synchronized and lease duration
longer than the hard task limit. Local BackgroundTasks mode has no automatic scheduler.

Cleanup processes at most 1000 expired records per hourly sweep and skips live leases;
retention is a target with scheduling/batch delay, not a strict second-level deletion SLA.
Admission is per process, not a distributed tenant quota. Decoder sandboxing, Supabase
sessions, R2 signed storage, physical-device QA, native sharing and production monitoring
remain open. A cached local video URI may become unavailable before a retry.

No environment configuration draft was changed or published in this phase. No hosted
resources, paid services, store submissions or production deployments were created.

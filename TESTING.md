# Validation

## Commands

```sh
.venv/bin/ruff check services/api scripts packages/evaluation
.venv/bin/ruff format --check services/api scripts packages/evaluation
.venv/bin/pytest services/api/tests -q
.venv/bin/python scripts/make_fixtures.py var/fixtures
.venv/bin/python packages/evaluation/benchmark.py var/fixtures --output var/benchmark.json
# After Compose startup and fixture ingestion (DEVELOPMENT.md):
.venv/bin/python scripts/smoke_api.py
cd apps/mobile
npm run typecheck
npm test
EXPO_OFFLINE=1 npx expo install --check
EXPO_OFFLINE=1 npx expo export --platform android --platform ios
```

Backend tests generate and decode actual MP4 videos. They verify matching offset,
unknown rejection, out-of-order rejection, duplicate/repeated-shot ambiguity, static
rejection, unauthorized job access, revocation of saved results, result deletion,
size limits, malformed containers and duration limits. TestClient runs the local executor;
the separate smoke test exercises real HTTP, PostgreSQL, Redis and an independent worker.

Development benchmark output is committed in docs/benchmark-development.json. Four edited
positive cases and one negative are too small to support accuracy or latency SLO claims.
Crop rejection is a known matcher limitation, not a passing robustness scenario. There is
no real-world holdout dataset yet. No audio exists in these fixtures; do not claim audio
recognition, muted/replaced-audio robustness or multilingual evaluation.

The installed Starlette emits a TestClient/httpx deprecation warning; all tests still
execute. Mobile checks establish source/bundle compilation, not native device behavior.
RNTL/Maestro, physical-device tests, hosted RLS, R2, cloud concurrency/load, destructive media,
signed builds and store readiness have not been validated. CI is checked in but has not
run on GitHub merely because local commands passed.

The current stage's observed results are in docs/VALIDATION_REPORT.md. To check the SQL
migration locally, with Compose PostgreSQL running, use `.venv/bin/python scripts/check_migration.py`.
It creates and drops its own uniquely named database, leaving the application database
untouched. It needs local operator database/role privileges; never point it at production.

## Reliability phase

`test_reliability.py` exercises concurrent token submissions and lease claims, duplicate
delivery preservation, expired owner fencing, dispatch cooldown, attempt exhaustion,
transient retry, active-lease retention protection, orphan removal, chunked request caps
and admission responses. Run `.venv/bin/python scripts/check_postgres_reliability.py` to
repeat this suite in a new disposable local PostgreSQL database (not the app database).
Both this script and the SQL migration checker require local database creation privileges.

`npm test` runs four Node tests of the actual TypeScript API module with simulated native
storage/transport boundaries: response loss/retry, different clip tokens, storage failure
and server rejection. These do not replace native device or real recognition tests.

The explicit `scripts/smoke_recovery.py --exercise-outage` check stops only the local
Compose Redis/worker/scheduler, retains an upload during the outage and verifies recovery
through real HTTP/FFmpeg/Celery. Run only when local service interruption is acceptable.

## Account/storage phase

`test_accounts.py` exercises real signed JWT verification, wrong claims/signatures, unknown
key refresh bounds, cross-user history/favorites/deletion, explicit guest claiming, session
verification outage, account-scoped idempotency and metadata retention. The PostgreSQL
checker now repeats both reliability and account suites in a disposable database.

`test_storage.py` starts an explicit loopback Moto HTTP S3 emulator with synthetic credentials.
It performs real upload/download/FFmpeg recognition/deletion, checks private ACLs, rejects
modified object bytes, and retries/reconciles remote deletions. It does not test R2 network
permissions or real S3 authentication. Moto and its server dependencies are dev-only.

Mobile tests cover JWT/capability routing across account changes and large Unicode secure
session storage, interrupted writes and logout. Hosted identity flows and physical devices
remain separate required gates. Run `pytest services/api/tests -q`, the PostgreSQL/migration
checkers, `npm test`, strict type checking and native bundle exports before reviewing changes.

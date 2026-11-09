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

# Development validation — 9 November 2026

This report covers the first implementation stage, not completion of the full product.

- Python 3.12.14, Node 24.22.1, Expo 58.0.23 / React Native 0.88.1.
- Backend pytest: 10 tests passed (one upstream TestClient/httpx deprecation warning).
- Ruff lint and format checks passed.
- Docker image built with TLS/signature verification intact and a non-root runtime.
- PostgreSQL and Redis health checks passed; API database health passed.
- Full HTTP/Celery smoke: generated six-second excerpt matched at 4.0s; unrelated video
  returned no_match. Capability ownership, deletion and inaccessible deleted result passed.
- Initial SQL migration applied to a fresh disposable local PostgreSQL database. RLS was
  enabled on all three tables; anon and authenticated roles were denied direct reads.
  This does not establish hosted Supabase/Auth policy behavior.
- TypeScript passed. Installed Expo SDK native-module manifest compatibility check passed
  in offline mode; the online Expo/React Native Directory check was blocked by network policy.
- Both Android and iOS Metro/Hermes bundles exported successfully. No native app was installed
  or launched. This Linux environment has no adb, Android emulator, or Xcode executable.
- The reusable setup script was executed successfully after the initial installation.
- npm production-tree audit after upgrading to SDK 58: 0 critical, 0 high, 5 moderate
  findings inherited through Expo CLI/fingerprint glob/minimatch tooling. No forced
  incompatible major dependency overrides were applied. Recheck advisories before release.
- Deterministic five-case benchmark: clean, recompressed/downscaled and caption-bar queries
  matched; cropped query failed; unrelated footage rejected. 3/4 positive retrieval, 1/1
  negative rejection. P50 ~0.139s and P95 ~0.172s for this tiny local fixture run only.
  Extraction/matching timing excludes mobile upload and queue delay. No SLO/accuracy claim.
- No external catalog was downloaded; generated footage has no fabricated watch link.
- No production deployments, purchases, signed native builds or GitHub CI runs performed.

## Configuration persistence

The cloud draft read repeatedly failed verification. The save attempt for install_script
and start_skill returned INVALID_ARGUMENT: saving could not be confirmed. No successful
save or publication is claimed. Repository instructions and scripts remain available at
DEVELOPMENT.md and scripts/setup.sh. The running Docker processes were actually validated;
they must be restarted in a future machine. Future-task snapshot restoration is untested.

## Remaining acceptance gate

Use an Android development build and then an iOS build on real devices to select a fixture,
upload it to the real worker, and confirm title/offset and unknown handling. EAS project,
signing/provisioning, a device-accessible backend and actual devices are still required.
Continue cloud auth/storage, richer recognition and native sharing per IMPLEMENTATION_PLAN.md.

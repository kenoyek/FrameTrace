# Implementation plan and acceptance gates

The full product specification is preserved in PRODUCT_SPEC.md. This repository starts empty.
Work proceeds in dependency order; a checked-in scaffold is not a completed integration.

1. **Discovery and executable foundation:** Python 3.12, Expo SDK 58 / React Native 0.88,
   FastAPI, SQLAlchemy, PostgreSQL, Redis/Celery, FFmpeg, OpenCV. Pass decoder and sequence
   tests, run the API and worker, retain frozen dependency resolutions.
2. **Controlled-catalog retrieval:** original synthetic footage, rights metadata, timestamped
   dHash index, constant-offset temporal verification, conservative ambiguity/rejection,
   CLI ingestion/revocation and measured evaluation. Gate: actual extracted excerpt at
   a known offset plus unknown video through an independent worker.
3. **Mobile vertical slice:** native picker, preview, consent before upload, progress,
   persistent capability token, real polling, evidence and no-match rendering. Gate:
   strict TypeScript and native bundle export; separately test on Android and iOS devices.
4. **Secure cloud integration:** Supabase JWT ownership and history, R2 signed uploads,
   bounded streaming ingress, quotas/rate limits, isolated workers, migrations, cleanup
   scheduling, queue recovery/idempotency and observability. Requires service configuration.
5. **Recognition expansion:** lawful diverse reference and holdout sets, audio, OCR,
   speech and embedding providers, scene segmentation and indexed retrieval. Gate:
   benchmark edit classes, negative confusers, repeated shots and timestamp uncertainty.
6. **Native sharing and full product:** Android content URI import; iOS extension with
   App Groups and development builds; trim UI, accounts, notifications, saved history,
   onboarding, restricted admin operations. Gate: foreground/cold-start device matrix.
7. **Release hardening:** adversarial media/security/load tests, privacy and rights review,
   monitoring, accessibility audit, store assets, signed Android/iOS builds and private beta.

## Important decisions and risks

- Start with visual retrieval. dHash is cheap and inspectable but brittle under cropping,
  text overlays, speed edits and mirrored footage. Semantic similarity alone cannot confirm origin.
- Keep alternate alignments when repeated shots/copies compete. Scores are not probabilities.
- Source URLs are optional, operator-supplied and must be independently verified; fixture
  recordings have no fabricated external source link. Publisher identity is not verified ownership.
- The local API uses per-job random bearer capabilities, hashed at rest; these are guest
  possession credentials, not Supabase accounts. Do not expose this development API publicly.
- JSON fingerprints and exhaustive retrieval suit a tiny catalog only. No scalable-index claim.
- Local `create_all` bootstraps the development schema. The explicit SQL migration is for
  fresh Supabase development databases and requires separate policy validation.
- Synthetic fixtures establish plumbing only, not performance on movies/social media.
- Apple signing, EAS credentials, real devices, authorized catalog assets and cloud resources
  remain external prerequisites. Do not buy services, deploy or publish without authorization.

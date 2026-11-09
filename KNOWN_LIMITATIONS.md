# Implementation status

## Implemented foundation

- [x] Monorepo layout, preserved product specification and phased acceptance gates
- [x] Authorized catalog operator CLI with content hash IDs, rights assertions and revocation
- [x] Real FFprobe/FFmpeg sampling and OpenCV perceptual fingerprint extraction
- [x] Constant-offset temporal verification, ambiguous matches and unknown rejection
- [x] Private guest jobs, actual worker stages, polling, cleanup and terminal-result deletion
- [x] PostgreSQL / Redis / Celery Compose workflow and independent-worker smoke test
- [x] Native Expo picker, preview, consent/upload progress, result/evidence/no-match display
- [x] Secure latest-job persistence and system/manual light/dark themes
- [x] Frozen dependencies, tests, deterministic evaluation and source/bundle CI configuration
- [x] Initial Supabase SQL migration (hosted application/policy validation still pending)

## Remaining product gates

- [ ] Demonstrate physical Android and iOS upload-to-result milestone
- [ ] Signed EAS development/release builds and native integration tests
- [ ] Native Android sharing and iOS App Group share extension
- [ ] Timeline trimming and recording
- [ ] Real-world authorized catalog and untouched evaluation holdout
- [ ] Scene segmentation, robust cropped/vertical/watermarked/speed-edited retrieval
- [ ] Audio fingerprints, transcripts, OCR, embeddings and vector search
- [ ] Supabase sessions/OAuth/accounts, private history/favorites and account deletion
- [ ] R2 private objects and signed upload/download, durable job recovery/idempotency
- [ ] Admission/rate limits, per-job decoder sandbox, retention scheduler and production metrics
- [ ] Restricted admin console, audit logs, feedback and catalog removal workflows
- [ ] Push notifications, analytics, onboarding and full settings/profile flows
- [ ] Accessibility/device QA, licensed branding assets, privacy review and store release

Cropped synthetic footage currently fails matching. No numeric score is displayed as a
probability. No original creator is inferred. Source links are optional operator assertions.
The reference catalog is tiny, JSON-backed and scanned exhaustively. The service binds to
loopback because it is not hardened for public traffic. No external cloud resources or
paid APIs have been provisioned and no production system was changed.

The current npm audit also reports five moderate transitive build-tooling advisories;
no high or critical production-tree findings were reported in this run.

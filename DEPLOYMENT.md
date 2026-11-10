# Deployment

Compose is for local development only. No hosted service has been deployed. Docker images
run as a non-root user; query media and the database persist in named local volumes.
Use the system CA BuildKit secret behind the managed proxy; never disable TLS verification.

Before staging: provision private PostgreSQL/Supabase and R2; authenticate users; define RLS;
apply reviewed migrations; implement signed storage and distributed upload quotas; add
network/tenant quotas; sandbox media decoders; operate/monitor the cleanup and recovery scheduler; test
interrupted-job recovery at deployment scale; configure structured telemetry/Sentry/OpenTelemetry and secrets rotation. Separate
staging and production resources. Perform load, security, backup/restore and failure tests.

Deployment and purchases require explicit authorization. No deployment credentials are
needed for the current local recognition acceptance gate. CI validates backend and mobile
source/bundles but does not publish containers or applications.

The account/private-query-storage adapter is now implemented. Activation and hosted
validation requirements are in docs/PHASE_3_ACCOUNTS_STORAGE.md. In particular, configure
asymmetric project signing, server-only S3 signing credentials, exact egress destinations,
runtime CA trust, private bucket access and independent lifecycle expiration before using
real user media. Do not treat passing emulated S3 tests as a hosted deployment check.

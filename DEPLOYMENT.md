# Deployment

Compose is for local development only. No hosted service has been deployed. Docker images
run as a non-root user; query media and the database persist in named local volumes.
Use the system CA BuildKit secret behind the managed proxy; never disable TLS verification.

Before staging: provision private PostgreSQL/Supabase and R2; authenticate users; define RLS;
apply reviewed migrations; implement signed storage and streaming upload limits; add
network/tenant quotas; sandbox media decoders; schedule cleanup; ensure interrupted jobs
recover; configure structured telemetry/Sentry/OpenTelemetry and secrets rotation. Separate
staging and production resources. Perform load, security, backup/restore and failure tests.

Deployment and purchases require explicit authorization. No deployment credentials are
needed for the current local recognition acceptance gate. CI validates backend and mobile
source/bundles but does not publish containers or applications.

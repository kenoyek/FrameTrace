# In-app test API connection check — 18 November 2026

Settings now offers an explicit Check connection action for the API address embedded in
the build. This helps distinguish local UI testing from recognition readiness once an
APK is available. It does not allow changing the server at runtime or require sign-in.

The probe makes GET /health under the configured API prefix, with no clip, guest capability,
account Authorization header or request body. It requests no cookies, redirects or cache,
and uses an eight-second abort timeout. The button prevents overlapping probes, and
unmount aborts an outstanding request. No request is sent for missing/invalid configuration.
HTTP/HTTPS base URLs must exclude credentials/query/fragment. The UI never displays server
error payloads or stores the diagnostic result. Network access still reveals normal
connection metadata to the configured API; this is not an anonymous connection mechanism.

States explain absent/invalid configuration, unreachable/unhealthy service, incompatible
health responses and a responding FrameTrace API/database. Success requires status=ok and
an execution mode of local or celery. It does not verify worker liveness, catalog coverage,
account-provider readiness, upload processing or matching quality. A healthy snapshot can
become stale immediately; it is not a release-readiness certification.

## Evidence and acceptance limits

All 38 mobile tests and strict TypeScript passed. Six new transport cases cover invalid
configuration without requests, prefix preservation/no credentials, nonhealthy/unrelated
responses, safe error messages, timeout abort, and caller cancellation. Tests simulate
transport; no live phone/API connection is claimed. Android and iOS JavaScript bundles
exported successfully. No native code, SDK dependency or backend behavior changed.

GitHub Actions status retrieval remains Forbidden from this cloud environment. No remote
APK workflow success or downloadable APK is confirmed. The phase 11 build path and phase
12 diagnostics still apply; existing native-build/device and security gates remain open.

On a test phone: open Settings and check with no API configured; then rebuild against a
reachable HTTPS test API. Verify a healthy response, airplane mode, an unavailable server,
wrong base path, timeout/retry and leaving the screen during a request. Confirm no clip or
auth token accompanies the probe. Next use an authorized fixture through Identify to test
the real upload/worker path. Check large text and screen-reader result announcements.

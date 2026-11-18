# Android test APK delivery — 18 November 2026

The current cloud environment still denies CONNECT to repo.reactnative.dev with HTTP
403, confirmed against React Native 0.88.1's actual AAR URL. Its observed network policy
is enforced/restricted and has no custom domain grants. GitHub Actions API requests from
this environment also return Forbidden. No allowlist, environment draft or publication
was changed. **No APK has been produced or installed in this phase.**

## Build and download

The Android test APK workflow runs on relevant pushes to main and supports manual runs:
https://github.com/kenoyek/FrameTrace/actions/workflows/android-test-apk.yml

After a green build, open that run and download its FrameTrace artifact. Unzip it to get
the APK, SHA256SUMS and build-info.json. Artifacts expire after 14 days. A failed run does
not produce a usable artifact. A workflow push/parsed YAML is not native-build evidence;
this environment cannot currently query the run's status through GitHub's API.

Use **internal-preview** (the default) for initial phone testing without Metro. It uses
the native release variant with Expo's generated Android Debug signing key and embeds
JavaScript. This is a development-signed internal test APK, not a production-signed/store
release and not a debuggable build. The **debug** option produces a genuinely debuggable
APK using the development client; run Metro (`npm start` in apps/mobile) on a reachable
computer. Both target ARM64 phones, not x86 emulators. Build artifacts from either option
have the same application ID; installing can replace a compatible existing build. Back up
needed test data first; a signing mismatch requires removing the prior test install.

The workflow runs mobile tests/typecheck, prebuilds native Android, installs the exact SDK
components, uses full JDK 17 and verified Gradle distribution integrity, and invokes the
same local build helper. It verifies APK ZIP integrity, manifest/bytecode, ARM64 libraries,
application ID, apksigner signature and development certificate. Internal previews must
contain assets/index.android.bundle and must not be debuggable; debug APKs must be
debuggable. Checksums and source revision are recorded. Verification is a prerequisite
to artifact upload, not proof of launch or successful recognition.

## API and testing readiness

Set repository Actions variable EXPO_PUBLIC_API_URL, or supply the manual workflow's
api_url input, to a reachable HTTPS development API before building for recognition tests.
The URL must have no credentials/query/fragment. Optional Supabase URL/publishable-key
repository variables enable account testing. These public settings are embedded in the
app; never use service-role credentials. A build without an API URL can test local UI,
appearance, onboarding, camera and share intake, but Identify will explain that the API
is unconfigured. A localhost API on the build machine is not reachable from your phone.

It is reasonable to begin **private smoke testing once a verified APK artifact exists**:
install on a compatible test phone, launch, check onboarding/navigation, record/pick/share
a permitted clip, review without uploading, and verify no crash. With a reachable test
backend/catalog, Identify should return the real fixture result. Follow MOBILE_RELEASE.md
for the full permission, lifecycle, account and deletion matrix. Do not call it accepted
until the phone flow actually passes. The existing dependency advisory remains an open
release gate; initial trusted private testing is not store/public beta approval.

There is no reliable completion time yet: a hosted runner still has to resolve native
dependencies and compile the custom Kotlin module. The first failed native check must be
fixed before delivery. Alternatively allow repo.reactnative.dev in this cloud environment
and retry locally. Other newly encountered dependencies or compilation errors may remain.

## Local commands and checks

```sh
cd apps/mobile
EXPO_OFFLINE=1 npx expo prebuild --platform android --no-install
cd ../..
.venv/bin/python scripts/build_android.py --variant internal-preview
.venv/bin/python scripts/verify_android_apk.py apps/mobile/android/app/build/outputs/apk/release/app-release.apk --variant internal-preview --build-tools /workspace/.cache/android-sdk/build-tools/37.0.0 --output /tmp/frametrace-build-info.json
```

The bundled local Gradle build was actually attempted: 89 tasks executed, then React
Native 0.88.1 release AAR retrieval from repo.reactnative.dev returned HTTP 403. No
native app compilation/signature/installation success is implied.

The complete backend suite passed 61 tests, with one PostgreSQL-only case skipped.
Six ZIP-policy tests passed. They use unit-test ZIP files, not fabricated installable APKs;
actual signature/Android tooling checks require a real successful build. Python lint/format,
workflow YAML parsing and diff checks passed. No remote Actions success, native compiler
success, APK signature verification or physical-device launch is claimed here.

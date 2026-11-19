# Android test APK — verified 19 November 2026

A real ARM64 internal-preview APK was built locally with `assembleRelease`: BUILD
SUCCESSFUL in 6m 11s, 821 actionable tasks. The native FrameTrace share module compiled.
The file is development-signed and embeds its JavaScript, so it does not require Metro.
It is not a production-signed/store release or a debuggable variant.

Artifact delivered in this chat: `/workspace/artifacts/FrameTrace-test-arm64.apk` (about
32 MiB). Build metadata and SHA256SUMS are in the same directory. APKs are not committed
to Git. Source revision: 1cf92d78b66284cde004e4d68bdf1b10b8bf70ed.

SHA256: `2e50529569d15674d5762b331bf077573cb535763b7912c18fd076b1e3eef8d2`

The verifier checked ZIP integrity, Android manifest/DEX, ARM64 libraries, application ID
app.frametrace.mobile, valid Android Debug signature, embedded JavaScript and the expected
non-debuggable preview variant. No emulator/physical-device installation, launch or flow
acceptance is claimed.

**No recognition API URL is configured in this artifact.** Use it for initial onboarding,
appearance, camera, gallery and share-intake smoke tests. Recognition requires rebuilding
with a reachable EXPO_PUBLIC_API_URL and a configured test backend/catalog. Accounts are
also unavailable without their public Supabase configuration. Existing security advisory,
iOS build, privacy/accessibility review and broader release gates remain open.

Build repair: Expo telemetry attempted to write /home/agent/.expo, which is unavailable in
this managed workspace. The build helper now disables telemetry for its child process.
The published network grants worked; no environment settings were modified here.
The hosted APK workflow's last observed failure was its setup-android action. It now uses
the SDK already provided by a pinned Ubuntu 24.04 runner. YAML validation passed; this
local success does not claim that the revised hosted workflow has completed.

Install the APK on a compatible ARM64 Android test phone, allow installation from the
chosen download source when prompted, then test the MOBILE_RELEASE.md acceptance matrix.
A different signing certificate on an existing FrameTrace installation may require
uninstalling it first, which removes its local data. Keep important test data separately.

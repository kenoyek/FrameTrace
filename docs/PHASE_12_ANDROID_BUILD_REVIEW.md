# Android share-intent fix and build diagnostics — 18 November 2026

Review found a real Android intent-lifetime defect: capture cleared `intent.data` before
its executor later read `intent.type`. Android Intent.setData clears the MIME type, so a
valid shared video could be rejected. Capture now snapshots the declared MIME alongside
the action/read grant before clearing the external intent, and uses that immutable value
on the copy executor. URI, grant, bounded-copy and backend-validation rules remain in place.
This is a source correction; no device lifecycle or Kotlin compiler success is claimed.

The native-project verifier now supports `--android-only`. It checks the generated share
filters and camera/microphone permissions without requiring an iOS project. The test-APK
workflow runs it immediately after Android prebuild. The existing full verifier continues
to check iOS target/source membership, embedding, dependencies and App Groups too.

GitHub Actions now preserves Gradle output in a diagnostic artifact if the native build
fails, along with available Gradle problem reports. These expire after seven days and
remain separate from installable APK artifacts. The final job summary reports whether a
verified artifact was uploaded; a diagnostic ZIP is not an APK. Console output is still
available for failures before Gradle starts. Source/typecheck tests run before compilation.

## Verification and remaining APK gate

- Strict TypeScript and all 32 mobile tests passed. These do not run Android Intent code.
- Android-only and full generated-project checks passed against the existing prebuilt
  projects. No config plugin, permission declaration or native SDK version changed.
- Workflow YAML parsed, Python lint/format and diff checks passed.
- A fresh request to the actual React Native 0.88.1 release AAR still failed proxy CONNECT
  with HTTP 403. The known download block persists; unchanged Gradle dependency resolution
  was not rerun. GitHub Actions status retrieval also returned Forbidden at api.github.com.
- No APK was produced, signature-verified, installed or device-tested here. No native
  build/remote workflow success or completion time is claimed. JS bundles and backend
  tests were not rerun because those implementations were unchanged.

The build workflow will run on this relevant main-branch push. Follow its status at
https://github.com/kenoyek/FrameTrace/actions/workflows/android-test-apk.yml . A green
verified APK artifact is the first private phone-testing milestone. Internal preview
needs no Metro; debug requires Metro. Recognition also needs a reachable configured test
API. See PHASE_11_ANDROID_TEST_APK.md and MOBILE_RELEASE.md for download/testing steps.
The artifact still needs launch, gallery/camera/share, permission and lifecycle acceptance.
Existing dependency-security and production-release gates remain open.

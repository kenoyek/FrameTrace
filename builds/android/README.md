# FrameTrace Android test APK

Download FrameTrace-test-arm64.apk from this directory using GitHub's Download raw file
button. This is a verified development-signed ARM64 internal-preview build. It includes
JavaScript and does not need Metro. Physical-device acceptance is still pending.

No recognition API URL is configured. Use this build for initial onboarding, appearance,
camera, gallery and share-intake checks. Recognition needs a new build configured with a
reachable test API. This is not a production/store release.

SHA256: 2e50529569d15674d5762b331bf077573cb535763b7912c18fd076b1e3eef8d2

The source revision and verification scope are in build-info.json. From the repository
root, verify the download using `sha256sum -c builds/android/SHA256SUMS`.

A different signing certificate on an existing FrameTrace installation can require
uninstalling it first, removing its local data. Keep any needed test data separately.

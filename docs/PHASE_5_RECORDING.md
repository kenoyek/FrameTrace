# System-camera recording foundation — 18 November 2026

The mobile home screen now offers Record a short video. Camera access is requested only
on that action. Android explicitly requests microphone permission; iOS uses its native
camera permission flow and the configured microphone purpose string. Denial explains
Settings/gallery alternatives. Cancellation preserves the existing selection.

The system camera is configured for video, a 30-second maximum and medium iOS quality.
OS enforcement and output encoding vary. Returned assets go through the same early
validation as gallery selections: local URI, video type, finite duration/size when supplied,
1–30 seconds, 50 MiB and a 4K pixel cap. Missing optional duration/size metadata is left to
backend probing. This is not a transcoder or trimming implementation.

The recording opens a local preview. Only Identify uploads it. A synchronous selection
gate prevents concurrent camera/picker launches and blocks upload or replacement while a
selection is pending. Replacing a selection clears its old interrupted-submission entry
and releases a previous native shared copy. Recordings stay in the OS-managed picker
cache; no claim of immediate secure erasure is made.

## Validation and remaining gates

- Strict TypeScript and 21 mobile tests pass, including five capture/preflight cases.
- Expo prebuild and generated native configuration checks cover camera/microphone purpose
  strings and Android permissions, alongside the share extension structure.
- Android/iOS JavaScript bundle exports are checked separately from native compilation.
- No physical-camera, microphone, playback or device-lifecycle acceptance is claimed.
  MOBILE_RELEASE.md records the unexecuted matrix. Native rebuild is needed for permissions.
- Prior native-build and security gates remain: repo.reactnative.dev network access,
  iOS signing/macOS tooling, and the unpatched Picomatch advisory described in SECURITY.md.
- No environment configuration, deployment or publication is part of this phase.

# Mobile build and device gate

Expo SDK 58, React 19.3, React Native 0.88.1. EAS configuration includes development,
internal preview and production profiles. Native bundle export checks compilation only.
No signed APK/AAB/IPA, TestFlight build or store submission exists yet.

Android-first validation: configure an EAS project and owned package identifier, produce a
development build, point it at a trusted device-accessible API, import the generated clean
fixture through the system picker, preview it and confirm upload. Check the real reference
and four-second timestamp; also unknown, offline, malformed, interrupted and large clips.
Repeat on iOS with appropriate Apple signing/provisioning. Record device/OS/build IDs.

Android ACTION_SEND intake and a custom native iOS share extension/App Group inbox are
now implemented. See docs/PHASE_4_NATIVE_SHARING.md for the build blocker and validation
limits. Expo Go is not the native-integration acceptance target.

Pending: native build/device acceptance, on-device trimming, physical-device camera capture and onboarding acceptance,
notifications, saved history, native artwork/splash, trademark checks, voice-over/TalkBack,
large-font/reduced-motion audit, data safety labels and store privacy disclosures.

## Share acceptance matrix — required, not yet executed

1. Install a native development build on Android and then iOS. For Android debug, connect
   Metro (`cd apps/mobile && npx expo start --dev-client`); a debug APK is not standalone
   JS distribution. Use the real backend with the authorized generated reference indexed.
2. Put var/fixtures/clean.mp4 on the device. Share from a real system gallery/provider while
   FrameTrace is terminated, foregrounded and backgrounded. On iOS save in the extension,
   finish it, then manually open FrameTrace. Confirm the local review/preview before Identify.
3. Before Identify, verify no POST /v1/recognitions occurred. After confirmation, expect the
   actual reference title and a source timestamp of 4s (±0.5s), not a simulated result.
4. Test another incoming share while uploading, rapid taps, empty/full inbox, discard,
   permission rejection, revoked content URI, provider failure and app termination mid-copy.
5. Test unsupported formats, >50 MiB, >30s, invalid dimensions and multiple-file payloads.
   Verify recovery through gallery selection; no original borrowed URI should be required
   after a successful copy. Caches/partial imports must expire on later app/extension runs.
6. Share HTTPS URLs (including private query tokens), plain text and unsafe schemes. No
   remote download or recognition may occur; the UI offers local selection. Check only the
   hostname is retained for links, and errors do not expose provider URI/query tokens.
7. Test iOS limited extension lifetime, cancellation, large Dynamic Type, phone/tablet safe
   areas, App Group provisioning, warm/cold launch, repeated saves and process termination.
8. Confirm accepted uploads release their local shared copy, interrupted response retries
   reuse their submission token, and restarting the app does not automatically upload.

Record real device/OS/build IDs, exact permissions, API job IDs and observed outcomes.
Passing source checks or bundles does not mark any of these device cases passed.

## Recording acceptance (not executed on devices)

On physical Android/iOS devices, verify first permission approval, denial, permanent denial
and Settings recovery; Android microphone denial; camera unavailable; cancellation with an
existing preview; repeated taps; foreground return; and a 30-second recording. Confirm no
recognition POST occurs until Identify. Check returned video size, rotation/resolution,
audio and preview playback; OS duration limits may vary, so preflight/server validation
must still reject overlong clips. Verify discarding/replacing an interrupted upload clears
its retry entry without automatically uploading a new recording.

First-run and reusable guide acceptance (not executed on devices): see docs/PHASE_6_ONBOARDING.md.

App-wide appearance and Settings device/accessibility acceptance (not executed): see docs/PHASE_7_SETTINGS.md.

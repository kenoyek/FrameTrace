# Native share-intake foundation — 18 November 2026

Native implementations and the consent-first mobile flow are in place. Native build/device
acceptance is **not complete**: Android dependency retrieval is blocked by the environment's
network policy, and iOS requires a macOS/Xcode signing environment.

## Implementation

A local Expo module lives in apps/mobile/modules/frametrace-share. The config plugin adds
Android SEND filters and an iOS native extension target. No third-party receiving-share
plugin was installed. The evaluated expo-share-intent 9.0.0 implementation traverses the
responder chain to call UIApplication and reopen the host; this implementation deliberately
uses a different design with extension-safe APIs and no forced host launch. This is a design
assessment, not an App Review approval or a claim of production platform compliance.

### Android

- Eligible for a single ACTION_SEND video/* or text/plain payload, with singleTask activity.
- Cold/foreground activity hooks capture intents; malformed parcelables are caught.
- Video imports require a content URI and a temporary read grant. Own-app authorities and
  legacy external file:// paths are rejected; gallery selection remains the fallback.
- A bounded copy moves permitted bytes into the app's private cache immediately; the
  borrowed provider URI is not stored in the inbox. No permanent URI grant is requested.
- ISO BMFF signature and native duration/resolution metadata are checked before preview.
- Read/stream/decode errors become recoverable inbox errors without retaining URI details.
- Multiple-file sends are not advertised and are rejected if delivered explicitly.

### iOS

- A plain UIKit extension uses NSItemProvider file representations and App Groups. No React
  runtime, URL downloader, UIApplication traversal or forced app opening runs in it.
- The temporary provider file is copied while its callback owns access. Security-scoped
  access is balanced; private file protection is applied. AVFoundation reads metadata.
- The extension saves a complete payload atomically, then tells the user to open FrameTrace.
  Done completes the extension request. Saving here is local, not a server recognition.
- File coordination reserves shared inbox slots across extension instances. Host-side
  operations run on a serial queue, copy into host cache, then remove the shared copy.
- Both targets get the same App Group entitlement and Info.plist identifier. The extension
  is embedded and is a host build dependency. APPLICATION_EXTENSION_API_ONLY is enabled.
- EAS extension credential metadata is registered; Apple provisioning/identifiers still
  require an owned development team and validation. Existing package IDs remain placeholders.

### Mobile consent and safety

Incoming items show a review banner. Review validates the native payload and opens a local
preview; Identify is the only media-upload action. A busy search is not replaced by an
incoming item. A synchronous upload gate protects against duplicate taps. Users can dismiss
inbox items, discard a preview, or choose another gallery clip. Import shared video also
checks manually, including when iOS split-screen does not deliver a foreground event.

Pending retries retain the native item ID, and accepted jobs retain a local cleanup receipt.
The native copy is released after server acceptance and cleanup is retried when the latest
result is restored. Interrupted cleanup still has the native cache-expiry fallback. This
is not a guarantee that every OS termination point or account-switch lifecycle was tested.

Limits match the current API: 50 MiB, 1–30 seconds, ≤3840×2160 pixels. Android holds at most
three inbox entries; iOS separately limits the extension inbox and host cache to three each.
Fresh entries are not silently evicted. Copies use bounded buffers; the copy deadline is
cooperative between reads, not a hard isolation guarantee against a hung platform provider.
Device caches are pruned after 24h when the app/extension next runs; no background purge
while an app is terminated is claimed. OS cache eviction can make an item unavailable earlier.

Shared HTTPS links are classified locally, with only their hostname retained. Paths, query
tokens and credentials are not persisted. No provider downloader is configured: the app
explains the limitation and offers local video selection. No clip is automatically added
to the reference catalog. None of the intake handlers automatically invokes recognition.

## Checks actually run

- Strict TypeScript and all 16 mobile boundary/policy tests passed.
- Six native JVM policy groups ran against the real Java copy/URL/path implementation:
  exact-limit bytes, oversize rejection, container signature, hostname extraction, unsafe
  schemes/credentials and traversal IDs. These are not Android intent/lifecycle tests.
- Both native projects generated through Expo prebuild. Checks verified a single extension,
  compiled-source group references, host dependency, embedding, matching App Groups/Info,
  activation rules and Android intent filters. These are not Swift compilation checks.
- SDK native-module manifest compatibility check passed in offline mode.
- Android and iOS JavaScript/Hermes bundle exports passed. No signed native binary is implied.
- Build prerequisites were installed in user-owned caches: Android 37.0 platform, build-tools
  37.0.0, NDK 27.1.12297006, CMake 3.22.1 and full Temurin JDK 17.0.21+9. The CLI archive and
  JDK were verified against official checksums; the helper also verifies the Gradle ZIP.
- Android Gradle build ran and resolved/configured the project, including the custom module.
  It failed fetching React Native 0.88.1's debug AAR after Maven Central redirected to
  repo.reactnative.dev; the proxy returned HTTP 403. A direct CONNECT probe was also denied.
  Native Kotlin compilation did not complete. There is no APK artifact to install or share.
- No iOS native compilation, emulator, real-device share flow, store signing or publication
  was performed. The Android device probe also could not initialize its default read-only
  home settings directory; no device-connectivity success is claimed.
- Backend recognition code was unchanged; the earlier live recognition evidence is not
  relabeled as a native share-to-result test. GitHub CI has been updated but not run here.

## Dependency audit release gate

The final `npm audit --omit=dev` reports **34 findings: 32 high, two moderate, zero
critical**. The high findings include inherited Expo/Metro dependencies affected by
[Picomatch repeated-extglob ReDoS](https://github.com/advisories/GHSA-fc5q-39xc-vjpf).
The registry's latest Picomatch version was 4.0.7 and the advisory covers <=4.0.7;
no patched release was available. These counts include dependent packages, not 32
independent flaws. This remains an open release gate.

Compatible audit fixes updated Expo to 58.0.26; Expo's installer then aligned native
package versions. TypeScript, all 16 mobile tests, prebuild, structural native checks,
SDK compatibility and both bundle exports passed again against that final lockfile.
The Gradle attempt preceded these patch updates; React Native remains 0.88.1 and its
required AAR host is still denied. No final-lockfile native compilation is claimed.
No forced SDK downgrade or unsupported dependency override was applied. Use trusted
checkouts and keep development tooling off untrusted networks pending remediation.

## Resume the blocked native build

An environment editor needs to add **repo.reactnative.dev** to the existing HTTP allowlist,
preserving other custom domains and package-manager presets. No settings or draft were
changed by this phase, and nothing was published. After saving access, refresh environment
status and retry with a fresh build process:

```sh
cd /workspace/FrameTrace
.venv/bin/python scripts/build_android.py
```

The helper builds ARM64 debug only. It preserves TLS verification using the inherited
proxy and public CA, reuses user-owned caches, and uses no production signing credentials.
Do not replace the missing artifact with another RN version or disable integrity checks.

On macOS, regenerate/prebuild and build with an owned Apple team. Verify both the host and
app-extension provisioning profiles include the chosen App Group. A native development
build is required; Expo Go cannot receive these native shares. Physical-device acceptance
cases and exact commands are in MOBILE_RELEASE.md and DEVELOPMENT.md.

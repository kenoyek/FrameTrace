# Mobile build and device gate

Expo SDK 58, React 19.3, React Native 0.88.1. EAS configuration includes development,
internal preview and production profiles. Native bundle export checks compilation only.
No signed APK/AAB/IPA, TestFlight build or store submission exists yet.

Android-first validation: configure an EAS project and owned package identifier, produce a
development build, point it at a trusted device-accessible API, import the generated clean
fixture through the system picker, preview it and confirm upload. Check the real reference
and four-second timestamp; also unknown, offline, malformed, interrupted and large clips.
Repeat on iOS with appropriate Apple signing/provisioning. Record device/OS/build IDs.

Next: Android ACTION_SEND with temporary content URI permission copying; iOS native share
extension/App Groups with extension lifecycle tests. No receiving-share library has been
selected or declared reliable. Expo Go is not the native-integration acceptance target.

Pending: on-device trimming, camera capture, share targets, onboarding, account screens,
notifications, saved history, native artwork/splash, trademark checks, voice-over/TalkBack,
large-font/reduced-motion audit, data safety labels and store privacy disclosures.

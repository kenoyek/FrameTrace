# App-wide appearance and settings — 18 November 2026

Settings now provides System, Light and Dark modes, plus entry points to the clip privacy
guide and Account & history. Home links to Settings & appearance instead of maintaining
its own temporary theme controls. A shared provider applies the selection to Home,
accounts, onboarding, guide, Settings, introduction loading UI and status-bar content.

The choice is a device-local SecureStore preference, independent of account sign-in/out.
System mode reacts to OS appearance changes; a missing/invalid stored value uses System.
A null OS appearance falls back to Dark. Startup can initially show the system appearance
while the saved choice loads; the native splash and OS camera are outside this provider.
The app does not claim a flash-free native launch or recolor system camera UI.

Selections take effect immediately. Writes are serialized so slow earlier writes cannot
overwrite a newer choice. Failed writes do not poison the queue. Only the latest selection
reports a save error; a failed save leaves that mode active for this session, with an
explicit message and retry by selecting the mode again. A read failure also explains the
fallback. Mode controls wait for initial loading. No preference is synced to a server,
and changing it does not modify jobs, auth credentials or upload retry entries.

## Checks and remaining acceptance

All 30 mobile tests and strict TypeScript passed. Five new preference tests cover invalid
values and round trips, OS resolution, ordered concurrent writes, failure recovery and
read errors. These are storage/policy tests, not mounted React or device UI tests.
Android and iOS JavaScript bundle exports passed. No native code, permissions,
dependencies or environment settings changed.

Device checks remain: change modes across all screens, restart and verify persistence,
toggle OS appearance in System mode, rapidly switch modes, simulate storage failures,
check sign-out preserves the device choice, and navigate Settings → guide/account → Back.
Test direct Settings entry, large text, VoiceOver/TalkBack radio announcements, status bar
contrast, and small/tablet screens. No accessibility audit or native-device acceptance is
claimed. Native build/signing prerequisites and the Picomatch security advisory remain
open as documented in SECURITY.md and prior phase reports. Notifications and complete
profile/account-deletion settings remain future work.

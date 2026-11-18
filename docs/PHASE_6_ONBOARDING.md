# First-run introduction and clip privacy guide — 18 November 2026

A first-run guide now precedes the app's routed screens. It explains permitted local
clips, preview and explicit upload, limited catalog coverage, uncertain/no matches,
unsupported shared-link downloading, clip retention and guest/account discoveries.
Home includes a reusable How FrameTrace works & clip privacy route.

The introduction requests no OS permissions, invokes no recognition API and requires no
account. Its completion is a versioned local SecureStore preference, not legal consent,
a processing authorization or a record that someone read every paragraph. A missing,
malformed or older value shows the guide. A storage read/write failure offers a retry
and explicit session-only continuation; it never silently claims persistence. The guide's
Continue action is synchronously guarded against repeated taps. Reopening the guide does
not modify the preference. Existing initial account-session restoration may still occur
through the authentication library; this is not an app-wide offline/network guarantee.

Existing share inbox entries and interrupted submissions are not consumed or uploaded by
the guide. Their usual home-screen review/restore flow starts after continuation. An
incoming route remains in the router state until the routed app mounts. Real cold-start
and deep-link behavior still require device acceptance; no device result is claimed.

## Verification

- All 25 mobile tests passed, including four preference tests for fresh/outdated values,
  successful persistence, storage read failure and storage write failure.
- Strict TypeScript passed. Android and iOS JavaScript bundles exported successfully.
- UI uses scrollable content, system appearance, header semantics, readable text sizing
  and button accessibility roles. These are implementation choices, not an accessibility
  audit or screen-reader certification.
- No backend, native permission, dependency or environment configuration changed.
- Native compilation/signing, device QA and the existing Picomatch security advisory
  remain open. Prior reports and SECURITY.md retain those release gates.

## Device acceptance still required

Fresh install: see guide before home; continue, restart and confirm it stays dismissed.
Reopen from Home; Back returns Home, including when the guide is a direct route. Verify
storage failure retry/session-only flow, process death, incoming shared video and pending
upload restoration. No clip may upload from opening or leaving the guide. Test large
text, VoiceOver/TalkBack focus order, small screens, tablets and both appearances. Verify
camera/microphone prompts only appear after Record. This guide is not a published legal
privacy policy; legal/privacy review is a separate release prerequisite.

# Canonical Product Requirements — ClipCascade Extended

This document is the immutable product contract for `GoodLight999/ClipCascade-Extended`.
Every development thread must read it before designing or changing code. Requirements may be expanded, but must not be silently removed, weakened, or replaced by easier proxy goals.

## 1. Primary objective

Deliver the most reliable practical ClipCascade client, with stable background **send and receive** operation as the absolute requirement.

ADB-free operation is the preferred end state, but it is not more important than reliability. If a device requires Shizuku or direct ADB to pass the stability gate, that supported path must remain available and be documented honestly.

## 2. Runtime privilege paths

The implementation must support explicit, independently testable capability tiers:

1. **Standard mode** — Android AccessibilityService and ordinary Android APIs; no ADB or Shizuku.
2. **Enhanced mode** — Shizuku-backed permissions or commands when they improve real-device reliability.
3. **Engineering mode** — direct ADB for development, diagnostics, stress testing, provisioning, and a last-resort supported path when no equally reliable tap-driven method exists.

Shizuku integration should preferentially use or adapt the fork at:

- `https://github.com/thedjchi/Shizuku`

Installing Shizuku itself may be delegated to the user. Everything after installation must be presented as a guided, tap-through workflow suitable for a non-technical user. Direct ADB may remain where technically necessary, but production setup should be converted to a Shizuku-assisted click workflow whenever possible.

The app must display the active tier and must not claim background reliability until the active tier passes both send and receive self-tests.

## 3. Historical Go Android implementation is the functional baseline

Use this repository extensively:

- `https://github.com/wuxinkami/ClipCascade_go_fork`

The Android/mobile source was removed from its later branch state but remains preserved in Git history. The canonical recovery point currently identified is:

- commit `084616111aa993c77c9f293811534253b7d3d3f9`

Relevant preserved paths include:

- `mobile/android/`
- `fyne_mobile/bridge/`
- `fyne_mobile/engine/`
- `pkg/crypto/`
- `pkg/protocol/`
- Android build scripts and CI definitions from that commit lineage

Reconstruct the working clipboard-copy mechanism from the historical implementation first. Preserve its useful behavior and protocol compatibility, then make it a strict reliability and usability superset. Do not merely imitate the README or reimplement from memory while ignoring the preserved source.

The recovered source must be imported or adapted into `ClipCascade-Extended` so future development does not depend on the reference fork remaining online.

## 4. Original ClipCascade compatibility

The original project is the protocol and server compatibility authority:

- `https://github.com/Sathvik-Rao/ClipCascade`

The Extended client must remain wire-compatible with original ClipCascade servers. At minimum this includes the original authentication flow, user-info/E2EE key derivation, WebSocket endpoint, STOMP destinations, clipboard message schema, and encryption format.

No incompatible server fork may become mandatory. A user running the original ClipCascade server must be able to use the Extended client.

## 5. User experience and permission guide

The application must contain a complete setup and repair wizard for all required permissions and vendor-specific settings. A user should be able to complete recommended setup by repeatedly tapping clearly labelled buttons in the application and Android Settings.

The guide must cover, where applicable:

- AccessibilityService enablement
- notification permission
- battery optimization exemption
- vendor autostart/background execution settings
- overlay permission only when the selected backend genuinely requires it
- Shizuku connection and authorization
- wireless-debugging or ADB provisioning when required
- verification that each permission actually took effect
- remediation when a self-test fails

The UI must never report a permission, connection, or background path as working merely because the relevant settings page was opened.

## 6. Languages

All user-facing application screens, permission guides, diagnostics, setup instructions, and essential documentation must support:

- English
- Japanese
- Simplified Chinese

A feature is not complete until all three language paths are usable.

## 7. Signing and upgrades

Every distributable release APK must use one permanent signing identity. Version N+1 must install over version N without uninstalling and without losing configuration.

Debug signing must never be presented as the durable public release lineage. CI must fail clearly when release-signing material is missing rather than silently producing a differently signed replacement.

The private signing key must not be committed to the public repository. The repository must contain reproducible signing instructions and CI secret requirements.

## 8. Reliability and truthful diagnostics

Quality takes priority over speed of delivery. Do not stop at architecture notes or a successful compile.

Required verification includes:

- local copy detection and remote send while the activity is closed
- remote receive and Android clipboard write while the activity is closed
- no false “connected” state before authentication, WebSocket/STOMP handshake, and subscription succeed
- automatic recovery after Wi-Fi/mobile transitions
- automatic recovery after server restart
- recovery after process death and service restart
- documented behavior after phone reboot
- 24-hour background send test
- 24-hour background receive test
- 500-copy stress test without duplicate storms or measurable input lag
- loop suppression for self-originated and remotely written clipboard content
- no plaintext credentials or clipboard payloads in persistent logs
- upgrade installation using the permanent signing identity
- real-device evidence, beginning with HONOR/MagicOS and adding AOSP/Pixel and Samsung/One UI where available

A build artifact is not evidence of runtime stability. Self-tests must distinguish receive success from send success and must exercise the real runtime path, not an internal mock that bypasses Android restrictions.

## 9. Build and delivery

Development must continue through:

- source implementation
- automated tests
- CI execution
- correction of CI failures
- APK assembly
- signed release assembly once signing secrets are configured
- install/upgrade verification
- recorded real-device test evidence

Do not claim an APK is ready when only documentation exists or when CI has not produced and validated it.

## 10. Continuity and handoff

Maintain these files as canonical state:

- `HANDOFF.md` — concise current state, exact next actions, active branch/PR, validation status
- `docs/PRODUCT_REQUIREMENTS.md` — this permanent product contract
- `docs/WORKLOG.md` — factual implementation and test record

When the user says:

> https://github.com/GoodLight999/ClipCascade-Extended←これを引継いで開発して！

the next agent must be able to resume by reading those files and inspecting the repository and CI. Do not rely on chat memory.

Handoff documents must describe the current truth directly. They must not waste context on conversational mistakes, apologies, superseded drafts, or narrative correction history.

## 11. Future OTP, SMS, and email scope

After text clipboard synchronization is demonstrably stable, extend the app toward a reliability and usability superset of:

- `https://github.com/jd1378/otphelper`

The future module should extract one-time codes from permitted SMS, notification, and email-notification sources and synchronize or expose them safely without requiring ADB where a reliable alternative exists. Shizuku or ADB may be used when necessary under the same stability-first and guided-setup rules.

OTP work must not destabilize the clipboard core and must be isolated behind separately testable modules and permissions.

## 12. Prohibited shortcuts

- Do not optimize for the marketing phrase “ADB-free” at the expense of background reliability.
- Do not discard the preserved Go Android source and invent an unverified replacement without first reproducing its useful behavior.
- Do not claim connected status before the real protocol connection is established.
- Do not use broad every-tap Accessibility processing that causes input lag or event storms.
- Do not store passwords in plaintext SharedPreferences.
- Do not ship changing APK signatures.
- Do not declare completion from documentation, mocks, foreground-only behavior, or compilation alone.
- Do not omit Japanese, English, or Chinese setup paths.

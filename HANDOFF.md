# Canonical Handoff — ClipCascade Extended

This file is the single source of truth for resuming development.

## Trigger phrase

When the user says:

> https://github.com/GoodLight999/ClipCascade-Extended←これを引継いで開発して！

perform these steps before coding:

1. Read this file completely.
2. Read `docs/WORKLOG.md`, newest entry first.
3. Inspect the newest open draft PR and its CI status.
4. Read every architecture, compatibility, signing, testing, and roadmap document present under `docs/`.
5. Never sacrifice reliability merely to claim that ADB is absent. Preserve a tiered runtime design and choose the most reliable verified path for each Android device.
6. Keep this file and the worklog current in every meaningful commit.

## Current repository state

- Repository: `GoodLight999/ClipCascade-Extended`
- Default branch: `main`
- Active development branch: `agent/android-accessibility-foundation`
- Expected PR: a draft PR from that branch to `main`
- The active branch currently contains bootstrap documentation only. Android code, Go engine code, CI, and APK artifacts have not yet been committed.

## Source baselines

- Original protocol/server: `Sathvik-Rao/ClipCascade`
- Historical Go-based Android implementation: `wuxinkami/ClipCascade_go_fork` at commit `084616111aa993c77c9f293811534253b7d3d3f9`
- The Android source is preserved in that commit and remains directly retrievable. Relevant paths include:
  - `mobile/android/`
  - `fyne_mobile/bridge/`
  - `fyne_mobile/engine/`
  - `pkg/crypto/`
  - `pkg/protocol/`

Use the historical Android implementation as the functional baseline. Preserve its useful clipboard-access and Go-engine ideas, then improve reliability, localization, credential storage, diagnostics, and update continuity.

## Product priority order

1. Stable background send and receive operation.
2. Truthful diagnostics and automatic recovery.
3. Simple setup and upgrade continuity.
4. Original ClipCascade server compatibility.
5. ADB-free operation where it is genuinely reliable.
6. Additional clipboard types and OTP-related features.

ADB elimination is not an absolute requirement. ADB, wireless debugging, or Shizuku may remain when they measurably improve stability. The project must not knowingly ship an unreliable no-ADB path merely because it appears simpler.

## Supported reliability tiers

The implementation must be designed around explicit, testable tiers rather than one hidden mechanism:

- **Standard mode:** no ADB and no Shizuku. AccessibilityService and normal Android APIs only.
- **Enhanced mode:** Shizuku-backed privileges or commands, started through a user-facing tap workflow. This is the preferred compatibility fallback when Standard mode is unreliable on a device.
- **Engineering mode:** direct ADB for development, diagnostics, stress testing, and last-resort provisioning. Any production dependency on direct ADB must be documented honestly and replaced by a tap-driven Shizuku flow where technically possible.

The application must detect and display which tier is active. It must never claim full background reliability before the active tier passes self-tests.

## Non-negotiable product requirements

- Stable background operation is the absolute condition.
- ADB-free operation remains a preferred goal, not a higher priority than reliability.
- Shizuku is an approved compatibility and reliability mechanism.
- Direct ADB is approved for diagnostics and may remain as a fallback when no equally reliable tap-driven route exists.
- A normal user should be able to complete the recommended setup by tapping through the application, Android Settings, and Shizuku. Shizuku installation itself may be delegated to the user.
- Server behavior must remain compatible with the original ClipCascade server.
- English, Japanese, and Simplified Chinese must remain supported.
- Release APK updates must use one permanent signing identity.
- Connection UI must never report “connected” before the WebSocket/STOMP handshake succeeds.
- Copy detection must not react expensively to every ordinary tap.
- Never store server passwords in plaintext SharedPreferences.
- Every thread must leave exact next steps and test evidence here and in `docs/WORKLOG.md`.

## Architecture direction

- Native Kotlin Android application.
- Shared Go protocol/E2EE engine compiled with gomobile into `engine.aar` unless a native Kotlin replacement proves more reliable and remains wire-compatible.
- AccessibilityService is one clipboard-event source, not a dogma and not the sole permitted source.
- Shizuku/ADB adapters must be isolated behind a capability interface so the transport and loop-suppression logic do not depend on one privilege path.
- Copy events are hints only; actual sending is gated by changed content fingerprints and source-aware loop suppression.
- Remote clipboard writes are fingerprint-marked before writing to suppress bounce loops.
- Credentials are encrypted with a key stored in Android Keystore.
- Engine state is persisted separately so the UI shows the last truthful state.
- No permanent foreground-service type or boot-start strategy may be assumed valid without CI checks, Android-version checks, and real-device evidence.

## Immediate next steps

1. Import the historical Android and Go source needed for the first build.
2. Define a `ClipboardAccessBackend` capability interface with Standard, Shizuku, and Engineering implementations.
3. Implement the original server-compatible login, E2EE, WebSocket, and STOMP engine.
4. Build a startup/self-test matrix that separately verifies:
   - server authentication;
   - STOMP handshake and subscription;
   - remote receive and local write;
   - local copy detection and remote send;
   - background operation while the UI is closed;
   - restart/reconnect behavior;
   - active privilege tier.
5. Implement Standard mode first, then run it on HONOR/MagicOS. Add Shizuku immediately wherever Standard mode misses events or is killed.
6. Add CI for Go tests, gomobile AAR generation, Android lint/tests, and APK assembly.
7. Configure one fixed signing identity and verify that version N+1 installs over version N.
8. Add diagnostic export containing states and timestamps only, never clipboard payloads or passwords.
9. Record exact device/Android/tier results in `docs/WORKLOG.md`.
10. Only after text sync is stable, add images/files and OTP modules.

## Definition of “stable enough for daily use”

A release is not stable merely because it built or worked while the activity was open. The supported tier on each declared device class must pass:

- 24-hour background receive test without manual app reopening.
- 24-hour background send test with the screen both on and off where the OS permits clipboard changes.
- 500-copy stress test with no duplicate storm and no measurable input lag.
- Network transitions Wi-Fi → mobile → Wi-Fi recover automatically.
- Server restart recovers automatically.
- App process death and service restart recover automatically.
- Phone reboot recovery is documented and succeeds through the declared tier.
- No false “connected” state.
- No plaintext secrets in app storage or logs.
- Upgrade from version N to N+1 succeeds without uninstalling.
- Japanese, English, and Chinese setup paths all complete.
- The app reports Standard, Enhanced, or Engineering mode truthfully.

If Standard mode fails but Enhanced mode passes, the device is supported in Enhanced mode. That is an acceptable result. Claiming Standard-mode support despite failed tests is not.

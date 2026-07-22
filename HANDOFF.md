# Canonical Handoff — ClipCascade Extended

This file is the single source of truth for resuming development.

## Trigger phrase

When the user says:

> https://github.com/GoodLight999/ClipCascade-Extended←これを引継いで開発して！

perform these steps before coding:

1. Read this file completely.
2. Read `docs/WORKLOG.md`, newest entry first.
3. Inspect the newest open draft PR and its CI status.
4. Read `docs/ARCHITECTURE.md`, `docs/SERVER_COMPATIBILITY.md`, and `docs/ROADMAP.md`.
5. Never replace the no-ADB AccessibilityService architecture with an ADB-only clipboard-log reader.
6. Keep this file and the worklog current in every meaningful commit.

## Repository state at bootstrap

- Repository: `GoodLight999/ClipCascade-Extended`
- Default branch: `main`
- Active development branch: `agent/android-accessibility-foundation`
- Expected PR: a draft PR from that branch to `main`
- Source baselines:
  - Original protocol/server: `Sathvik-Rao/ClipCascade`
  - Historical Android implementation: `wuxinkami/ClipCascade_go_fork` at commit `084616111aa993c77c9f293811534253b7d3d3f9`
- The current repository started empty. This branch introduces the first implementation.

## Non-negotiable product requirements

- ADB-free stable operation is the final goal.
- Shizuku may be an optional compatibility aid, never the normal happy path.
- A user must be able to finish setup by tapping through the app and Android Settings.
- Server behavior must remain compatible with the original ClipCascade server.
- English, Japanese, and Simplified Chinese must remain supported.
- Release APK updates must use one permanent signing identity.
- Connection UI must never report “connected” before the WebSocket/STOMP handshake succeeds.
- Copy detection must not react to every ordinary tap.
- Never store server passwords in plaintext SharedPreferences.
- Every thread must leave exact next steps and test evidence here and in `docs/WORKLOG.md`.

## Implemented architecture

- Native Kotlin Android application.
- Android AccessibilityService owns the long-lived network engine lifecycle.
- Go engine compiled with gomobile into `engine.aar`.
- Temporary accessibility overlay is a fallback clipboard-read aid; `SYSTEM_ALERT_WINDOW` is optional.
- No perpetual `dataSync` foreground service.
- No boot receiver that illegally starts a restricted foreground service.
- Copy events are treated as hints only; actual sending is gated by a changed SHA-256 content fingerprint.
- Remote clipboard writes are fingerprint-marked before writing to suppress bounce loops.
- Credentials are encrypted with an AES-GCM key stored in Android Keystore.
- Engine state is persisted separately so the UI shows the last truthful state.

## Known incomplete work

1. A permanent signing key must be added to GitHub Actions secrets. See `docs/SIGNING.md`.
2. CI must be observed and any build failures fixed before calling the APK installable.
3. Real-device testing is still required on at least:
   - HONOR / MagicOS
   - Pixel / AOSP-like Android
   - Samsung / One UI if available
4. Clipboard images/files are not implemented in the Android bootstrap.
5. Shizuku adapter is only a roadmap item.
6. OTP/SMS/email notification extraction is only a roadmap item.
7. Accessibility copy-label heuristics need telemetry-backed tuning without collecting clipboard contents.
8. Vendor autostart/battery guides need device-specific deep links where safe.

## Immediate next steps

1. Fix all GitHub Actions failures until:
   - Go unit tests pass.
   - gomobile creates `android/app/libs/engine.aar`.
   - Android lint passes.
   - debug APK assembles.
2. Configure fixed signing secrets and verify a signed release APK.
3. Add an instrumentation test seam for AccessibilityService clipboard probes.
4. Add an in-app diagnostic export containing states/timestamps only, never clipboard payloads or passwords.
5. Run the real-device matrix and record exact results in `docs/WORKLOG.md`.
6. Only after text sync is stable, add images/files, Shizuku compatibility, and OTP modules.

## Definition of “stable enough for daily use”

- 24-hour background receive test without manual app reopening.
- 500-copy stress test with no duplicate storm and no input lag.
- Network transitions Wi-Fi → mobile → Wi-Fi recover automatically.
- Server restart recovers automatically.
- App process kill and AccessibilityService restart recover automatically.
- Phone reboot recovers after Android restores the enabled AccessibilityService.
- No false “connected” state.
- No plaintext secrets in app storage or logs.
- Upgrade from version N to N+1 succeeds without uninstalling.
- Japanese, English, and Chinese setup paths all complete.

# Canonical Handoff — ClipCascade Extended

This is the concise current-state entry point for resuming development. The permanent product contract is [`docs/PRODUCT_REQUIREMENTS.md`](docs/PRODUCT_REQUIREMENTS.md).

## Resume trigger

When the user says:

> https://github.com/GoodLight999/ClipCascade-Extended←これを引継いで開発して！

perform these steps before changing code:

1. Read this file completely.
2. Read `docs/PRODUCT_REQUIREMENTS.md` completely. Its requirements are non-negotiable.
3. Read `docs/WORKLOG.md`, newest entry first.
4. Inspect the repository tree, active branch, newest draft PR, CI runs, and artifacts. Never infer implementation from documentation alone.
5. Inspect the preserved Android source in the Go reference commit listed below before designing the clipboard path.
6. Continue implementation, tests, CI repair, APK building, and factual handoff updates in the same thread.

Handoff text must state the present truth directly. Do not spend context on conversational mistakes, apologies, superseded plans, or correction history.

## Repository state

- Repository: `GoodLight999/ClipCascade-Extended`
- Default branch: `main`
- Active development branch: `agent/android-accessibility-foundation`
- Open PR: none at the time of this handoff; create a draft PR after meaningful implementation is pushed.
- Current contents: bootstrap documentation and product requirements only.
- Not yet committed: Android implementation, Go engine, CI workflow, signing workflow, APK, or real-device evidence.

Do not claim code, CI, or APK exists until verified from the repository and workflow artifacts.

## Absolute priority

**Stable background send and receive operation is the absolute condition.**

ADB-free operation is preferred, but it is not an absolute requirement. Retain Shizuku or direct ADB whenever they measurably improve stability.

Runtime capability tiers:

1. **Standard** — AccessibilityService and ordinary Android APIs; no ADB or Shizuku.
2. **Enhanced** — Shizuku-backed reliability path. Prefer or adapt `https://github.com/thedjchi/Shizuku`. Shizuku installation may be delegated to the user; subsequent setup must be guided by clear tap-through screens.
3. **Engineering** — direct ADB for development, diagnostics, stress tests, provisioning, and a documented last resort when no equally reliable tap-driven path exists.

The app must disclose the active tier and separately prove background send and background receive before reporting that setup is healthy.

## Required source baselines

### Historical Go Android implementation — functional baseline

- Repository: `https://github.com/wuxinkami/ClipCascade_go_fork`
- Preserved Android recovery commit: `084616111aa993c77c9f293811534253b7d3d3f9`
- Relevant paths:
  - `mobile/android/`
  - `fyne_mobile/bridge/`
  - `fyne_mobile/engine/`
  - `pkg/crypto/`
  - `pkg/protocol/`
  - Android build scripts and historical CI

The Android source is not lost. It was removed from a later branch state but remains retrievable at the commit above.

Reconstruct its useful clipboard-copy mechanism first, import or adapt it into this repository, and then make it more reliable. Do not replace it with a speculative clean-room design without first reproducing its working behavior.

### Original ClipCascade — server/protocol authority

- Repository: `https://github.com/Sathvik-Rao/ClipCascade`

The Extended client must remain compatible with original ClipCascade servers. Preserve the original login, E2EE key derivation, WebSocket/STOMP endpoints, destinations, clipboard schema, and encryption format. No incompatible server fork may become mandatory.

### Future OTP baseline

- Repository: `https://github.com/jd1378/otphelper`

OTP, SMS, and email-notification code extraction is a later module. Implement it only after clipboard text synchronization passes the stability gate. It must be isolated so it cannot destabilize the clipboard core.

## Non-negotiable product requirements

- English, Japanese, and Simplified Chinese for all user-facing UI, setup, permissions, diagnostics, and essential documentation.
- Complete permission/setup/repair wizard suitable for a non-technical user clicking through the app and Android Settings.
- Guided AccessibilityService, notifications, battery optimization, vendor autostart, overlay-when-needed, Shizuku, and ADB/wireless-debugging setup.
- Permission verification based on actual state, not merely opening a Settings page.
- One permanent release signing identity for all public APKs.
- Version N+1 must install over version N without uninstalling or losing configuration.
- Android Keystore-backed credential protection; no plaintext password storage.
- Truthful connection state; never report connected before real authentication, WebSocket/STOMP handshake, and subscription succeed.
- Copy detection must not perform expensive work on every ordinary tap.
- Source-aware fingerprint loop suppression for local and remote clipboard writes.
- Capability interfaces must isolate Standard, Shizuku, and direct-ADB clipboard access from protocol, state, diagnostics, and UI.
- Work must continue through implementation, tests, CI, APK assembly, install/upgrade verification, and real-device evidence. Documentation or compilation alone is not completion.

## Immediate implementation sequence

1. Recover the historical Go Android source into a local working tree and audit licenses/attribution.
2. Import the minimum original-compatible Go protocol, crypto, gomobile bridge, and native Android shell into this repository.
3. Reproduce historical text send/receive behavior before redesigning it.
4. Introduce a `ClipboardAccessBackend` capability interface with Standard, Enhanced/Shizuku, and Engineering/ADB implementations or explicit placeholders.
5. Replace broad every-click processing with conservative event hints plus changed-content fingerprint checks.
6. Implement truthful engine states and independent send/receive self-tests that run while the activity is closed.
7. Implement encrypted configuration and the three-language setup/repair wizard.
8. Add CI for Go tests, gomobile AAR generation, Android lint/unit tests, and debug APK assembly.
9. Configure permanent release signing through repository secrets and verify N-to-N+1 update installation.
10. Run the real-device stability matrix beginning with HONOR/MagicOS; add Shizuku immediately if Standard mode is unreliable.
11. Record exact code, CI, artifact, and device results in `docs/WORKLOG.md` after each meaningful step.

## Stability gate

A device/tier combination is not supported merely because the activity-open path works or an APK compiles. It must pass:

- 24-hour background send test.
- 24-hour background receive test.
- Screen-on and screen-off behavior documented where Android permits clipboard changes.
- 500-copy stress test with no duplicate storm and no measurable input lag.
- Wi-Fi → mobile → Wi-Fi recovery.
- Server restart recovery.
- Process death/service restart recovery.
- Phone reboot recovery through the declared tier.
- No false connected state.
- No plaintext credentials or clipboard contents in persistent logs.
- Upgrade from version N to N+1 with the same signing identity.
- Complete English, Japanese, and Simplified Chinese setup paths.
- Accurate display of Standard, Enhanced, or Engineering mode.

If Standard fails but Enhanced passes, declare the device supported in Enhanced mode. Do not pretend Standard passed.

## Handoff maintenance rule

After every meaningful implementation or test session, update:

- this file with current branch/PR, actual implemented state, exact next actions, blockers, and validated artifacts;
- `docs/WORKLOG.md` with factual commits, commands, CI results, device/tier results, and failures;
- `docs/PRODUCT_REQUIREMENTS.md` only when requirements are deliberately expanded by the user, never to weaken existing requirements.

# ClipCascade Extended

Reliability-first Android client for servers compatible with
[`Sathvik-Rao/ClipCascade`](https://github.com/Sathvik-Rao/ClipCascade).

## Runtime/setup order

1. **ADB-free primary path:** Accessibility copy signal → serialized visible capture → clipboard read/staging → durable upstream-compatible transport.
2. **Android Share:** text, process text, image and files are staged immediately where required, then placed in the durable queue.
3. **Preferred privileged fallback:** open/get Shizuku from Extended, start and authorize it once, apply/verify grants, then stop Shizuku completely.
4. **Second fallback:** run two PC ADB commands once.
5. Always-on Shizuku is intentionally not a runtime requirement.
6. OTP/SMS/email extraction remains absent until generic clipboard real-device acceptance is complete.

The app includes direct Accessibility/overlay controls, guided one-time Shizuku setup, copyable PC ADB guidance, Reliability Self-Test and active one-tap diagnostics. Product UI, dynamic status, diagnostics and notifications support English, Japanese and Simplified Chinese.

## Architecture

- Authentication, encryption, P2S/STOMP, P2P/WebRTC, inbound text/image/files and server compatibility remain based on the pinned upstream source.
- Android capture follows the proven Accessibility→overlay→clipboard concept in `wuxinkami/ClipCascade_go_fork`, but replaces broad clicks, selection false positives, global debounce, dropped binding triggers and concurrent overlays with tested classification, a persistent event queue and a watchdog-protected coordinator.
- Accessibility uses `canRetrieveWindowContent=false`; ignored high-frequency events avoid AsyncStorage/SQLite work.
- The repository materializes the exact upstream commit from `UPSTREAM.lock`, copies canonical overlay source and applies deterministic finalizers guarded by static checks and tests.

## Reliability design

### Capture and Share

- JavaScript listeners are registered before the native durable-event queue is activated and drained.
- One-shot capture launch, retry, destruction and timeout cannot permanently wedge later requests.
- Text and readable clipboard URIs use a common native reader; transient URI bytes are staged into app-owned cache.
- Handles MIME-less/Spanned/HTML `ACTION_SEND`, `ACTION_PROCESS_TEXT`, image, single-file and multiple-file Share.
- Staged URI lists use JSON; legacy queue entries remain readable.
- File, batch and total-cache limits, expiry and partial-failure cleanup are enforced.

### Durable delivery

- Outbound items persist across offline periods, reconnects and process death in a queue scoped to server mode, URL and username.
- Non-manual runtime replacement/failure preserves queued work; explicit manual stop clears it.
- Transport adapters return explicit delivery outcomes. Ambiguous truthy values cannot delete a queue head.

P2S:

- Keeps the upstream payload exactly `{payload, type}`.
- Uses standard STOMP `receipt` acknowledgement, with upstream self-echo as an identity-checked compatibility fallback.
- A late receipt/echo can acknowledge only the matching durable head.
- Receipt timeout is transient and retried rather than permanently discarding valid data.
- Runtime ownership is checked again immediately before `publish()`.
- Typed, expiring one-shot guards replace the old global hash/image flag and cannot suppress an unrelated next copy.

P2P:

- Stable retry IDs, UTF-8-safe fragments, bounded concurrent reassembly, replay/conflict/TTL controls and DataChannel backpressure.
- Signaling-connected and open-compatible-DataChannel states remain distinct.
- Incompatible/decrypt-failing peers are quarantined individually.
- Optional compatibility metadata travels only in OFFER/ANSWER; no proprietary clipboard control frame is sent to legacy clients.

### Foreground runtime

- One Notifee handler and one JavaScript network-runtime lease.
- Every start is serialized; forced replacement waits up to 10 seconds for the exact old lease to finish.
- Notification display alone is not success: startup waits up to 8 seconds for a live runtime lease.
- Five-second heartbeat, 15-second stale threshold, supervised loops/callbacks and coordinated pending-Share recovery.
- WorkManager, boot/update and visible-copy recovery use explicit start intent, not stale-state toggling.

### Shizuku boundary

- Transient non-daemon AIDL UserService for setup only.
- Sticky Binder delivery, Binder death, authorization, bounded startup and command exit codes are handled.
- Success requires actual retained READ_LOGS and overlay state.
- `binder-pending` represents the Shizuku startup race without falsely declaring it absent.
- Routine capture/network source is statically forbidden from using Shizuku.

### Product integrity

- Extended-owned screens, deterministic light/dark palettes and complete EN/JA/zh-CN localization.
- ADB commands and diagnostic reports are selectable and one-tap copyable.
- Upstream footer, external-link/funding UI, update prompts and update/metadata requests are absent.
- OTP notification-listener/extractor classes are absent from source and APK; CI rejects reintroduction.

## Build

```bash
./scripts/materialize_upstream.sh
cd build/mobile
npm ci
python3 ../../scripts/patch_react_native_snapshot_repository.py .
npm run lint
npm test -- --runInBand
cd android
./gradlew lintExtended testExtendedUnitTest assembleExtended
```

APK output:

```text
build/mobile/android/app/build/outputs/apk/extended/app-extended.apk
```

Identity:

```text
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.5 / versionCode 320005
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

## One-time fallback

Preferred:

1. Press **Open / get Shizuku** in Extended.
2. Start Shizuku, return to Extended and run one-time setup.
3. Verify Self-Test, then stop Shizuku completely.

Second choice:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

Same-package/same-signer in-place updates normally retain settings and grants, but Extended verifies actual state. Uninstalling resets them.

## Validated implementation artifact

```text
Implementation commit: 349003a994a0f05485a4f86605f9939abd4bcc98
Successful CI run: 30187796193
Version: 3.2.0-extended.5 / 320005
APK size: 93,681,991 bytes
APK SHA-256: 19d2fad3ca85b4d0be7a15e3cb0042327c1d018e1ce33eb0c0281adef4aeb818
Signature: APK Signature Scheme v2
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

Run `30187796193` passed exact materialization, all architecture/forbidden-residue validators, signing-key inspection, dependency/repository audit, ESLint, every Jest suite, Android Lint, every Extended Kotlin test, APK assembly, ZIP/zipalign, v2 signature, Manifest/DEX/Hermes checks, checksum and artifact upload.

The same signed APK then passed API 35 and API 36 emulator smoke: light/dark launch, text Share, `ACTION_PROCESS_TEXT`, cold-start MediaStore real-PNG Share with app-owned staging/native-event evidence, HOME/background process survival, and crash/ANR/known-regression scans. Downloaded APK and evidence archives were independently rechecked.

This is a **strong automated device-test candidate**, not final product acceptance. HONOR 400 Pro upgrade/OEM background behavior, live upstream P2S/P2P/desktop interoperability, Shizuku retention after stop/reboot, screen-off/Doze/process/reboot endurance, battery and typing-latency evidence remain required. PR #2 stays Draft.

See `HANDOFF.md`, `WORKLOG.md` and `docs/TEST_PLAN.md` for the canonical continuation and acceptance matrix. `3.2.0-extended.3` remains device-failed and must not be reused as a baseline.

# ClipCascade Extended

Reliability-first Android client for servers compatible with [`Sathvik-Rao/ClipCascade`](https://github.com/Sathvik-Rao/ClipCascade).

## Runtime/setup order

1. **ADB-free primary path:** Accessibility copy signal → serialized visible capture → clipboard read/staging → durable upstream-compatible transport.
2. **Android Share:** text, process text, image and files are staged immediately where required, then placed in the durable queue.
3. **Preferred privileged fallback:** use Shizuku once to apply and verify retained grants, then stop it completely.
4. **Second fallback:** run two PC ADB commands once.
5. Routine runtime intentionally has no always-on Shizuku dependency.
6. OTP/SMS/email extraction remains absent until generic clipboard real-device acceptance is complete.

Extended includes Accessibility/overlay controls, guided Shizuku setup, copyable ADB guidance, Reliability Self-Test and active diagnostics. UI, runtime status, diagnostics and notifications support English, Japanese and Simplified Chinese.

## Architecture

- Authentication, encryption, P2S/STOMP, P2P/WebRTC, inbound text/image/files and server compatibility remain based on pinned upstream source.
- Android capture follows the proven Accessibility→visible overlay→clipboard concept in `wuxinkami/ClipCascade_go_fork`, while replacing broad clicks, selection false positives, global debounce, dropped binding events and concurrent overlays with tested classification, persistent ordering and a watchdog-protected coordinator.
- Accessibility uses `canRetrieveWindowContent=false`; ignored high-frequency events avoid AsyncStorage/SQLite work.
- `UPSTREAM.lock` + `scripts/materialize_upstream.sh` reproducibly generate the app from canonical `overlay/` source and deterministic finalizers.

## Reliability design

### Capture and Share

- JavaScript listeners are registered before native durable-event activation/drain.
- Capture launch, retry, Activity destruction and timeout cannot permanently wedge later requests.
- Text and readable clipboard URIs use a common native reader; transient bytes are staged into app-owned cache.
- Handles MIME-less/Spanned/HTML text, `ACTION_PROCESS_TEXT`, image and single/multiple-file Share.
- JSON URI lists, legacy queue decoding, file/batch/cache limits, expiry and partial-failure cleanup.

### Durable delivery

- Server-scoped queue survives offline periods, reconnects and process death.
- Recovery/replacement/failure preserves queued work; explicit manual stop clears it.
- Delivery adapters return explicit outcomes; ambiguous truthy values cannot delete a queue head.

P2S keeps the upstream payload exactly `{payload, type}`. Standard STOMP `receipt` is primary acknowledgement, with upstream self-echo as an identity-checked fallback. Late callbacks may acknowledge only the matching durable head. Receipt timeout is transient. Runtime ownership is rechecked immediately before `publish()`. Typed expiring feedback guards replace the old global hash/image flag.

P2P uses stable retry IDs, UTF-8-safe fragments, bounded concurrent reassembly, replay/conflict/TTL controls and DataChannel backpressure. Signaling and an open compatible DataChannel are distinct states. Incompatible peers are quarantined individually. Optional compatibility metadata travels only in OFFER/ANSWER; no proprietary clipboard control frame is sent.

### Foreground runtime

- One Notifee handler and one JavaScript network-runtime lease.
- All starts are serialized; forced replacement waits up to 10 seconds for the exact old lease.
- Notification display alone is not success; startup waits up to 8 seconds for a live callback lease.
- Five-second heartbeat, 15-second stale threshold and supervised loops/callbacks.
- WorkManager, boot/update and visible-copy recovery use explicit start intent, not stale-state toggling.

### Shizuku boundary

- Transient non-daemon AIDL UserService for setup only.
- Sticky Binder delivery, Binder death, authorization, bounded startup and command exit codes.
- Success requires real retained READ_LOGS and overlay state.
- `binder-pending` represents the startup race truthfully.
- CI statically forbids Shizuku use in routine capture/network source.

### Product integrity

- Extended-owned screens, deterministic light/dark palettes and complete EN/JA/zh-CN localization.
- Selectable/copyable ADB and diagnostic reports.
- No inherited footer, funding/link UI, update prompt or update/metadata request.
- OTP notification-listener/extractor code is absent and CI rejects reintroduction.

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

Output:

```text
build/mobile/android/app/build/outputs/apk/extended/app-extended.apk
```

Identity:

```text
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.5 / 320005
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

## One-time fallback

Preferred: open/get Shizuku from Extended, authorize and apply setup, verify Self-Test, then stop Shizuku completely.

Second choice:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

Same-package/same-signer updates normally retain settings and grants, but Extended verifies actual state. Uninstall resets them.

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

Run `30187796193` passed exact materialization, every validator, signing-key inspection, dependency/repository audit, ESLint, every Jest suite, Android Lint, every Kotlin test, APK assembly, ZIP/zipalign, v2 signature, Manifest/DEX/Hermes/checksum and artifact upload.

The same signed APK passed API 35 and API 36 smoke: light/dark launch, text Share, `ACTION_PROCESS_TEXT`, cold-start real-PNG MediaStore Share with app-owned staging/native-event evidence, HOME/background PID survival and crash/ANR/known-regression scans. APK and evidence archives were independently rechecked.

Later documentation and packaged-APK assertion updates do not alter the behavioral artifact authority above. Application-source changes require a new fully green build/API35/API36 authority.

This is a **strong automated device-test candidate**, not final product acceptance. HONOR 400 Pro upgrade/OEM behavior, live upstream P2S/P2P/desktop interoperability, Shizuku retention after stop/reboot, screen-off/Doze/process/reboot endurance, battery and typing latency remain required. PR #2 stays Draft.

See `HANDOFF.md`, `WORKLOG.md` and `docs/TEST_PLAN.md`. `3.2.0-extended.3` remains device-failed and must not be reused as a baseline.

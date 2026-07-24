# ClipCascade Extended

Reliability-first Android client for servers compatible with
[`Sathvik-Rao/ClipCascade`](https://github.com/Sathvik-Rao/ClipCascade).

## Runtime/setup order

1. **ADB-free clipboard runtime:** Accessibility copy signal → persistent serialized one-shot overlay → clipboard read/staging → durable upstream-compatible transport.
2. **Android Share outbound:** text/image/files → immediate bounded app-cache staging where required → durable transport.
3. **Best privileged fallback:** open/get Shizuku from Extended, start it once, authorize/apply/verify grants, then stop Shizuku.
4. **Second fallback:** run the two PC ADB commands once.
5. Always-on Shizuku is intentionally not a runtime requirement.
6. OTP/SMS/email is deferred until the generic clipboard device matrix is green.

The app provides direct Accessibility/overlay controls, guided Shizuku setup, copyable PC ADB guidance, Reliability Self-Test and one-tap active diagnostics. Product UI, dynamic status, diagnostics and notifications support English, Japanese and Simplified Chinese.

## Upstream + Go-fork architecture

- Authentication, encryption, P2S/STOMP, P2P/WebRTC, inbound text/image/files and server compatibility remain based on pinned `Sathvik-Rao/ClipCascade` source.
- The Android capture concept is based on the working Accessibility→overlay→clipboard path in `wuxinkami/ClipCascade_go_fork`.
- Generic clicks, selection-only capture, global debounce, dropped service-binding triggers, concurrent overlays and fragile state are replaced by a localized classifier, persistent native-event queue and serialized watchdog-protected coordinator.
- Accessibility declares `canRetrieveWindowContent=false`; ignored high-frequency events do not query AsyncStorage/SQLite.

## Reliability changes

### Capture and event delivery

- JavaScript listeners are registered before the native durable-event queue is activated and drained.
- Native events persist until listener readiness is explicit.
- One-shot overlay launch/destruction/timeout cannot permanently wedge later copies.
- Clipboard text and readable clipboard URIs use a common native reader; URI payloads are staged into app-owned cache before transient access disappears.
- Active diagnostics send a real native→React probe rather than trusting stored flags.

### Durable transport

- Outbound data persists across offline periods and process death in a bounded queue scoped to server mode, URL and username.
- P2S keeps an item until the server self-echoes `metadata.extendedDeliveryId`; timeout, backoff and late ACK are handled.
- P2P uses stable retry IDs, UTF-8-safe fragmentation, concurrent peer/message reassembly, replay/conflict/TTL limits and DataChannel backpressure.
- P2P signaling-only and actual open DataChannel states are distinct.
- Incompatible/decrypt-failing peers are quarantined individually instead of poisoning the whole room.
- Compatibility metadata travels only through optional OFFER/ANSWER fields already forwarded by the upstream signaling server; no proprietary clipboard control frame is sent to legacy clients.

### Android Share and files

- `ACTION_PROCESS_TEXT`, MIME-less/text/HTML `ACTION_SEND`, image, single-file and multiple-file shares are handled.
- Share and clipboard URIs are copied immediately into bounded app-owned FileProvider cache.
- URI lists use JSON; legacy comma-separated queue entries remain readable.
- File, batch and total-cache limits, partial-failure cleanup, expiry cleanup and duplicate suppression are enforced.

### Foreground runtime and recovery

- One foreground handler and one active network runtime lease are enforced.
- Start/stop decisions use persisted service state instead of stale React state.
- Service stop waiting is bounded.
- A 5-second heartbeat records actual runtime liveness; stale requested service state fails diagnostics.
- The polling loop is supervised and always releases listeners, service state and runtime lease after failure.
- When the service died but sync remains requested, the next explicit copy can recover it from the visible transparent capture Activity without relying on an illegal arbitrary background start.

### Shizuku boundary

- Shizuku uses a transient non-daemon AIDL UserService only for setup.
- Sticky Binder delivery, Binder death, authorization and setup timeouts are handled.
- Command exit codes and actual retained READ_LOGS/overlay states are verified before success.
- Routine capture and network files are statically forbidden from using Shizuku.

### Product integrity

- The inherited update/funding/footer UI and upstream update/metadata network calls are removed.
- Android adaptive colors are used for dark-mode readability.
- ADB instructions and diagnostic reports are selectable and one-tap copyable.
- OTP notification-listener/extractor code is absent from the core source and APK; CI rejects reintroduction.

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

APK: `build/mobile/android/app/build/outputs/apk/extended/app-extended.apk`

```text
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.4 / versionCode 320004
Signer SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

## One-time fallback

Preferred:

1. Press **Open / get Shizuku** in Extended.
2. Start Shizuku, return to Extended and press the one-time setup button.
3. Verify Self-Test, then stop Shizuku completely.

Second choice:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

A same-package/same-signer in-place update normally retains configuration and grants, but Extended rechecks actual state. Uninstalling resets them.

## Validated desk artifact

```text
Validated implementation commit: 225c15b221c5e33728b7997e34ff9221e9606730
Successful CI run: 30015603542
Version: 3.2.0-extended.4 / 320004
APK size: 93,636,243 bytes
APK SHA-256: af6fcf2b274c5bd57a08c2632fcb7efaa618dccab78250231b575c3006aefa48
Signature: APK Signature Scheme v2
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

The run passed exact materialization, architecture guards, signing-key inspection, ESLint, all Jest suites, Android Lint, all Extended Kotlin tests, APK assembly, ZIP/zipalign, v2 signature, Manifest checks, native DEX assertions, release Hermes assertions, OTP absence, upstream-update URL absence, checksum and artifact upload.

The downloaded artifact was independently extracted and its checksum, archive report, Manifest, DEX/Hermes markers and exclusion assertions were rechecked.

This is a **desk/static validated device-test candidate**, not device acceptance. HONOR 400 Pro testing is still required for OEM Accessibility delivery, background and screen-off behavior, live P2S/P2P interoperability, Shizuku grant persistence, service recovery, reboot/update recovery, exactly-once behavior, endurance, battery and typing-latency claims.

`3.2.0-extended.3` is explicitly device-failed and must not be reused as a baseline. See `HANDOFF.md`, `WORKLOG.md` and `docs/TEST_PLAN.md`.
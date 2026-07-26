# ClipCascade Extended — Reliability Test Plan

Compilation, Self-Test output and emulator CI are not final real-device acceptance.

## 1. Automated gate

Every behavioral source head must pass:

- exact pinned-upstream materialization and every guarded finalizer;
- canonical-source, architecture, ordering and forbidden-residue validators;
- deterministic signed-variant dev-server resource scoped only to `extended`;
- stable signing-key inspection;
- dependency/repository audit, ESLint and every Jest suite;
- Android Lint, every Extended Kotlin unit test and `assembleExtended`;
- APK ZIP integrity, zipalign, fixed v2 signature and checksum;
- packaged `resources.arsc` fixed loopback value and absence of RFC1918 build-host IP;
- package/version/non-debuggable/Accessibility/permission/Shizuku Manifest checks;
- native DEX reliability checks;
- packaged Hermes checks for listener readiness, serialized runtime/start confirmation, receipt/self-echo delivery, typed feedback, queue preservation and localization;
- packaged absence of OTP, inherited update URLs/UI and obsolete transport markers;
- API 35 and API 36 smoke using the uploaded signed release APK.

Current deterministic-resource candidate:

```text
Implementation commit: 751b8b4bec93a81ecab00c1df5a885b5c844c550
CI run: 30191423570
Version: 3.2.0-extended.5 / 320005
Application ID: com.clipcascade.extended
APK size: 93,681,991 bytes
APK SHA-256: 475d3c3f511852267710da5880c61955c247538701ada534aba2999d172c8b28
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

Run `30191423570` passed build and both emulator jobs. API 35/API 36 evidence contains `checkpoint=passed`, exit code `0`, numeric MediaStore URI, image staging/native-event markers, background PID, light/dark screenshots and no app crash/ANR/known-regression marker. APK and evidence were independently rechecked.

The documentation-only build immediately following this update must reproduce the exact APK hash above. A different hash fails reproducibility even if functional tests remain green.

`3.2.0-extended.3` is device-failed and is not an acceptance baseline.

## 2. Upgrade-first install

1. Do not uninstall before recording upgrade behavior.
2. Install `.5` / `320005` over the installed same-package build.
3. Record installer failure rather than bypassing it with uninstall.
4. Verify application ID and signer.
5. Verify server/settings/requested-state and retained permissions/app-ops.
6. Run/copy automatic diagnostics before setup changes.
7. Record Reliability Self-Test.
8. Perform a separate clean-install test only after upgrade evidence is saved.

## 3. UI and localization

Test Japanese, English and Simplified Chinese in light and dark mode.

Require complete language consistency across login, advanced settings, synchronization, setup, Self-Test, diagnostics, dynamic runtime states and notifications. Technical details/raw JSON remain available. ADB/report text is selectable and copyable. No inherited footer/link/funding/update UI, obsolete ADB guidance or update/metadata request. Any unreadable/mixed screen or obscuring permission dialog fails.

## 4. ADB-free clipboard path

Enable the copy detector and overlay through Extended, keep Shizuku stopped and PC ADB disconnected, then connect to a known-good server. Connected is allowed only after real P2S transport or an open compatible P2P DataChannel.

Across browser, messaging, notes/editor, document/PDF viewer and an OEM/system app:

- hidden unique text copy → exactly one peer delivery;
- selection without copy → no stale resend;
- rapid A→B→C → exact order/no miss;
- repeated same value and A/B/A/B;
- removed-from-recents, idle and recoverable runtime/process death;
- multilingual feedback, rotation and battery saver where available.

Inspect classifier/coordinator/capture/native-event/queue state after any miss.

## 5. Share text/process text

While Extended is closed and already open, test ordinary text, Spanned/styled text, HTML, MIME-less `ACTION_SEND` with `EXTRA_TEXT` and `ACTION_PROCESS_TEXT`. Require one durable item, listener-safe native delivery, runtime start only when requested and pending-state cleanup for unsupported/empty intents.

## 6. Images and files

### Image clipboard

Copy from an app exposing a readable clipboard URI. Require immediate staging, one correct peer delivery and truthful diagnostics for unreadable URIs. Repeat hidden/idle and repeated/alternating images; feedback suppression must not erase a legitimate next value.

### Android Share

Test one/multiple images, one/multiple generic files, comma/non-ASCII filenames, `CharSequence` plus stream, bounded large/batch inputs and broken/oversized/partial batches. Require immediate FileProvider staging, JSON URI list, exactly one durable delivery, no partial leftovers and expiry cleanup.

## 7. Emulator smoke

API 35 and API 36 must each:

1. verify checksum and install release APK;
2. capture light launch screenshot/UI XML;
3. pass text Share and process-text native-event markers;
4. create/write a real PNG in MediaStore and resolve numeric Content URI;
5. cold-start `ACTION_SEND image/png` with matching data/stream and read grant;
6. record image staging and native-event markers;
7. HOME, wait and require live process PID;
8. capture dark launch screenshot/UI XML;
9. reject app/native crash, ANR, React-host, StatusBar, forbidden foreground-service and AEAD markers;
10. emit passed summary/checkpoint and exit code `0`.

## 8. Reproducible release build

1. Build a fully green `assembleExtended` artifact and record APK bytes/hash.
2. Change documentation only; do not modify generated mobile inputs, dependencies, signer or workflow build commands.
3. Run the full build again on a different hosted runner.
4. Require identical APK size and SHA-256.
5. Extract both APKs and require all entries, including `resources.arsc` and v2 signature payload, to be byte-identical.
6. Require packaged-resource validator output `Packaged release resources contain no build-host private IP: OK` in both runs.

Any private runner address or repeat-build hash difference fails the gate.

## 9. Automatic diagnostics

Require active coverage of native→React probe, listener readiness/pending events, Accessibility/classifier/coordinator/capture, real foreground clipboard read/MIME/URI count, outbound queue, Share staging/cache, service heartbeat/runtime/duplicate/transition/recovery errors, P2P compatibility/errors, P2S incident counters, Shizuku/grants and package/device identity.

Copied reports must exclude credentials, username, endpoints, hashes/keys and salt.

## 10. P2S matrix

Outbound cases: multilingual/long text, emoji/combining characters, offline reconnect, disconnect after publish, receipt timeout, early receipt, late receipt after another head, self-echo fallback, runtime replacement immediately before publish, image and file flows.

Require exact upstream `{payload, type}` body, standard receipt primary ACK, matching self-echo fallback, queue-head identity for late callbacks, transient timeout/no permanent drop, WAITING+queue retention when stop begins before publish, manual-only clear, typed feedback and coalesced inbound incidents.

Inbound: text/image/files in visible/background/screen-off states where allowed, repeated/alternating values and reconnect. Require correct apply/save, one-shot loop suppression and truthful connection state.

## 11. P2P matrix

Test matching Extended peer, legacy upstream peer, encryption-mode mismatch, different key, multiple peers/reconnect/departure, simultaneous long fragmented send/receive, disconnect/retry and overlapping fragmented messages.

Require no proprietary control frame/signaling type, legacy-safe OFFER/ANSWER metadata, explicit success/waiting, individual quarantine, no repeated recreation/send, truthful open-compatible peer count and no repeated AEAD flood.

## 12. Foreground runtime/lifecycle

Exercise normal duplicate starts, pending Share start, stale-heartbeat replacement, successful/failed/timed-out old stop, missing callback lease, HOME/background, screen off, Doze, process kill, boot/update, network transitions, peer sleep/wake and capture timeout/destruction.

Require serialized starts, duplicate join, exact old-lease wait, no success before live callback lease, no old-state overwrite, queue preservation on non-manual replacement and no coordinator wedge/duplicate runtime/startup lie.

## 13. Guided one-time Shizuku

Test not installed, Binder pending, unauthorized, ready to apply and already configured while stopped. Require bounded wait, authorization, successful remote exit codes and local retained-state verification. Stop Shizuku completely, repeat clipboard/Share, reboot without restarting it and retest. Denial/timeout must not leave BUSY or permit late work.

Routine Shizuku Binder dependency fails acceptance.

## 14. PC ADB fallback

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

Apply once, disconnect PC and repeat clipboard/Share/reboot/update. Revoke separately and require truthful degraded state.

## 15. Stress/endurance

- 30-minute rapid/repeated/alternating unique-copy sequence;
- 8-hour idle/reconnect;
- repeated receipt timeout/reconnect;
- simultaneous long P2P send/receive;
- repeated bounded image/file batches;
- repeated runtime death and next-copy recovery;
- battery, wakeups, typing latency, task loops and ghost notification observation.

Compare with Accessibility disabled.

## 16. Deferred OTP

OTP notification-listener/extractor code remains absent until generic clipboard and lifecycle acceptance is green on target device and live server/desktop.

## 17. Failure evidence

Record automatic diagnostics, device/OEM/build, Extended version/signer/hash, upgrade path, server mode/version/encryption, source/target/payload/timestamp/action, Self-Test, actual permission/app-op state, Shizuku state, focused logs/screens/UI XML and persistence across restart/reboot/update.

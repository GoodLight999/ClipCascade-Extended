# ClipCascade Extended — Reliability Test Plan

Compilation, Self-Test output and emulator CI are not final real-device acceptance.

## 1. Automated gate

Every behavioral source head must pass:

- exact pinned-upstream materialization and every guarded finalizer;
- canonical-source, architecture, ordering and forbidden-residue validators;
- deterministic signed-variant dev-server resource scoped only to `extended`;
- Android dependency information excluded from APK/Bundle signing metadata;
- stable signing-key inspection;
- dependency/repository audit, ESLint and every Jest suite;
- Android Lint, every Extended Kotlin unit test and `assembleExtended`;
- APK ZIP integrity, zipalign, fixed v2 signature and checksum;
- packaged `resources.arsc` fixed loopback value and absence of RFC1918 build-host IP;
- APK Signing Block absence of dependency-info pair `0x504b4453`;
- package/version/non-debuggable/Accessibility/permission/Shizuku Manifest checks;
- native DEX reliability checks;
- packaged Hermes checks for listener readiness, serialized runtime/start confirmation, receipt/self-echo delivery, typed feedback, queue preservation and localization;
- packaged absence of OTP, inherited update URLs/UI and obsolete transport markers;
- API 35 and API 36 smoke using the uploaded signed release APK.

Current reproducible artifact authority:

```text
Application/build implementation commit: 3f7f01d36d19456bd741fb8b2e65b913cc4ddf34
Final harness head: ac34de11c73d4d565542b482739c2b3e5339b304
First deterministic build run: 30192487659
Second byte-identical build and complete smoke run: 30192942851
Version: 3.2.0-extended.5 / 320005
Application ID: com.clipcascade.extended
APK size: 93,673,799 bytes
APK SHA-256: 5911acfcba1e0e7a28b3e5cc13f268d5fbeb9c4c1653c9148d0954f8333e557c
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

The two hosted-runner APKs are identical under SHA-256 and `cmp`, with the same 537 ZIP entries, central directory, v2 signer pair and deterministic padding. Run `30192942851` passed build, API 35 and API 36. Both evidence archives contain `checkpoint=passed`, exit code `0`, numeric MediaStore URI, image staging/native-event markers, background PID, light/dark screenshots and no app/native crash, ANR or known-regression marker.

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

Transient `adb logcat -d` failures are retried up to three times. Each failed attempt remains in the evidence artifact. Positive markers may receive a short bounded wait and fresh log capture. This must not bypass crash/ANR/known-regression checks.

## 8. Reproducible release build

1. Build the complete signed `assembleExtended` artifact on a hosted runner and record bytes/hash.
2. Change only files outside Android materialization/build inputs, such as the emulator harness or documentation.
3. Run the same full build on another hosted runner.
4. Require identical APK size, SHA-256 and `cmp` result.
5. Require identical ZIP entry names/content, central directory and APK Signing Block pair hashes.
6. Require Signing Block IDs to contain v2 signature `0x7109871a` and deterministic padding `0x42726577`, and not contain dependency-info `0x504b4453`.
7. Require packaged-resource validator output confirming no build-host private IP or SDK dependency block.

Any repeat-build byte difference fails this gate.

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

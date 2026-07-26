# ClipCascade Extended — Reliability Test Plan

Compilation, Self-Test output and emulator CI are not final real-device acceptance.

## 1. Automated gate

Every behavioral source head must pass:

- exact pinned-upstream materialization and every guarded finalizer;
- canonical-source, architecture, ordering and forbidden-residue validators;
- stable signing-key inspection;
- `npm ci`, repository audit, ESLint and every Jest suite;
- Android Lint and every Extended Kotlin unit test;
- `assembleExtended`;
- APK ZIP integrity and zipalign;
- APK Signature Scheme v2 and fixed certificate verification;
- package/version/non-debuggable/Accessibility/permission/Shizuku Manifest checks;
- native reliability DEX checks;
- packaged Hermes checks for listener readiness, runtime serialization, start confirmation, standard receipt/self-echo delivery, typed feedback, queue preservation and localization;
- packaged absence of OTP classes, inherited update URLs/UI and obsolete transport markers;
- checksum and artifact upload;
- API 35 and API 36 smoke using the uploaded signed release APK.

Current behavioral implementation authority:

```text
Implementation commit: 349003a994a0f05485a4f86605f9939abd4bcc98
CI run: 30187796193
Version: 3.2.0-extended.5 / 320005
Application ID: com.clipcascade.extended
APK size: 93,681,991 bytes
APK SHA-256: 19d2fad3ca85b4d0be7a15e3cb0042327c1d018e1ce33eb0c0281adef4aeb818
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

Run `30187796193` passed build and API 35/API 36 smoke. Both emulator evidence archives contain `checkpoint=passed`, exit code `0`, numeric MediaStore URI, image staging/native-event markers, a live background PID, light/dark screenshots and no app crash/ANR/known-regression marker. The APK and evidence were independently rechecked.

`3.2.0-extended.3` is device-failed and must not be used as an acceptance baseline.

## 2. Upgrade-first install

1. Do **not** uninstall the existing Extended build before recording upgrade behavior.
2. Install `.5` / `320005` over the currently installed same-package build.
3. Record installer failure instead of bypassing it with uninstall.
4. Verify application ID and signer remain the values above.
5. Verify server URL, username, settings, requested synchronization state and retained permissions/app-ops.
6. Before changing setup, run automatic diagnostics and copy the complete report.
7. Record Reliability Self-Test.
8. Perform a separate clean-install onboarding test only after upgrade evidence is saved.

## 3. Product UI and localization

Test Android language in Japanese, English and Simplified Chinese, in light and dark mode.

Require:

- login, advanced settings, synchronization, setup, Self-Test and diagnostics consistently use the selected language;
- dynamic connection/login/logout/error state and notifications are localized;
- technical exception detail and raw JSON remain available;
- ADB commands and reports are selectable and one-tap copyable;
- input, card, dialog and body contrast is readable;
- inherited GitHub/help/donate/homepage/footer/update prompt and obsolete ADB guidance are absent;
- no upstream update/metadata request occurs.

Any mixed inherited UI, hidden permission dialog or unreadable screen is a failure.

## 4. ADB-free clipboard path

1. Enable **ClipCascade copy detector** through Extended.
2. Confirm Accessibility states that window content is not retrieved.
3. Allow overlay through Extended.
4. Keep Shizuku stopped and PC ADB disconnected.
5. Connect to a known-good server.
6. Require Connected only after real P2S transport or an open compatible P2P DataChannel. Signaling alone must say it is waiting for a peer.

Test at least browser, messaging, notes/editor, document/PDF viewer and an OEM/system app.

For each:

- copy unique text while Extended is hidden; require exactly one peer delivery;
- select without copying; stale clipboard must not resend;
- rapid A→B→C; require order, no miss and no stale value;
- repeat the same value and alternate A/B/A/B;
- repeat after removing UI from recents while runtime remains requested;
- repeat after recoverable process/runtime death;
- inspect classifier/coordinator/capture/native-event/queue state after any miss.

Repeat representative tests with multilingual copy feedback, rotation, battery saver and available screen states.

## 5. Android Share text/process text

Test while Extended is closed and while already open:

- ordinary `text/plain`;
- Spanned/styled text;
- HTML text;
- MIME-less `ACTION_SEND` with `EXTRA_TEXT`;
- `ACTION_PROCESS_TEXT`.

Require exactly one durable item, listener-safe native delivery, automatic runtime start only when synchronization is requested, and pending-state cleanup for unsupported/empty intents.

## 6. Image clipboard and Share files

### Image clipboard

- Copy an image from an app exposing a readable clipboard URI.
- Require immediate app-owned staging while access is valid.
- Require exactly one correct peer delivery.
- Repeat hidden, removed from recents and after idle.
- Repeat/alternate images; feedback suppression must not erase a later legitimate value.
- An unreadable URI must produce truthful diagnostic failure, not success.

### Android Share

Test:

- one image and multiple images;
- one generic file and multiple files;
- comma and non-ASCII filenames;
- `CharSequence` plus stream;
- moderately large file and bounded multi-file batch;
- broken/oversized/partially readable batches.

Require immediate FileProvider staging, JSON URI list, exactly one durable delivery, no partial leftovers after rejection, expiry cleanup and localized save/staging errors.

## 7. Emulator smoke contract

API 35 and API 36 must each:

1. verify artifact checksum and install the release APK;
2. launch light mode and capture screenshot/UI XML;
3. pass text Share and `ACTION_PROCESS_TEXT` native-event markers;
4. create a real PNG, insert it into MediaStore, resolve its numeric Content URI and write its bytes;
5. cold-start Extended with `ACTION_SEND image/png`, matching `Intent.data`/`EXTRA_STREAM` and read grant;
6. record `Shared payload staged: event=SHARED_IMAGE;count=1` and `Native event accepted: event=SHARED_IMAGE`;
7. HOME the app, wait and require a live process PID;
8. launch dark mode and capture screenshot/UI XML;
9. reject app crash, native crash, ANR, React-host, StatusBar, forbidden foreground-service and AEAD regression markers;
10. emit `summary.json`, `checkpoint=passed` and exit code `0`.

## 8. Automatic diagnostics

Run before setup changes and after every failure. Require active coverage of:

- native→React probe and timeout;
- listener readiness and pending native events;
- Accessibility/classifier/coordinator/capture state;
- real foreground clipboard read, MIME types and URI count;
- outbound queue count/state/failure;
- Share pending/staging/cache count and bytes;
- service requested state, heartbeat freshness, runtime instance, duplicate suppression, transition/recovery/loop/detached errors;
- P2P candidate/compatible/incompatible peers and operation/signaling errors;
- P2S inbound incident code/count/time/detail;
- Shizuku Binder/API/UID/authorization and actual READ_LOGS/overlay;
- package/version/device identity and raw status JSON.

The copied report must exclude password, hashes/keys, username, server/WebSocket URL and salt.

## 9. P2S transport matrix

Use an upstream-compatible server and desktop/client.

Outbound cases:

- short/long multilingual text, emoji and combining characters;
- offline enqueue then reconnect;
- disconnect after publish but before acknowledgement;
- receipt timeout and retry;
- receipt arriving before the local send promise completes;
- late receipt after another queue item is head;
- self-echo fallback with and without receipt support;
- runtime replacement during base64/encryption immediately before publish;
- image clipboard and Share text/image/files.

Require:

- wire payload remains exactly upstream-compatible `{payload, type}`;
- standard STOMP `receipt` is primary acknowledgement;
- matching self-echo may acknowledge the same durable head;
- late receipt/echo never removes a different head;
- timeout is transient and does not permanently drop valid work;
- a stop beginning before publish returns WAITING and retains the queue;
- explicit manual stop clears only when intended;
- no global previous-content hash or untyped image suppression;
- repeated AEAD/malformed incidents are coalesced and reset on success.

Inbound cases: text/image/files, visible/background/screen-off where allowed, repeated and alternating values, reconnect after sleep/wake. Require correct apply/save behavior, typed one-shot loop suppression and no false connection state.

## 10. P2P transport and compatibility

Test:

- one matching Extended peer;
- one legacy upstream peer without compatibility metadata;
- encryption-mode mismatch;
- different key causing AEAD failure;
- several peers, reconnects and departures;
- long simultaneous bidirectional fragmented text;
- disconnect during send and retry;
- overlapping fragmented messages from different peers.

Require:

- no proprietary DataChannel control frame or unsupported signaling type;
- optional OFFER/ANSWER metadata does not break legacy peers;
- success/waiting delivery result is explicit;
- one incompatible peer is quarantined without stopping compatible peers;
- quarantined peers are not recreated/sent repeatedly;
- Peer count represents open compatible DataChannels, not signaling sessions or duplicate runtimes;
- no repeated AEAD flood for an isolated peer.

## 11. Foreground runtime / lifecycle

Exercise:

- normal duplicate start requests;
- pending Share with stopped runtime;
- stale-heartbeat forced replacement;
- old runtime that stops successfully;
- old runtime whose stop callback fails or exceeds 10 seconds;
- notification displayed but no callback lease within 8 seconds;
- HOME/background, screen off, Doze, process kill, force-stop/relaunch;
- boot and package replacement;
- Wi-Fi/mobile/airplane changes, server restart and peer sleep/wake;
- second copy while capture is in flight and capture timeout/destruction.

Require:

- starts are serialized;
- normal duplicate start joins the active runtime;
- replacement waits for exact old lease completion before new start;
- no success before a real callback lease;
- old terminal state cannot overwrite new runtime state;
- non-manual replacement preserves durable queue;
- no coordinator wedge, duplicate overlay, multiple runtime leases or startup Connected lie.

## 12. Guided one-time Shizuku

Test states:

- not installed;
- installed but Binder still pending;
- running unauthorized;
- authorized ready to apply;
- already configured while Shizuku is stopped.

Require guided open/install, bounded Binder wait, authorization, successful remote exit codes and local retained-grant verification. Stop Shizuku completely, repeat clipboard/Share tests, reboot without restarting Shizuku and retest. Denial/timeout must not leave BUSY or permit late work.

Any routine capture/network dependency on Shizuku Binder is a failure.

## 13. PC ADB fallback

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

Apply once, disconnect PC, repeat clipboard/Share/reboot/update tests. Revoke each separately and require truthful degraded state rather than fabricated success.

## 14. Stress and endurance

- 30-minute rapid/repeated/alternating unique-copy sequence;
- 8-hour idle/reconnect;
- repeated receipt timeout/reconnect cycles;
- simultaneous P2P long send/receive;
- repeated image/share batches within limits;
- repeated runtime death and next-copy recovery;
- battery, wakeups, typing latency, task/restart loops and ghost notification observation.

Record a baseline with Accessibility disabled and compare against detector-enabled behavior.

## 15. Deferred OTP

OTP notification-listener/extractor code is absent. Do not reintroduce it until every generic clipboard and lifecycle acceptance section is green on the target device and live server/desktop.

## 16. Failure evidence

Record:

- copied automatic-diagnostics report;
- device/OEM/Android build;
- Extended versionCode, signer and APK hash;
- upgrade or clean install path;
- server mode/version and encryption configuration;
- source/target app, payload pattern, timestamp and exact action;
- Self-Test before/after;
- actual permission/app-op screenshots where relevant;
- Shizuku absent/running/stopped state;
- focused logs/screenshots/UI XML only when automatic diagnostics are insufficient;
- whether the fault survives process restart, reboot or update.

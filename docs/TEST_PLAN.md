# ClipCascade Extended — Reliability Test Plan

Compilation, Self-Test output and CI are not device acceptance.

## Automated desk gate

Every behavioral code head must pass:

- exact pinned-upstream materialization and guarded finalizers;
- final architecture/scope invariants;
- stable signing-key inspection;
- `npm ci`, ESLint and all Jest suites;
- Android Lint and all Extended Kotlin unit tests;
- `assembleExtended`;
- APK ZIP integrity and zipalign;
- APK Signature Scheme v2 verification;
- package/version/Accessibility/READ_LOGS/overlay/Shizuku Manifest checks;
- non-debuggable and OTP-free Manifest/DEX checks;
- required native reliability implementation checks in DEX;
- required listener/singleton/recovery/share/localization checks in the release Hermes bundle;
- absence of upstream update/metadata URLs in the release bundle;
- checksum and artifact upload.

Validated desk baseline:

```text
Implementation commit: 225c15b221c5e33728b7997e34ff9221e9606730
CI run: 30015603542
Version: 3.2.0-extended.4 / 320004
Application ID: com.clipcascade.extended
APK size: 93,636,243 bytes
APK SHA-256: af6fcf2b274c5bd57a08c2632fcb7efaa618dccab78250231b575c3006aefa48
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

The downloaded CI artifact was independently extracted. APK SHA-256, archive integrity report, Manifest, DEX/Hermes markers, OTP exclusion and upstream-update URL exclusion matched the CI evidence.

`3.2.0-extended.3` is a device-failed build and must not be used as an acceptance baseline.

## Upgrade-first install

1. Do **not** uninstall the existing `.3` Extended build.
2. Install `3.2.0-extended.4` / `320004` over `.3`.
3. Record any installer error instead of bypassing the test by uninstalling.
4. Verify the application ID remains `com.clipcascade.extended`.
5. Verify the signer SHA-256 remains the value above.
6. Verify server URL, username, settings, foreground-service requested state and retained permissions/app-ops.
7. Before changing any setup, run **fully automatic diagnostics** and copy the complete report.
8. Record Reliability Self-Test.
9. Perform a separate clean-install onboarding test only after the upgrade result is recorded.

## Product UI and localization gate

Test with Android language set to Japanese, English and Simplified Chinese.

For each language:

- login, advanced settings, synchronization, device setup, Self-Test and automatic diagnostics use the selected language consistently;
- dynamic connection/login/logout/error states are localized while technical exception detail remains available;
- notification channel names, connection-lost/restored notifications, received-file notifications and file-save errors are localized;
- ADB commands and diagnostics are selectable and one-tap copyable;
- dark mode and light mode both provide readable background/text contrast;
- `GITHUB`, `HELP`, `DONATE`, `HOMEPAGE`, `New version available!` and obsolete three-command ADB instructions are absent;
- no upstream update/metadata network request appears.

Any mixed inherited UI or unreadable dialog is a failure.

## Preferred ADB-free clipboard path

1. Open the app and use the direct Accessibility button.
2. Enable **ClipCascade copy detector**.
3. Confirm its description says window content is not retrieved.
4. Allow overlay through the direct app button.
5. Do not start Shizuku and do not connect PC ADB.
6. Connect to a known-good server.
7. Require `Connected` only after a real P2S transport or an open P2P DataChannel. P2P signaling alone must say it is waiting for a peer.

Test text from at least five unrelated source apps:

- browser;
- chat/messaging;
- notes/editor;
- document/PDF viewer;
- OEM/system app.

For each app:

- copy a unique text while Extended is hidden; require exactly one peer delivery;
- select text without copying; stale clipboard must not resend;
- perform rapid A→B→C copies; require correct order, no miss, no stale and no duplicate;
- copy the same text repeatedly, then alternate A/B/A/B;
- repeat after removing the UI from recents while the foreground service remains;
- repeat after process death/restart where Android permits;
- record Accessibility/coordinator/capture/outbound-queue state after any miss.

Repeat representative tests with English, Japanese, Simplified/Traditional Chinese and Korean copy feedback, rotation, battery saver and screen states where copying is possible.

## Android Share text path

Test all of the following while Extended is not already open:

- ordinary `text/plain` share;
- styled/Spanned text;
- HTML text share;
- MIME-less `ACTION_SEND` with `EXTRA_TEXT`;
- `ACTION_PROCESS_TEXT` from a text-selection menu.

Require:

- exactly one durable outbound item;
- no lost event before JavaScript listener readiness;
- automatic service start only when synchronization is requested;
- unsupported/empty intents clear `shared_payload_pending` rather than causing later phantom startup.

## Image clipboard and Android Share files

### Image clipboard

1. Copy an image from an app that exposes a readable clipboard URI.
2. Require the URI to be read while permission is valid and staged into Extended app-owned cache.
3. Require exactly one peer delivery with the correct image.
4. Repeat with Extended hidden, after removing UI from recents and after an idle interval.
5. Copy the same image repeatedly and then alternate two images; require duplicate suppression without suppressing a later legitimate value.
6. When an app/Android version does not expose a readable URI, require truthful diagnostic status rather than fabricated success.

### Android Share image/files

1. Use the source app's Android Share action and select ClipCascade Extended.
2. Test a single image, multiple images, a generic single file and multiple files.
3. Include a filename containing a comma and non-ASCII characters.
4. Test `CharSequence` text plus a stream when the source supplies both.
5. Test a moderately large file and a multiple-file batch.
6. Confirm app-owned staging status and exactly one delivery.
7. Confirm a rejected oversized/broken share leaves no partial batch and clears pending state.
8. Confirm old staged batches are cleaned after the retention period/app relaunch.
9. Confirm the localized failure Toast/dialog appears when staging or saving fails.

## Fully automatic diagnostics gate

Run once before setup changes and after every failure. Require the report to actively cover:

- native→React event probe;
- JS-listener readiness and durable native-event count;
- Accessibility state and last capture/coordinator status;
- foreground clipboard read, MIME types and URI count;
- outbound queue count/state/failure information;
- share pending/staging/cache files/cache bytes;
- foreground service requested state, heartbeat freshness, runtime instance, duplicate suppression, last loop failure and visible-copy recovery state;
- P2P candidate/compatible/incompatible peer counts and last compatibility error;
- Shizuku Binder/API/UID/authorization and actual READ_LOGS/overlay state;
- restart receiver state;
- raw status and native-probe JSON.

The report must be fully copyable. A stored flag without an active event/clipboard probe is insufficient.

## Transport and inbound matrix

Test both P2S and P2P where available.

### Android → peer

- short and long text;
- Japanese/emoji/combining-character payloads crossing fragment boundaries;
- offline copy followed by reconnect;
- P2S disconnect before self-echo, then reconnect;
- P2P peer disconnect during fragmented send;
- simultaneous bidirectional long text;
- multiple P2P peers receiving the same durable item;
- image clipboard;
- Android Share text/image/files.

Require authentication, encryption, size limits, durable ordering, truthful status, loop suppression and no avoidable duplicate.

### Peer → Android

- text, image and files;
- app visible, background and screen off where Android permits;
- repeated/alternating values;
- P2P overlapping fragmented messages from different peers;
- reconnect after peer sleep/wake.

Require correct clipboard/download behavior, no task wipe/restart loop and no false connection state.

### P2P compatibility / regression

- one Extended peer with matching encryption/key;
- one legacy upstream peer without compatibility metadata;
- one peer with encryption disabled when Extended has it enabled;
- one peer with a different key causing AEAD failure;
- several reconnects and peer departures.

Require:

- a legacy peer is not sent a proprietary clipboard control frame;
- optional compatibility fields in OFFER/ANSWER do not break the legacy peer;
- one decrypt-incompatible peer is quarantined without stopping compatible peers;
- quarantined peers are not repeatedly recreated or sent outbound data;
- `Peers` represents open compatible DataChannels, not signaling sessions or stale duplicate runtimes;
- AEAD BadTag does not repeat indefinitely for the same quarantined peer.

## Best fallback: guided Shizuku once

1. Press **Open / get Shizuku** in Extended.
2. If installed, require the Shizuku app to open.
3. If not installed, require the recommended `thedjchi/Shizuku` releases page to open.
4. Install/start Shizuku as guided, then return to Extended.
5. Press the one-time setup button.
6. Approve Extended in Shizuku.
7. Require successful remote command exit codes and local verification of READ_LOGS + overlay.
8. Confirm Self-Test reports `runtimeDependency=false` and `usage=one-time-setup-only`.
9. Stop Shizuku completely.
10. Repeat the five-app text, Share and representative image-clipboard tests; Shizuku being stopped must not break routine runtime.
11. Reboot without restarting Shizuku; recheck actual grants and retest.
12. Perform a later in-place update with Shizuku stopped and retest.
13. Deny/cancel authorization and allow the dialog/setup to time out; require no permanent BUSY state and no late setup work after failure.

Any routine clipboard/network operation that requires the Shizuku Binder is a failure.

## Second fallback: PC ADB once

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

1. Apply each command once.
2. Disconnect the PC.
3. Run the same five-app text and representative image/share matrix.
4. Reboot without ADB and retest.
5. Perform an in-place update and retest.
6. Revoke READ_LOGS and overlay separately; require truthful degraded status and no fabricated success.

## Lifecycle and restart matrix

- start sync and remove the UI from recents;
- background the app and verify the service continues;
- Android process kill;
- simulate/observe foreground runtime failure, then perform the next explicit copy and require visible-copy recovery;
- app force-stop, then explicit relaunch;
- reboot;
- package replacement `.3`→`.4`;
- Wi-Fi off/on, mobile data switch and airplane mode;
- P2S server restart;
- P2P peer sleep/wake and signaling reconnect;
- rotate during one-shot capture;
- trigger a second copy while capture is in flight;
- trigger capture launch failure/timeout if reproducible.

Require no permanent coordinator wedge, no duplicate overlay Activity, no event loss before JavaScript listener readiness, no multiple runtime leases and no old `Connected` state at startup.

## Stress and endurance

- 30-minute rapid-copy sequence with unique, repeated and alternating values;
- 8-hour idle/reconnect;
- P2S ACK timeout/reconnect cycles;
- simultaneous P2P send/receive of long multilingual text;
- multiple image clipboard and Android Share batches within staging limits;
- repeated service death/next-copy recovery where reproducible;
- battery use, wakeups, typing latency, task wipe/restart loops, ghost notifications and progressively heavier input.

Record a baseline with Accessibility disabled and compare typing latency/battery with the detector enabled.

## Deferred OTP phase

OTP notification-listener code is absent from the current core APK. Do not reintroduce it until every generic clipboard section above is green.

Later compare directly against `jd1378/otphelper` across Gmail, SMS/messaging, expanded notification fields, multiple codes, false positives, deduplication, privacy controls and app-specific rules.

## Failure evidence

Do not require a manually written long report when the automatic report is available. Record:

- complete copied automatic-diagnostics report;
- device and HONOR/Android build;
- Extended versionCode, signer and APK hash;
- install path: upgrade or clean;
- server mode/version and encryption setting;
- source/target app and payload pattern;
- timestamp and exact action;
- Self-Test before/after;
- actual permission/app-op screenshots when relevant;
- whether Shizuku was running, stopped or never started;
- focused ClipCascade, Accessibility, Clipboard, React, ActivityTaskManager and OEM-power logs only when the automatic report is insufficient;
- persistence after process restart, reboot and update.
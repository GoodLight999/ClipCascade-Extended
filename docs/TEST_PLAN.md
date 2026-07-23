# ClipCascade Extended — Reliability Test Plan

Compilation, self-test output and CI are not device acceptance.

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
- required reliability implementation DEX checks;
- checksum and artifact upload.

Validated desk baseline:

```text
Implementation/CI commit: 9beafea87393ee68d2e377addb6770f8cc95cdda
CI run: 29981770558
Version: 3.2.0-extended.3 / 320003
APK SHA-256: 07d2a7ebc864415026e39226763f824176f1e3a8d4bffc8b81c15aedf0dad4f0
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

## Upgrade-first install

1. Do **not** uninstall the existing Extended build.
2. Install `3.2.0-extended.3` / `320003` over `.2`.
3. Record any installer error rather than bypassing the test by uninstalling.
4. Verify the application ID remains `com.clipcascade.extended`.
5. Verify the signer SHA-256 remains the value above.
6. Verify server URL, username, settings, foreground-service state and all retained permissions/app-ops.
7. Record Reliability Self-Test before changing any setup.
8. Perform a separate clean-install onboarding test only after the upgrade test is recorded.

## Preferred ADB-free text path

1. Open the app and use the direct Accessibility button.
2. Enable **ClipCascade copy detector**.
3. Confirm its description says window content is not retrieved.
4. Allow overlay through the direct app button.
5. Do not start Shizuku and do not connect PC ADB.
6. Connect to a known-good server.
7. Require `Connected` only after a real P2S transport or an open P2P DataChannel. P2P signaling alone must say it is waiting for a peer.

Test at least five unrelated source apps:

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

### Non-text outbound boundary

Automatic clipboard capture is text-only. Clipboard image/file URIs are intentionally not queued because their read permission is commonly transient.

For Android→peer image/files:

1. Use the source app's Android Share action.
2. Select ClipCascade Extended.
3. Test a single image, multiple images and generic files.
4. Include a filename containing a comma and non-ASCII characters.
5. Test a moderately large file and a multiple-file batch.
6. Confirm app-owned staging status and exactly one delivery.
7. Confirm a rejected oversized/broken share leaves no partial batch.
8. Confirm old staged batches are cleaned after the retention period/app relaunch.

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
- Android Share image/files.

Require authentication, encryption, size limits, durable ordering, truthful status, loop suppression and no avoidable duplicate.

### Peer → Android

- text, image and files;
- app visible, background and screen off where Android permits;
- repeated/alternating values;
- P2P overlapping fragmented messages from different peers;
- reconnect after peer sleep/wake.

Require correct clipboard/download behavior, no task wipe/restart loop and no false connection state.

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
10. Repeat the five-app text matrix; Shizuku being stopped must not break routine runtime.
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
3. Run the same five-app text matrix.
4. Reboot without ADB and retest.
5. Perform an in-place update and retest.
6. Revoke READ_LOGS and overlay separately; require truthful degraded status and no fabricated success.

## Lifecycle and restart matrix

- start sync and remove the UI from recents;
- Android process kill;
- app force-stop, then explicit relaunch;
- reboot;
- package replacement `.2`→`.3`;
- Wi-Fi off/on, mobile data switch and airplane mode;
- P2S server restart;
- P2P peer sleep/wake and signaling reconnect;
- rotate during one-shot capture;
- trigger a second copy while capture is in flight;
- trigger capture launch failure/timeout if reproducible.

Require no permanent coordinator wedge, no duplicate overlay Activity, no event loss before JavaScript listener readiness and no old `Connected` state at startup.

## Stress and endurance

- 30-minute rapid-copy sequence with unique, repeated and alternating values;
- 8-hour idle/reconnect;
- P2S ACK timeout/reconnect cycles;
- simultaneous P2P send/receive of long multilingual text;
- multiple Android Share batches within staging limits;
- battery use, wakeups, typing latency, task wipe/restart loops, ghost notifications and progressively heavier input.

Record a baseline with Accessibility disabled and compare typing latency/battery with the detector enabled.

## Deferred OTP phase

OTP notification-listener code is absent from the current core APK. Do not reintroduce it until every generic clipboard section above is green.

Later compare directly against `jd1378/otphelper` across Gmail, SMS/messaging, expanded notification fields, multiple codes, false positives, deduplication, privacy controls and app-specific rules.

## Failure evidence

Record:

- device and HONOR/Android build;
- Extended versionCode, signer and APK hash;
- install path: upgrade or clean;
- server mode/version and encryption setting;
- source/target app and payload pattern;
- timestamp and exact action;
- Self-Test before/after;
- connection/outbound-queue/capture/shared-staging states;
- whether Shizuku was running, stopped or never started;
- actual permission/app-op screenshots;
- focused ClipCascade, Accessibility, Clipboard, React, ActivityTaskManager and OEM-power logs;
- persistence after process restart, reboot and update.

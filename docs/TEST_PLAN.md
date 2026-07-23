# ClipCascade Extended — Reliability Test Plan

Compilation/self-test output is not device acceptance.

## Automated gate

Every behavioral head must pass exact upstream materialization, guarded overlays, signing-key inspection, `npm ci`, ESLint, Jest, `testExtendedUnitTest`, `assembleExtended`, `apksigner verify`, checksum, and artifact upload.

## Upgrade-first install

1. Do not uninstall an existing Extended build.
2. Install `3.2.0-extended.2` / `320002` over it.
3. Verify configuration retention and signer SHA-256
   `2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd`.
4. Record Self-Test fields. Preserve installer errors instead of bypassing the test by uninstalling.
5. Later perform a separate clean-install onboarding test.

## Preferred ADB-free path

1. Enable **ClipCascade copy detector** via the in-app Accessibility button.
2. Confirm its description says window content is not retrieved.
3. Allow overlay through the in-app button.
4. Do not start Shizuku or use PC ADB.
5. Connect to a known-good server and confirm Connected is shown only after real transport connection.

Test at least five unrelated source apps: browser, chat, notes/editor, document viewer, and OEM/system app. For each:

- copy a unique text with Extended hidden; require exactly one peer delivery;
- select text without copying; stale clipboard must not resend;
- perform rapid A→B→C copies; require correct order/no miss/no stale/no duplicate;
- repeat after removing UI from recents while foreground service remains;
- record coordinator/capture status after any miss.

Repeat representative tests with English/Japanese/Chinese copy feedback, battery saver, rotation, and screen state where copying is possible. Image/file outbound remains through Android Share unless a device provides a reliable URI clipboard event.

## Transport/inbound matrix

Test P2S and P2P where available: Android→peer text copy, peer→Android text/image/files with app visible/background/screen off, and Android Share image/files. Verify authentication, encryption, size limits, truthful status, reconnect, loop suppression, and exactly-once behavior.

## Best fallback: Shizuku once

1. Start Shizuku once and press the in-app setup button.
2. Approve Extended.
3. Require successful command exit codes and local verification of READ_LOGS + overlay.
4. Stop Shizuku completely.
5. Repeat the five-app matrix; Shizuku being stopped must not break normal runtime.
6. Reboot without restarting Shizuku; recheck grants and retest.
7. Perform a later in-place update with Shizuku stopped and retest.

Any routine copy/network operation that requires the Shizuku Binder is a failure.

## Second choice: PC ADB once

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

Disconnect the PC, run the same matrix, reboot without ADB, perform an in-place update, then revoke each grant separately and require truthful degraded status.

## Stress/endurance

- 30-minute rapid-copy sequence with repeated/alternating values;
- process kill, swipe-away, reboot, Wi-Fi/mobile/airplane changes, peer sleep/wake;
- 8-hour idle/reconnect;
- battery, wakeups, typing latency, task wipe/restart loops, ghost notifications, and progressively heavier input.

## Deferred OTP phase

Do not expand OTP/SMS/email until all clipboard sections are green. Later compare directly against `jd1378/otphelper` across Gmail, SMS/messaging, expanded notification fields, multiple codes, false positives, deduplication, privacy controls, and app-specific rules.

## Failure evidence

Record device/OEM build, Extended version/signer/APK hash, server mode/version, source app, payload pattern, timestamp, Self-Test before/after, whether Shizuku was running/stopped/never started, permission screenshots, focused ClipCascade/Accessibility/Clipboard/React/ActivityTaskManager/OEM-power logs, and persistence after process restart/reboot/update.

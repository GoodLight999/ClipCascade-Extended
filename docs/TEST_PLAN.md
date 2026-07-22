# ClipCascade Extended — Reliability Test Plan

This document distinguishes automated evidence from checks that require a real
Android device and a live ClipCascade-compatible server. A design claim is not a
pass result.

## 1. Automated CI gate

Every pull request must pass all of the following in `.github/workflows/android-ci.yml`:

1. Fetch the exact upstream commit from `UPSTREAM.lock` and verify its SHA.
2. Apply every overlay and upstream repair with guarded markers.
3. Restore and inspect the fixed sideload signing key.
4. Run `npm ci` and `npm run lint`.
5. Run the React Native Jest render test.
6. Run `testExtendedUnitTest`, including OTP and clipboard-denial policy tests.
7. Run `assembleExtended` to produce a non-debuggable APK.
8. Verify the APK with `apksigner` and publish its SHA-256 checksum.
9. Upload the APK, checksum, and signer report as one artifact.

## 2. Fresh-install acceptance

Use the CI APK with package name `com.clipcascade.extended`.

1. Install the APK on a clean device.
2. Confirm the launcher name is **ClipCascade Extended**.
3. Grant notification permission when requested.
4. Open Android battery settings from the app and exempt ClipCascade Extended
   from aggressive power management.
5. Log in to a known-good ClipCascade server.
6. Verify that the app does **not** display “Connected” before a WebSocket or P2P
   transport has actually connected.
7. Open **Reliability Self-Test** and record every displayed field.

## 3. Core synchronization matrix

Run each case in P2S and P2P mode when both are available.

| Direction | Payload | App visible | App background | Screen off |
|---|---|---:|---:|---:|
| Android → peer | Text | Required | Required by share/OTP; generic copy uses fallback | Required by share/OTP; generic copy uses fallback |
| Peer → Android | Text | Required | Required | Required |
| Android → peer | Image | Required | Required through Android Share | Required through Android Share |
| Peer → Android | Image | Required | Required | Required |
| Android → peer | File(s) | Required | Required through Android Share | Required through Android Share |
| Peer → Android | File(s) | Required | Required | Required |

For every case, verify exactly-once delivery and confirm that the source payload
is not echoed back as a duplicate.

## 4. ADB-free OTP acceptance

1. Grant **Notification Access (OTP Sync)** from the app.
2. Start synchronization and background the app.
3. Receive an OTP notification from each available source:
   - Gmail
   - Beeper
   - Perceptron or another messaging client
4. Verify that only the 4–8 digit authentication code is sent.
5. Verify that an order number, tracking number, date, and ordinary chat message
   are not sent.
6. Repeat the same notification and verify the two-minute duplicate filter.
7. Stop synchronization and verify that subsequent OTP notifications are not sent.

## 5. Generic background clipboard fallback

Android 10+ does not provide ordinary background clipboard access to a normal
application. Manual Share and notification OTP capture remain the ADB-free paths.
For automatic generic-copy capture, the supported fallback is:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

Then:

1. Force-stop and reopen the app.
2. Start synchronization.
3. Confirm Self-Test reports `READ_LOGS fallback: true` and `Overlay fallback: true`.
4. Background the app, copy text in at least five unrelated applications, and
   verify exactly-once delivery without bringing ClipCascade to the foreground.
5. Revoke each permission separately and verify that Self-Test accurately reports
   the missing capability instead of claiming full operation.

Shizuku is an accepted future replacement or setup assistant for this fallback,
but no Shizuku API integration is claimed in the current build.

## 6. Lifecycle and endurance

1. Swipe the UI away while synchronization is active; verify foreground service
   reception remains operational.
2. Reboot the device; verify configured restart behavior and status accuracy.
3. Kill the process, reopen it, and verify queued native events are delivered once.
4. Run a 30-minute rapid-copy test and an 8-hour idle/reconnect test.
5. Toggle Wi-Fi/mobile data and suspend/resume the peer computer.
6. Verify no task wipe, launcher restart loop, duplicate tray/notification state,
   or progressively heavier text input.
7. Record battery consumption before and after the endurance run.

## 7. Upgrade and signature continuity

1. Install one Extended CI APK.
2. Install a later Extended CI APK without uninstalling the first.
3. Confirm Android performs an in-place update and retains configuration.
4. Verify the signer certificate SHA-256 remains:

```text
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

The Extended package has a distinct application ID and therefore is not an
in-place update of the upstream `com.clipcascade` package.

## 8. Failure evidence

For every failed device check, preserve:

- device manufacturer/model and Android build;
- server mode and server version;
- exact test step and timestamp;
- Reliability Self-Test output;
- foreground-service and connection notifications;
- `adb logcat` limited to ClipCascade, ClipboardService, ClipboardManager,
  ReactNativeJS, AndroidRuntime, and system power-management tags;
- whether the failure survives process restart and reboot.

# ClipCascade Extended — Canonical Handoff

Last materially updated: **2026-07-23 JST**

This file is the single continuation document. Do not reconstruct project state
from abandoned branches, archived repositories, old chat speculation, or CI
failures that have already been superseded here.

## 1. Repository and source authority

- Development repository: `GoodLight999/ClipCascade-Extended`
- Active branch: `stability-mobile-otp`
- Active draft PR: `#2 — Build a reliability-first Android client and standalone APK`
- Primary source: `Sathvik-Rao/ClipCascade`
- Android/Go historical reference: `wuxinkami/ClipCascade_go_fork`
- Permanently excluded: `GoodLight999/Trash-ClipCascade`

The excluded repository must not be imported, copied, migrated, tested as a
baseline, treated as a source of implementation facts, or described as a
canonical/archived original. It contains failed work and is irrelevant to the
current implementation.

Before using any repository, verify exact owner/name, archive status, stated role,
and the user's designation. Never promote an archived or ambiguously identified
repository to source-of-truth status.

## 2. User requirement that governs all choices

**Stable operation is the absolute requirement.** Eliminating ADB is a goal, not
permission to weaken reliability. The current hierarchy is:

1. ADB-free Android Share / Process Text for arbitrary outbound content.
2. ADB-free `NotificationListenerService` for OTP notifications.
3. ADB-free background inbound synchronization through the foreground service.
4. `READ_LOGS` plus overlay as the supported fallback for automatic generic
   background clipboard capture on Android 10+.
5. Shizuku may later replace or guide the fallback, but Shizuku is not presently
   implemented and must not be claimed as working.

Design documents alone are not completion. Every change must progress through
implementation, automated tests, CI, and APK generation, followed by real-device
acceptance when device access is available.

## 3. Reproducible upstream baseline

`UPSTREAM.lock` pins:

```text
Repository: Sathvik-Rao/ClipCascade
Commit: fd2cbbce69d5e5fa6b9b758d13a7dc6efdcb8a39
Mobile path: ClipCascade_Mobile/src
```

`scripts/materialize_upstream.sh` fetches only that commit, verifies the resulting
SHA, copies the mobile source, applies `scripts/apply_overlay.py`, and then applies
`scripts/fix_upstream_js.py`. Every source rewrite uses guarded markers so an
upstream drift fails loudly instead of producing a partial APK.

## 4. Implemented reliability changes

### Android task and lifecycle safety

- `ClipboardFloatingActivity` no longer uses `FLAG_ACTIVITY_CLEAR_TASK`.
- One-shot capture uses no-history/no-animation flags and always removes its
  overlay without recursive `finish()` behavior.
- `ScheduleService` health notifications reopen the existing task using
  `SINGLE_TOP | CLEAR_TOP`, never clear the task.
- Periodic WorkManager setup uses unique work with `KEEP` instead of a blocking
  main-thread query and replacement cycle.

### Native-event durability

`PendingReactEventStore.kt` persists a bounded FIFO queue when React Native is not
ready. It covers:

- Android Share / Process Text intents;
- notification OTP events;
- logcat/overlay clipboard fallback events.

The queue is drained after the native clipboard listener starts. A short
fingerprint window suppresses immediate duplicate enqueue operations.

### Generic background clipboard fallback

- Clipboard denial detection is isolated in `ClipboardAccessPolicy.kt` and unit
  tested against AOSP/OEM-style log lines.
- Logcat starts from recent entries with `-T 1` rather than a fragile formatted
  timestamp.
- Both `ClipboardService` and `ClipboardManager` tags are monitored.
- Only denial lines containing this package ID trigger one-shot capture.
- Status is persisted for Self-Test instead of pretending the fallback is active
  when `READ_LOGS` or overlay permission is missing.

Supported ADB setup:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

### ADB-free notification OTP path

`NotificationCaptureService.kt` extracts 4–8 digit codes only when a nearby
English, Japanese, Chinese, or Korean authentication keyword is present. It:

- reads title, text, expanded text, subtext, summary, and text lines;
- ignores the app's own notifications and group summaries;
- operates only while synchronization is requested;
- suppresses the same source/code for two minutes;
- queues the event if React Native is unavailable;
- records source package and code length in diagnostics without logging the code.

`OtpExtractorTest.kt` covers English, Japanese, Chinese, nearest-code selection,
and rejection of unrelated tracking/date numbers.

### UI and diagnostics

- Launcher/application name: `ClipCascade Extended`
- Application ID: `com.clipcascade.extended`
- Version: `3.2.0-extended.1` / versionCode `320001`
- Added **Notification Access (OTP Sync)** system-settings entry.
- Added **Reliability Self-Test**, reporting package, requested service state,
  connection text, notification access, `READ_LOGS`, overlay permission, pending
  native events, clipboard fallback status, and OTP capture status.
- All in-app ADB commands use the Extended package ID.

### Upstream correctness repairs

The pinned upstream JavaScript contained errors that prevented a strict build and
could affect runtime behavior. Guarded repairs now:

- declare session-validation, encryption-hash, and service-toggle variables;
- hash the actual `password_s` argument, including saved-password login, rather
  than the unrelated component state variable;
- replace `clearFiles((expensiveCall = true))` with `clearFiles(true)`;
- use the imported `text-encoding` namespace explicitly;
- use strict logout status comparison;
- document and narrowly suppress the intentional one-shot bootstrap hook warning.

## 5. CI and APK evidence

Green implementation commit:

```text
f948196bce539022ec047ab1b23de4b7712c418d
```

Complete successful workflow:

```text
Workflow: Android reliability CI
Run ID: 29965756451
```

The green run passed:

- exact upstream materialization and overlay drift checks;
- stable keystore restoration and alias inspection;
- `npm ci`;
- JavaScript/TypeScript ESLint;
- React Native Jest rendering test;
- Android `testExtendedUnitTest`;
- Android `assembleExtended`;
- `apksigner verify --verbose --print-certs`;
- checksum creation and artifact upload.

Validated APK:

```text
Filename: ClipCascade-Extended.apk
Size: 93,540,387 bytes
SHA-256: 23e798e0a6169bbf0b5904f304c2563fa0c87487d5c1ade8c9d902cf7648ecfb
Signing scheme: APK Signature Scheme v2
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signer key: RSA 3072-bit
```

The repository-pinned keystore is deliberately a public sideload continuity key,
not a secret trust credential. Its purpose is that later Extended CI builds can
update earlier Extended CI builds without uninstalling them.

## 6. What CI has not proven

Do not upgrade any of these to “working” until real-device evidence exists:

- connection to the user's actual P2S/P2P server and credentials;
- background behavior on the user's HONOR Android power-management build;
- Gmail, Beeper, and Perceptron notification payload variants;
- generic-copy fallback across OEM ClipboardService log formats;
- reboot relaunch behavior;
- long-duration battery use, reconnect behavior, and duplicate suppression;
- in-place update between two separately generated Extended APKs.

The current APK is compiled and automatically validated, not yet device-accepted.
`docs/TEST_PLAN.md` is the required acceptance matrix.

## 7. Immediate continuation order

1. Install the current APK without changing the code baseline.
2. Run fresh-install checks and capture Reliability Self-Test output.
3. Verify truthful disconnected/connected status against a live server.
4. Test background inbound text with UI hidden and screen off.
5. Test Android Share outbound text/image/file.
6. Grant Notification Access and test Gmail/Beeper/Perceptron OTP notifications.
7. Test unrelated numeric notifications to confirm no false send.
8. Only if generic copy is required, grant the documented ADB fallback and test
   at least five source applications.
9. Run process-kill, reboot, 30-minute rapid-copy, and 8-hour idle/reconnect tests.
10. Fix from preserved logs; do not replace the working architecture with a new
    speculative rewrite.

## 8. Branch and review discipline

- Keep PR #2 draft until real-device acceptance is recorded or the user explicitly
  chooses to merge the CI-complete baseline first.
- Do not create substitute branches merely to avoid a failing check; fix the
  active branch and preserve the diagnostic history.
- Do not delete or rewrite the green implementation evidence.
- Update this file whenever code behavior, upstream pin, CI state, package ID,
  signer, known limitations, or next-step ordering changes.

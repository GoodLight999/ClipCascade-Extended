# ClipCascade Extended — Canonical Handoff

Last updated: **2026-07-23 JST**

A new thread must resume from only:

> https://github.com/GoodLight999/ClipCascade-Extended ←これを引継いで開発して！

## Authority and active work

- Repository: `GoodLight999/ClipCascade-Extended`
- Branch: `stability-mobile-otp` (historical name; clipboard reliability is priority)
- Draft PR: `#2`
- Protocol/server authority: `Sathvik-Rao/ClipCascade`
- Primary Android behavior reference: `wuxinkami/ClipCascade_go_fork`
- Shizuku API: `RikkaApps/Shizuku-API`; optional user-facing fork: `thedjchi/Shizuku`
- Permanently excluded: `GoodLight999/Trash-ClipCascade`; never import, test, or derive facts from it.

## Non-negotiable requirements

1. Stable generic clipboard send/receive is the core product.
2. Preferred runtime is ADB-free: Accessibility Service + ordinary overlay permission.
3. Preferred privileged fallback setup is **Shizuku started once**, authorization and grants applied/verified, then Shizuku may stop.
4. Second choice is one-time PC ADB commands.
5. **Always-on Shizuku is forbidden as a normal requirement.** Routine clipboard/network runtime must not use its Binder.
6. Preserve full `Sathvik-Rao/ClipCascade` authentication, encryption, P2S/P2P, payload, and reconnect compatibility.
7. Setup guidance must cover English, Japanese, and Simplified Chinese.
8. Keep `com.clipcascade.extended`, the permanent signer, and increasing versionCode for in-place updates.
9. OTP/SMS/email is deferred until generic clipboard acceptance is green; later work must exceed `jd1378/otphelper` rather than add a superficial regex feature.

## Current implementation

`UPSTREAM.lock` pins `Sathvik-Rao/ClipCascade` commit
`fd2cbbce69d5e5fa6b9b758d13a7dc6efdcb8a39`, mobile path
`ClipCascade_Mobile/src`. Materialization verifies the SHA and applies guarded overlays.

Implemented ADB-free path:

- `ClipCascadeAccessibilityService` observes events outside Extended only while sync is requested.
- `CopySignalClassifier` recognizes explicit/localized copy feedback in English, Japanese, Chinese, and Korean, avoids generic-click triggering, and unit tests cover rejection/acceptance.
- `ClipboardCaptureCoordinator` persists the newest request, serializes overlay acquisition, retries launch failure, and preserves a newer request arriving during capture.
- `ClipboardFloatingActivity` performs one-shot 1x1 overlay focus acquisition, reads text/image/file URI payloads, cleans up in `finally`, and delivers or persists the React event.
- Accessibility and READ_LOGS-denial triggers share the same coordinator.
- Accessibility declares `canRetrieveWindowContent=false`.

Implemented one-time Shizuku setup:

- standard Shizuku API/provider `13.1.5`;
- Binder/API/UID/authorization detection and in-app authorization request;
- transient non-daemon AIDL UserService applies `READ_LOGS` and overlay app-op;
- every command exit code is checked;
- Extended polls its own real permission/app-op state and refuses to report success unless both are retained;
- synchronous Binder/command/verification work runs on a dedicated worker thread, not the UI thread;
- UserService is removed after setup; status explicitly reports `runtimeDependency=false` and `usage=one-time-setup-only`.

Setup UI includes direct Accessibility/overlay buttons, one-time Shizuku setup, PC ADB second-choice guidance, and Reliability Self-Test. OTP setup is not in the core flow.

Existing foundation retained: pending native-event FIFO, task/lifecycle corrections, truthful diagnostics scaffolding, guarded upstream JS fixes, stable signing, lint/Jest/Android tests, and signed APK CI.

## Current validated build

```text
Implementation commit: 257dc2d83f3f8d2f972c2b7f2dffdea2dc3bde84
CI run: 29970990520
Version: 3.2.0-extended.2
versionCode: 320002
Application ID: com.clipcascade.extended
APK size: 93,595,251 bytes
Run-specific APK SHA-256:
4951029a94a81485f54881aa1b3f16298d936515e9374b7d9a108c58649b4a19
Signing: APK Signature Scheme v2
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

Run `29970990520` passed exact materialization, signing-key inspection, `npm ci`, ESLint, Jest, `testExtendedUnitTest`, `assembleExtended`, `apksigner verify`, checksum, and artifact upload. APK hashes are per-run; bit-for-bit reproducibility is not claimed.

## Permission/update semantics

One-time Shizuku or PC ADB grants normally survive Shizuku stopping, reboot, and same-package/same-signer in-place updates. The app must still recheck actual state after startup/update. Uninstall, signer/package change, manifest removal, user/admin/OEM action, or permission reset may revoke them.

Second-choice commands:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

## Proof boundary

CI proves compilation, tests, packaging, and signature only. It has **not** proven HONOR/OEM Accessibility delivery, background Activity/overlay behavior, real Shizuku grant persistence, live user server compatibility, rapid-copy/endurance behavior, reboot recovery, battery impact, or actual `.1`→`.2` in-place update. Never claim these without device evidence.

## Immediate continuation

1. Install `.2` over the previous Extended APK without uninstalling when possible.
2. Verify configuration retention, signer/versionCode continuity, and actual grants.
3. Enable Accessibility + overlay; test ADB-free generic text copy from at least five apps with Extended hidden.
4. Test rapid A→B→C copies, selection-without-copy, duplicates, stale content, and typing latency.
5. Test live P2S/P2P truthfulness, inbound background/screen-off behavior, reconnect, process kill, and reboot.
6. Start Shizuku once, authorize/apply/verify, stop it, repeat tests, then reboot **without restarting Shizuku** and retest.
7. Test one-time PC ADB separately as second choice.
8. Run 30-minute rapid-copy and 8-hour idle/reconnect tests.
9. Preserve Self-Test/log evidence for failures; fix the existing architecture rather than speculative rewrites.
10. Keep OTP isolated until all generic clipboard gates are green.

`WORKLOG.md` is chronological evidence; `docs/TEST_PLAN.md` is the executable matrix. Keep PR #2 draft until real-device acceptance is recorded or the user explicitly changes merge strategy.

# ClipCascade Extended — 正本引継ぎ

Last updated: **2026-07-26 JST**

新しいスレッドでは、次の一文だけで本書とリポジトリを正本として再開する。

> https://github.com/GoodLight999/ClipCascade-Extended ←これを引継いで開発して！

## 1. Authority / active work

- Repository: `GoodLight999/ClipCascade-Extended`
- Active branch: `stability-mobile-otp`
- Draft PR: `#2`
- Package: `com.clipcascade.extended`
- Version: `3.2.0-extended.5` / versionCode `320005`
- Fixed signer certificate SHA-256: `2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd`
- Protocol/server authority: `Sathvik-Rao/ClipCascade`
- Android behavior reference: `wuxinkami/ClipCascade_go_fork`
- Shizuku API: `RikkaApps/Shizuku-API`
- Guided Shizuku distribution: `thedjchi/Shizuku`

過去の破綻した派生物、archive、trash、別リポジトリを資料として復活させない。一次資料は本リポジトリ、上記本家、Go版参考実装だけとする。

## 2. Current validated implementation

```text
Implementation commit: 751b8b4bec93a81ecab00c1df5a885b5c844c550
Successful CI run: 30191423570
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.5 / 320005
APK size: 93,681,991 bytes
APK SHA-256: 475d3c3f511852267710da5880c61955c247538701ada534aba2999d172c8b28
Signature: APK Signature Scheme v2
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

Run `30191423570` passed exact pinned-upstream materialization, every finalizer/validator, deterministic Extended build-resource source guard, dependency/repository audit, ESLint, every Jest suite, Android Lint, every Extended Kotlin test, release assembly, APK ZIP/zipalign/v2 signature/Manifest/DEX/Hermes/checksum and the packaged-resource reproducibility gate.

The packaged gate verified that `resources.arsc` contains the fixed loopback dev-server resource and no RFC1918 build-host address. This removes the prior GitHub-runner-IP-only APK hash drift without changing debug automatic discovery.

The identical signed APK passed API 35 and API 36 smoke: light/dark launch, text Share, `ACTION_PROCESS_TEXT`, cold-start real-PNG MediaStore Share, app-owned staging/native-event evidence, HOME/background PID survival and crash/ANR/known-regression scans. APK and both evidence archives were independently rechecked.

This is the first deterministic-resource build. The documentation-only build immediately following this update must reproduce the exact APK SHA-256 above; if it does not, reproducibility is not proven and this authority must be replaced.

## 3. Non-negotiable requirements

1. Generic Android clipboard synchronization is the core product.
2. Normal operation is ADB-free: Accessibility copy signal → serialized visible capture → clipboard read/staging → durable transport.
3. Shizuku is one-time setup only; routine capture/networking must work after it is stopped.
4. PC ADB is the second fallback and exposes only two selectable/copyable commands.
5. Text copy, Share/process text, image clipboard, image Share and single/multiple-file Share remain supported targets.
6. Upstream authentication, encryption, P2S/STOMP, P2P/WebRTC, server and desktop compatibility remain authoritative.
7. EN/JA/zh-CN cover complete UI, runtime state, diagnostics and notifications.
8. Light/dark mode remains readable; inherited footer/link/funding/update UI and update requests remain absent.
9. Fixed signer and monotonic versionCode preserve in-place updates.
10. OTP/SMS/email extraction remains absent until generic clipboard real-device acceptance.
11. Diagnostics exercise active paths rather than echoing flags.
12. Behavioral/evidence changes synchronize this file, `WORKLOG.md`, `README.md`, `docs/TEST_PLAN.md` and PR #2.

## 4. Source architecture / cleanliness

- Pin: `UPSTREAM.lock`
- Entry: `scripts/materialize_upstream.sh`
- Canonical overlay: `overlay/`
- Validators: `scripts/validate_*.py`
- CI: `.github/workflows/android-ci.yml`

Generate final design directly. Keep state machines in pure tested modules. Guard generated source and packaged APK separately. Failure artifacts retain generated runtime/policies/validators. Never weaken a guard merely to turn CI green; move it to the current contract.

The signed Extended build type overrides React Native 0.80.x's host-dependent dev-server resource with loopback. `validate_release_reproducibility.py` verifies both generated Gradle scope and packaged `resources.arsc`; debug builds retain automatic host discovery.

## 5. Clipboard acquisition

1. `ClipCascadeAccessibilityService` classifies explicit copy signals with `canRetrieveWindowContent=false`.
2. `ClipboardCaptureCoordinator` serializes requests.
3. `ClipboardFloatingActivity` supplies a short visible foreground-access window.
4. Temporarily empty/denied reads receive one bounded retry.
5. Text/readable URIs are read and staged while access is valid.
6. `PendingReactEventStore` persists until listener readiness and drains in order.
7. A stale requested runtime can recover from the next explicit visible copy.

READ_LOGS is optional fallback only. Ignored high-frequency events do not query AsyncStorage/SQLite.

## 6. Shizuku / ADB boundary

States:

- `already-configured`: retained grants verified; Shizuku may be stopped;
- `not-installed`: guided distribution action;
- `binder-pending`: startup Binder may still be arriving;
- `permission-required`: live Binder, Extended unauthorized;
- `ready-to-apply`: authorization present, one-time setup available.

Native setup handles sticky Binder, death, bounded wait, UserService lifecycle, exit codes and actual retained permission/app-op verification. Routine runtime source is statically forbidden from using Shizuku.

```text
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

## 7. Share / staged files

Handles `ACTION_SEND`, `ACTION_SEND_MULTIPLE`, `ACTION_PROCESS_TEXT`, `CharSequence`, Spanned/HTML and MIME-less text. Readable Content URIs are copied immediately to bounded app-owned FileProvider cache. JSON URI lists retain legacy decoding. Per-file/batch/cache limits, expiry, partial-failure cleanup and duplicate control are enforced. Logs contain event metadata, not payload content.

## 8. Durable transport

Queue is scoped by server mode + URL + username, serialized and lease-admission-checked. It survives offline/reconnect/process death and non-manual replacement. Explicit manual stop clears it. Delivery outcomes are explicit; ambiguous truthy ACK is rejected.

### P2S

- Wire body remains exactly `{payload, type}`.
- Standard STOMP `receipt`/`watchForReceipt` is primary ACK.
- Upstream self-echo is typed, identity-checked fallback.
- Late callbacks acknowledge only matching durable head.
- Receipt timeout is transient and retried, never permanent drop solely for missing ACK.
- Runtime ownership is rechecked immediately before `publish()`.
- Concurrent stop cancels receipt/echo state and returns WAITING.
- Inbound decrypt/malformed incidents are classified/coalesced and reset on success.

### Feedback

Global previous-content hash and untyped image boolean are absent. Typed expiring one-shot guards include mismatch and clock-rollback handling.

### P2P

Stable retry ID, UTF-8 fragmentation, bounded concurrent reassembly/conflict/replay/TTL/size/backpressure and explicit outcomes. Compatibility metadata appears only in OFFER/ANSWER. No proprietary DataChannel control frame/signaling type. Incompatible peers are quarantined individually.

## 9. Foreground runtime

- One Notifee handler and one network-runtime lease.
- All starts serialized by `runStartTransition`.
- Forced replacement waits up to 10 seconds for exact old lease.
- Start waits up to 8 seconds for an actual callback lease.
- Normal duplicate start joins active runtime.
- Five-second heartbeat, 15-second stale threshold and coordinated pending-Share recovery.
- WorkManager/boot/update/visible-copy recovery use explicit start intent.
- Poll/timer/host/signaling/peer work is supervised.
- Terminal state is written before lease release.

## 10. Product UI / diagnostics

Extended-owned login/settings/sync/setup/Self-Test/diagnostics, complete EN/JA/zh-CN, deterministic light/dark palettes, selectable one-tap-copy reports/ADB and no inherited update/link/funding UI.

Diagnostics actively cover native→React delivery, listener readiness, capture/clipboard MIME/URI, queue, Share staging/cache, runtime/heartbeat/recovery/errors, P2P compatibility/errors, P2S incidents and Shizuku/grants. Copied reports exclude secrets and endpoints.

## 11. Automated verification

Every behavioral head requires generation/validators, deterministic release-resource source and binary checks, dependency audit, ESLint/Jest, Android Lint/Kotlin/assembly, APK ZIP/zipalign/signature/Manifest/DEX/Hermes/checksum, packaged required/forbidden markers and API35/API36 smoke.

Smoke requires signed artifact install, light/dark screenshot/UI XML, text/process Share, real-PNG MediaStore cold-start Share with URI grant, staging/native-event evidence, HOME/background PID and no app crash/native crash/ANR/known React/StatusBar/foreground/AEAD marker.

## 12. Remaining real-device boundary

CI green is not product acceptance. Still required: HONOR 400 Pro in-place update; full real-device localization/light-dark review; Shizuku absent/pending/unauthorized/applied-stopped/post-reboot matrix; live upstream P2S/desktop and P2P interoperability; foreground/background/screen-off/Doze/network/process/reboot endurance; five-app copy matrix; ordering/duplicate/endurance/battery/wakeup/typing-latency evidence.

PR #2 stays Draft.

## 13. Continuation

1. Read this file and confirm branch/PR/head.
2. Inspect latest build/API35/API36 jobs.
3. Confirm the next documentation-only build reproduces APK SHA-256 `475d3c3f511852267710da5880c61955c247538701ada534aba2999d172c8b28` exactly.
4. On failure inspect generated source, checkpoint, summary, exit-info, logcat, screenshots/UI XML.
5. Reproduce in a pure test or deterministic emulator step first.
6. Never distribute an older APK after application-source changes.
7. After a new all-green behavioral run independently verify bytes/hash/signer/Manifest/markers/evidence.
8. Synchronize all documents and PR.

## 14. Definition of done

Requires latest behavioral generation/tests/APK/API35/API36 green, repeated identical APK generation, fixed-signer target-device upgrade, HONOR/live upstream bidirectional text/image/file, Shizuku-stopped/reboot operation, lifecycle endurance, real-device localization, secret-free diagnostics and synchronized documentation.

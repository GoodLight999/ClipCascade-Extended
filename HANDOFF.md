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

## 2. Current validated and reproducible artifact

```text
Application/build implementation commit: 3f7f01d36d19456bd741fb8b2e65b913cc4ddf34
Final harness head: ac34de11c73d4d565542b482739c2b3e5339b304
First deterministic build run: 30192487659
Second byte-identical build + full smoke run: 30192942851
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.5 / 320005
APK size: 93,673,799 bytes
APK SHA-256: 5911acfcba1e0e7a28b3e5cc13f268d5fbeb9c4c1653c9148d0954f8333e557c
Signature: APK Signature Scheme v2
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

Runs `30192487659` and `30192942851` were produced on separate hosted runners with unchanged Android build inputs. The signed APKs are identical under SHA-256 and `cmp`, including all 537 ZIP entries, central directory, v2 signer block and deterministic padding.

The reproducibility repair removes both non-deterministic inputs previously found by independent APK comparison:

1. React Native 0.80.x build-host IP injection is overridden only for the signed `extended` variant with loopback; debug automatic discovery remains intact.
2. Android Gradle Plugin SDK dependency information is excluded from APK/Bundle signing metadata because its encrypted signing-block payload changes between builds.

`validate_release_reproducibility.py` verifies the generated Gradle scope and rejects packaged RFC1918 build-host addresses or Signing Block pair `0x504b4453` before artifact upload. Final Signing Block pairs are v2 signature `0x7109871a` and deterministic padding `0x42726577` only.

Run `30192942851` passed exact pinned-upstream materialization, every finalizer/validator, deterministic-source and packaged-binary gates, dependency/repository audit, ESLint, every Jest suite, Android Lint, every Extended Kotlin test, release assembly, ZIP/zipalign/v2 signature/Manifest/DEX/Hermes/checksum, artifact upload and API 35/API 36 smoke.

Both emulator artifacts were independently checked: `checkpoint=passed`, exit code `0`, all summary fields passed, numeric MediaStore URI, image staging/native-event markers, background PID and no app crash/native crash/ANR/known regression. The earlier API 36 failure in Run `30192487659` was a transient `adb logcat -d` exit 255 during evidence collection; the app PID remained alive with no abnormal-exit record. The harness now records/retries transient logcat reads without suppressing genuine failures.

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

Every behavioral head requires generation/validators, deterministic release-resource source and Signing Block checks, dependency audit, ESLint/Jest, Android Lint/Kotlin/assembly, APK ZIP/zipalign/signature/Manifest/DEX/Hermes/checksum, packaged required/forbidden markers and API35/API36 smoke.

Smoke requires signed artifact install, light/dark screenshot/UI XML, text/process Share, real-PNG MediaStore cold-start Share with URI grant, staging/native-event evidence, HOME/background PID and no app crash/native crash/ANR/known React/StatusBar/foreground/AEAD marker. Transient ADB evidence reads are retried and each failed attempt remains in the artifact.

## 12. Remaining real-device boundary

CI green and reproducible APK do not establish product acceptance. Still required: HONOR 400 Pro in-place update; full real-device localization/light-dark review; Shizuku absent/pending/unauthorized/applied-stopped/post-reboot matrix; live upstream P2S/desktop and P2P interoperability; foreground/background/screen-off/Doze/network/process/reboot endurance; five-app copy matrix; ordering/duplicate/endurance/battery/wakeup/typing-latency evidence.

PR #2 stays Draft.

## 13. Continuation

1. Read this file and confirm branch/PR/head.
2. Inspect latest build/API35/API36 jobs.
3. Never distribute an APK whose SHA differs from the current authority after an Android-input change.
4. On failure inspect generated source, checkpoint, summary, exit-info, logcat attempts, screenshots/UI XML.
5. Reproduce in a pure test or deterministic emulator step first.
6. After a new all-green behavioral run independently verify bytes/hash/signer/Manifest/markers/evidence and repeated-build identity.
7. Synchronize all documents and PR.

## 14. Definition of done

Requires latest behavioral generation/tests/APK/API35/API36 green, repeated identical APK generation, fixed-signer target-device upgrade, HONOR/live upstream bidirectional text/image/file, Shizuku-stopped/reboot operation, lifecycle endurance, real-device localization, secret-free diagnostics and synchronized documentation.

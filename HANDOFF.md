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

Behavioral implementation authority:

```text
Implementation commit: 349003a994a0f05485a4f86605f9939abd4bcc98
Successful CI run: 30187796193
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.5 / 320005
APK size: 93,681,991 bytes
APK SHA-256: 19d2fad3ca85b4d0be7a15e3cb0042327c1d018e1ce33eb0c0281adef4aeb818
Signature: APK Signature Scheme v2
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

Run `30187796193` passed:

- exact pinned-upstream materialization and every finalizer/validator;
- `npm ci`, repository audit, ESLint and every Jest suite;
- Android Lint, every Extended Kotlin unit test and `assembleExtended`;
- ZIP integrity, zipalign, v2 signature, Manifest, DEX and Hermes assertions;
- packaged runtime coordinator, receipt, typed-feedback and queue-preservation markers;
- absence of OTP code, inherited update URLs/UI and obsolete transport markers;
- API 35 and API 36 release-APK emulator smoke.

Both emulator jobs installed the same signed APK and passed light launch, text Share, `ACTION_PROCESS_TEXT`, cold-start real-PNG MediaStore Share, app-owned staging/native-event evidence, HOME/background PID survival, dark launch, crash/ANR and known-regression scans. The downloaded APK and both evidence archives were independently rechecked.

Subsequent documentation and CI-assertion-only commits do not change the behavioral APK authority above. If application source changes, this section must be replaced with a new fully green build/API35/API36 authority.

## 3. Non-negotiable requirements

1. Generic Android clipboard synchronization is the core product.
2. Normal operation must be ADB-free: Accessibility copy signal → serialized visible capture → clipboard read/staging → durable transport.
3. Shizuku is a one-time permission/setup assistant. Routine capture and networking must work after Shizuku is fully stopped.
4. One-time PC ADB is the second fallback and exposes only two selectable/copyable commands.
5. Text copy, Share text/process text, image clipboard, image Share and single/multiple-file Share remain supported targets.
6. Upstream authentication, encryption, P2S/STOMP, P2P/WebRTC, server and desktop compatibility remain authoritative.
7. Japanese, English and Simplified Chinese must cover complete screens, runtime status, diagnostics and notifications.
8. Light/dark mode must remain readable; inherited update/funding/footer UI and update network calls stay absent.
9. Fixed signing identity and monotonically increasing versionCode preserve in-place updates.
10. OTP/SMS/email extraction stays absent until generic clipboard real-device acceptance is complete.
11. Automatic diagnostics must exercise active paths, not merely repeat stored flags.
12. Behavioral changes and evidence changes require synchronized updates to this file, `WORKLOG.md`, `README.md`, `docs/TEST_PLAN.md` and PR #2.

## 4. Source architecture and cleanliness

The repository reproducibly materializes a pinned upstream mobile tree, copies canonical overlay files and applies deterministic finalizers.

- Pin: `UPSTREAM.lock`
- Entry point: `scripts/materialize_upstream.sh`
- Canonical overlay: `overlay/`
- Validators: `scripts/validate_*.py`
- Android CI: `.github/workflows/android-ci.yml`

Rules:

- Generate the final design directly; do not add a later phase solely to undo a knowingly obsolete phase.
- Keep state machines in pure modules with Jest/Kotlin tests.
- Guard generated source and packaged APK markers separately.
- Failure artifacts must retain generated `App.js`, `StartForegroundService.js`, policies, validators and build reports.
- Never weaken a guard merely to make CI green; move it to the correct current contract.

## 5. Android clipboard acquisition

Primary path:

1. `ClipCascadeAccessibilityService` classifies localized explicit-copy signals without retrieving window content.
2. `ClipboardCaptureCoordinator` serializes requests and preserves newer work.
3. `ClipboardFloatingActivity` provides a short visible foreground-access window.
4. Empty/temporarily denied reads receive one bounded retry.
5. Text or readable clipboard URIs are read; URI bytes are staged while access is valid.
6. `PendingReactEventStore` persists native events until JavaScript listener readiness and drains them in order.
7. If synchronization remains requested but runtime heartbeat is stale, the next explicit visible copy can launch Headless recovery.

READ_LOGS is an optional signal fallback only. Ignored high-frequency Accessibility events must not query AsyncStorage/SQLite.

## 6. Shizuku / ADB setup boundary

`ShizukuSetupPolicy.js` separates:

- `already-configured`: retained READ_LOGS and overlay are already verified; Shizuku may be stopped;
- `not-installed`: open the guided distribution;
- `binder-pending`: installed/startup may still be delivering the Binder; native bounded waiting handles the race;
- `permission-required`: Binder is live but Extended is not authorized;
- `ready-to-apply`: authorization is present and one-time setup may run.

Native setup verifies sticky Binder receipt, Binder death, authorization, bounded UserService lifecycle, remote command exit codes and actual retained Android permission/app-op state. Routine runtime files are statically forbidden from referencing Shizuku.

PC fallback:

```text
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

## 7. Android Share and staged files

- Handles `ACTION_SEND`, `ACTION_SEND_MULTIPLE` and `ACTION_PROCESS_TEXT`.
- Accepts `CharSequence`, Spanned/HTML and MIME-less text where Android supplies text.
- Copies readable image/file Content URIs immediately into bounded app-owned FileProvider cache.
- Uses JSON URI lists while retaining legacy queue decoding.
- Enforces per-file, batch and total-cache bounds, expiry, partial-failure cleanup and duplicate control.
- Unsupported/empty intents clear pending state and cannot trigger a later phantom service start.
- Logs only event type/count/pending metadata, never payload content.

## 8. Durable transport

### Queue contract

- Queue scope is server mode + URL + username.
- Enqueue is serialized and admission-checked against the live runtime lease.
- Queue survives offline periods, reconnects, process death and non-manual runtime replacement.
- Explicit manual stop clears the queue; recovery/replacement/failure stops preserve it.
- Delivery adapters return explicit outcomes; ambiguous truthy values are rejected.

### P2S

- Keeps the upstream payload exactly `{payload, type}`; no proprietary delivery metadata is inserted.
- Uses standard STOMP `receipt` headers and `watchForReceipt` as the primary server-processing acknowledgement.
- Retains upstream self-echo as a compatibility fallback, matched by typed content fingerprint and queue-head identity.
- Late receipt/echo can acknowledge only the same durable head.
- Receipt timeout is transient and schedules retry; it never permanently drops an otherwise valid payload merely for lacking acknowledgement.
- Runtime ownership is rechecked immediately before irreversible `publish()`; a concurrent stop cancels receipt/echo state and returns WAITING.
- Inbound decrypt/malformed failures are classified and coalesced for 30 seconds, with counters and success reset.

### Feedback suppression

- Global previous-content hash and one-shot image boolean are absent.
- Typed one-shot guards include content fingerprint, expiry and clock-rollback handling.
- A mismatched next copy is not accidentally suppressed.

### P2P

- Retry ID is stable across attempts.
- UTF-8 fragmentation, concurrent peer/message accumulation, duplicate/conflict/TTL/size limits and DataChannel backpressure are bounded.
- Success and waiting results are explicit.
- Optional compatibility metadata appears only in upstream-forwarded OFFER/ANSWER fields.
- No proprietary DataChannel control frame or unsupported signaling type is sent.
- Incompatible/decrypt-failing peers are quarantined individually and excluded from outbound/recovery work.

## 9. Foreground runtime and recovery

- Exactly one Notifee handler and one JavaScript network-runtime lease are allowed.
- All starts are serialized through `runStartTransition`.
- Forced replacement requests the old runtime to stop and waits up to 10 seconds for that exact lease to finish.
- A start is not considered successful merely because a notification was displayed; it waits up to 8 seconds for an actual runtime lease.
- Duplicate normal starts join the existing runtime rather than stopping it.
- Instance ID, heartbeat, duplicate suppression, transition state and failures are persisted for diagnostics.
- Five-second heartbeat is stale after 15 seconds; pending Share recovery can force a coordinated replacement.
- WorkManager, boot/update and visible-copy recovery use explicit start intent, never stale-state toggling.
- Poll loops, timers, host callbacks, signaling and peer operations are supervised.
- Terminal state is written before lease release so an old runtime cannot overwrite the new runtime's state.

## 10. Product UI and diagnostics

- Extended-owned login, advanced settings, synchronization, setup, Self-Test and automatic diagnostics screens.
- Complete EN/JA/zh-CN dictionaries and localized notification resources.
- Deterministic light/dark palettes; contrast is covered by Jest and emulator screenshots.
- ADB commands and reports are selectable and one-tap copyable.
- No inherited GitHub/help/donate/homepage/footer/update prompt or update metadata request.

Automatic diagnostics actively covers native→React delivery, listener readiness, capture state, real foreground clipboard read/MIME/URI count, outbound queue, Share staging/cache, heartbeat/runtime/duplicate/recovery state, P2P peer compatibility/errors, P2S inbound incidents and Shizuku/grant state. Copied reports exclude credentials, user/server endpoints and key material.

## 11. Automated verification

Every behavioral head must pass:

1. canonical-source validation and exact pinned-upstream materialization;
2. all finalizers and architecture/forbidden-residue validators;
3. `npm ci`, repository audit, ESLint and Jest;
4. Android Lint, Kotlin tests and `assembleExtended`;
5. APK ZIP/zipalign/v2 signature/Manifest/DEX/Hermes/checksum checks;
6. packaged markers for runtime serialization, receipt/self-echo ACK, typed feedback, queue preservation and localization;
7. packaged absence of obsolete transport, OTP and inherited update markers;
8. API 35 and API 36 emulator smoke using the uploaded signed APK.

Emulator smoke requires:

- install with checksum verification;
- light/dark launch, screenshots and UI XML;
- text Share and `ACTION_PROCESS_TEXT` native-event evidence;
- a real PNG inserted into MediaStore and cold-start `ACTION_SEND image/png` with URI grant;
- app-owned staging and native-event evidence;
- HOME/background process survival;
- no app crash, native crash, ANR, known React/StatusBar/Foreground-Service regression or AEAD flood marker.

## 12. Real-device acceptance boundary

CI/emulator green is not product acceptance. Remaining evidence:

- in-place update on HONOR 400 Pro with configuration/grant retention;
- complete Japanese/English/Simplified-Chinese and light/dark visual acceptance;
- Shizuku absent, starting, unauthorized, authorized, applied-and-stopped and post-reboot states;
- live upstream P2S server and upstream desktop bidirectional text/image/file interoperability;
- live P2P with matching and mismatching encryption/key, peer departure and reconnect;
- foreground, HOME, screen off, Doze, network loss/recovery, process death and reboot;
- five-app Accessibility copy matrix, rapid/repeated/alternating copies and exact ordering;
- endurance, battery, wakeups and typing-latency comparison.

PR #2 stays Draft until these are recorded.

## 13. Immediate continuation procedure

1. Read this file and confirm branch/PR/head.
2. Inspect the latest CI build, API 35 and API 36 jobs.
3. For a failure, download its artifact and inspect checkpoint, summary, generated source, exit-info, logcat, screenshots and UI XML.
4. Reproduce the cause in a pure policy test or deterministic emulator step before changing implementation.
5. Never redistribute an older APK after application source changes.
6. After a new all-green behavioral run, independently verify bytes, SHA-256, signer, Manifest, packaged markers and both emulator evidence archives.
7. Synchronize all four documents and PR #2.

## 14. Definition of done

Completion requires all of the following:

- latest behavioral source passes generation, lint, Jest, Android tests and packaged-APK validation;
- API 35 and API 36 real-PNG smoke pass;
- fixed-signature upgrade succeeds on the target device;
- HONOR 400 Pro and live upstream server/desktop pass bidirectional text/image/file tests;
- one-time Shizuku setup works after Shizuku is completely stopped and after reboot;
- foreground/background/screen-off/reconnect/process-death/reboot endurance passes;
- localization and light/dark visual acceptance passes on real hardware;
- diagnostics correctly expose induced failures without secrets;
- this file, `WORKLOG.md`, `README.md`, `docs/TEST_PLAN.md` and PR #2 cite one coherent evidence state.

# ClipCascade Extended — Worklog

`HANDOFF.md` is the canonical current state. This file preserves concise chronological engineering evidence without serving as an alternative design authority.

## 2026-07-23 — Corrected product priority

The project priority was fixed as:

1. generic Android clipboard reliability;
2. ADB-free Accessibility copy path;
3. one-time guided Shizuku as the preferred fallback;
4. one-time PC ADB as the second fallback;
5. no always-on Shizuku runtime dependency;
6. OTP/SMS/email only after generic clipboard real-device acceptance.

Pinned upstream remains the protocol/server source. The Go-fork supplied evidence that Accessibility→visible overlay→clipboard could work in the background, but its broad click triggering, global debounce, dropped binding events, concurrent overlays and limited UX were not copied directly.

## 2026-07-23 — Accessibility and setup foundation

Implemented localized copy-signal classification, `canRetrieveWindowContent=false`, a serialized capture coordinator, visible transparent capture Activity, native event persistence before React readiness, optional READ_LOGS fallback, transient Shizuku UserService setup, retained-state verification, complete setup controls and fixed Extended signing continuity.

## 2026-07-23 — Extended.3 real-device rejection

`.3` passed its then-current desk gate but failed HONOR 400 Pro testing: unreadable dark diagnostics, inherited mixed UI, Shizuku misdetection, duplicated ADB guidance, broken foreground/Share/image/file paths, runtime loss, stale/multiplied peers, AEAD flood and events that never reached durable enqueue. `.3` remains device-failed and is not an acceptance baseline.

## 2026-07-23 to 2026-07-25 — Device-failure repair

### Capture / Share

- Registered JavaScript listeners before native event activation/drain.
- Added readiness probes, persistent ordered drain, bounded capture retry and watchdogs.
- Added clipboard URI staging while access is valid.
- Added `CharSequence`, Spanned/HTML, MIME-less text, process text, image and single/multiple-file Share.
- Added bounded cache, JSON URI lists, expiry and partial-failure cleanup.

### UI / diagnostics / Shizuku

- Replaced inherited partial UI with Extended-owned EN/JA/zh-CN screens.
- Removed footer, links/funding, update prompts and update/metadata requests.
- Added deterministic light/dark palettes, contrast tests and copyable reports/ADB.
- Added active clipboard/event probes and secret-free diagnostics.
- Added sticky Shizuku Binder, Binder-death handling, bounded wait and `binder-pending`.
- Verified real retained grants and statically excluded Shizuku from routine runtime code.

### P2P / runtime / queue

- Distinguished signaling from open compatible DataChannels.
- Added stable retry ID, UTF-8-safe fragments, bounded reassembly/backpressure and peer quarantine.
- Removed proprietary DataChannel control frames and unsupported signaling types.
- Added one Notifee handler, one network-runtime lease, heartbeat and supervised callbacks.
- Added durable server-scoped queue and preserved it on recovery/replacement/failure.

## 2026-07-25 to 2026-07-26 — Extended.5 completion

### Runtime ownership

- Extracted `ForegroundRuntimeCoordinator`.
- Serialized starts through `runStartTransition`.
- Forced replacement waits up to 10 seconds for exact old-lease completion.
- Start success waits up to 8 seconds for an actual callback lease.
- Duplicate normal starts join the current runtime.
- Terminal state is persisted before lease release.
- WorkManager recovery became an explicit start rather than a stale-state toggle.

### P2S receipt and retry

The earlier proprietary delivery-metadata approach was removed. Final wire body remains exactly `{payload, type}`.

- Standard STOMP `receipt`/`watchForReceipt` is primary acknowledgement.
- Upstream self-echo is an identity-checked fallback.
- Late callbacks may acknowledge only the matching durable head.
- Receipt timeout is transient and retried, not a permanent drop.
- Early receipt is rechecked after send completion.
- Runtime ownership is rechecked immediately before `publish()`.
- Concurrent stop cancels receipt/echo state and returns WAITING.

### Explicit delivery / feedback

- Added tested delivery policy/executor with explicit WAITING/SENT/AWAITING_RECEIPT/FEEDBACK/POLICY outcomes.
- Rejected ambiguous truthy ACKs.
- Replaced global previous-content hash and untyped image flag with typed expiring one-shot guards.
- Added clock-rollback and mismatched-next-copy tests.

### Guards

- Rewrote generated-source validators for the current contracts.
- Deleted obsolete ACK source/finalizer/tests.
- Expanded failure artifacts.
- Expanded packaged Hermes checks to require coordinator/receipt/feedback/queue markers and reject obsolete transport markers.

## 2026-07-26 — Reproducible signed APK repair

Independent comparison of fully green APKs found two non-runtime causes of hash drift.

### Build-host resource

All DEX/Hermes/Manifest/native/assets were equal, but `resources.arsc` contained a GitHub-runner private address injected by React Native 0.80.x. The signed `extended` build type now overrides only `react_native_dev_server_ip` with loopback; debug keeps automatic discovery. Source and binary validators require correct scope and reject RFC1918 addresses.

### SDK dependency Signing Block

After the resource fix, all 537 ZIP entries and central directory were equal, but Signing Block pair `0x504b4453` differed. This was Android Gradle Plugin SDK dependency information, whose encrypted payload varies per build. The Android DSL now sets:

```groovy
dependenciesInfo {
    includeInApk = false
    includeInBundle = false
}
```

The structural APK parser rejects `0x504b4453`. Final Signing Block pairs are v2 signature `0x7109871a` and deterministic padding `0x42726577` only.

### Evidence-collector hardening

The first fully deterministic APK passed API 35, while API 36 stopped because `adb logcat -d` transiently returned exit 255 during evidence capture. The app PID was alive and exit-info contained no abnormal exit. Logcat collection now retries up to three times, preserves failed attempts and waits briefly for delayed positive markers without masking genuine crash/ANR checks.

## 2026-07-26 — Byte-identical final candidate

```text
Application/build implementation commit: 3f7f01d36d19456bd741fb8b2e65b913cc4ddf34
Final harness head: ac34de11c73d4d565542b482739c2b3e5339b304
First deterministic build run: 30192487659
Second byte-identical build + complete smoke run: 30192942851
Version: 3.2.0-extended.5 / 320005
Application ID: com.clipcascade.extended
APK size: 93,673,799 bytes
APK SHA-256: 5911acfcba1e0e7a28b3e5cc13f268d5fbeb9c4c1653c9148d0954f8333e557c
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

The two APKs were compared independently: same size and SHA-256, `cmp` identical, same 537 entry names/content, and identical v2 signer/padding pair hashes.

Run `30192942851` passed exact materialization, all source/binary validators, dependency/repository audit, ESLint, every Jest suite, Android Lint, every Extended Kotlin test, release assembly, ZIP/zipalign, v2 signature, Manifest/DEX/Hermes/checksum, artifact upload and API 35/API 36 smoke.

Both emulator evidence archives contained `checkpoint=passed`, exit code `0`, all summary fields passed, numeric MediaStore URI, image staging/native-event evidence, background PID and no app/native crash, ANR or known regression marker. API 36 completed without requiring a retry in the final run.

## Remaining acceptance boundary

Still required: HONOR 400 Pro in-place update; complete real-device localization/light-dark review; Shizuku absent/pending/unauthorized/applied-stopped/post-reboot matrix; live upstream P2S/desktop and P2P interoperability; foreground/background/screen-off/Doze/network/process/reboot endurance; five-app copy matrix; ordering/duplicate/endurance/battery/wakeup/typing-latency evidence.

OTP remains deferred. PR #2 remains Draft until the real-device/live-server matrix is recorded.

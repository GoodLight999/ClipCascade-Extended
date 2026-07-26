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

## 2026-07-26 — Automated release-candidate evidence

```text
Implementation commit: 349003a994a0f05485a4f86605f9939abd4bcc98
Successful CI run: 30187796193
Version: 3.2.0-extended.5 / 320005
Application ID: com.clipcascade.extended
APK size: 93,681,991 bytes
APK SHA-256: 19d2fad3ca85b4d0be7a15e3cb0042327c1d018e1ce33eb0c0281adef4aeb818
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

Run `30187796193` passed exact materialization, all validators, dependency/repository audit, ESLint, every Jest suite, Android Lint, every Extended Kotlin test, release assembly, ZIP/zipalign, v2 signature, Manifest/DEX/Hermes/checksum and artifact upload.

The same signed APK passed API 35 and API 36 smoke: light/dark launch, text Share, process text, real-PNG MediaStore cold-start Share with URI grant, app-owned staging/native-event evidence, HOME/background process survival and crash/ANR/known-regression scans. Both emitted `checkpoint=passed` and exit code `0`.

The downloaded APK and both evidence archives were independently checked. Hash, size, signer, Manifest identity, required markers and forbidden obsolete/OTP/update markers matched.

Documentation and packaged-APK assertions were synchronized afterward without changing application behavior. The artifact authority remains the implementation/run/hash above until a behavioral-source change requires a replacement.

## Remaining acceptance boundary

Still required: HONOR 400 Pro in-place update; complete real-device localization/light-dark review; Shizuku absent/pending/unauthorized/applied-stopped/post-reboot matrix; live upstream P2S/desktop and P2P interoperability; foreground/background/screen-off/Doze/network/process/reboot endurance; five-app copy matrix; ordering/duplicate/endurance/battery/wakeup/typing-latency evidence.

OTP remains deferred. PR #2 remains Draft until the real-device/live-server matrix is recorded.

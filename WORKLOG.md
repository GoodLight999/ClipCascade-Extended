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

Implemented:

- localized copy-signal classification;
- Accessibility with `canRetrieveWindowContent=false`;
- persistent serialized capture coordinator;
- transparent visible capture Activity;
- native event persistence before React listener readiness;
- READ_LOGS signal as an optional fallback;
- transient Shizuku AIDL UserService for one-time READ_LOGS/overlay setup;
- command exit-code and retained Android-state verification;
- direct EN/JA/zh-CN setup controls and PC ADB fallback;
- fixed Extended package/signing continuity.

## 2026-07-23 — Extended.3 desk audit and real-device rejection

The `.3` source passed its then-current CI gate, but HONOR 400 Pro testing rejected it. Observed failures included:

- unreadable dark-mode diagnostics;
- inherited English/footer/update UI;
- Shizuku authorization misdetection;
- duplicated/non-copyable ADB guidance;
- broken foreground send/receive and Share paths;
- image/file failures;
- foreground runtime loss after backgrounding;
- stale/multiplied peers and repeated AEAD BadTag;
- capture events that never reached the durable outbound queue.

`.3` remains device-failed and forbidden as an acceptance baseline.

## 2026-07-23 to 2026-07-25 — Device-failure repair

### Capture and native-event delivery

- Registered JavaScript listeners before activating/draining native events.
- Added explicit readiness, ordered persistent drain and active native→React diagnostics.
- Added bounded capture retry, launch/destruction watchdog and rollback-safe scheduling.
- Added clipboard URI staging while permission is valid.
- Expanded Share handling to `CharSequence`, Spanned/HTML, MIME-less text, process text, image and single/multiple files.
- Added bounded app-owned cache, JSON URI lists, expiry and partial-failure cleanup.

### Product UI and diagnostics

- Replaced inherited partial UI with Extended-owned login/settings/sync/setup/diagnostic screens.
- Removed upstream footer, external links/funding, update prompts and update/metadata requests.
- Added complete Japanese, English and Simplified-Chinese dictionaries and native notification resources.
- Added deterministic light/dark palettes and contrast tests.
- Made ADB guidance and reports selectable and one-tap copyable.
- Added active clipboard/event probes and secret-free incident reporting.

### Shizuku boundary

- Added sticky Binder delivery, Binder death handling and bounded startup wait.
- Added `binder-pending` so an installed/starting Shizuku instance is not falsely treated as absent.
- Verified actual retained READ_LOGS/overlay state and deleted the transient UserService after setup.
- Added static guards forbidding routine capture/network source from using Shizuku.

### P2P

- Distinguished signaling from open compatible DataChannels.
- Added stable retry identity, UTF-8-safe fragmentation, bounded concurrent reassembly, duplicate/conflict/TTL controls and backpressure.
- Removed proprietary DataChannel control frames and unsupported signaling types.
- Limited optional compatibility metadata to OFFER/ANSWER.
- Quarantined incompatible/decrypt-failing peers individually.

### Foreground runtime and queue

- Added one registered Notifee handler and one network-runtime lease.
- Added persisted service intent, bounded stop, five-second heartbeat and stale-runtime recovery.
- Supervised polling, timers, host callbacks, signaling and peer operations.
- Added durable server-scoped outbound queue and serialized admission.
- Preserved queue on replacement/failure/recovery; explicit manual stop alone clears it.
- Added Headless recovery from boot, package replacement and visible-copy recovery.

## 2026-07-25 to 2026-07-26 — Extended.5 transport/runtime completion

A deeper generated-code audit found additional races that ordinary green builds did not prove.

### Runtime ownership

- Extracted `ForegroundRuntimeCoordinator`.
- Serialized every service start through `runStartTransition`.
- Forced replacement now requests the exact old runtime to stop and waits up to 10 seconds for lease completion.
- Start success now waits up to 8 seconds for an actual Notifee callback lease instead of trusting notification display.
- Duplicate normal starts join the existing runtime.
- Terminal state is persisted before lease release so an old runtime cannot overwrite a replacement's state.
- WorkManager recovery became an explicit start instead of a stale-state toggle.

### P2S acknowledgement and retry

The earlier proprietary delivery-metadata/self-echo design was removed.

Final contract:

- upstream wire body remains exactly `{payload, type}`;
- standard STOMP `receipt`/`watchForReceipt` is the primary acknowledgement;
- upstream self-echo remains an identity-checked compatibility fallback;
- late callbacks can acknowledge only the matching durable queue head;
- receipt timeout is transient and schedules retry rather than permanently dropping valid work;
- an early receipt is rechecked after send completion so the same flush can continue;
- runtime ownership is checked immediately before irreversible `publish()`;
- a concurrent stop cancels receipt/echo state and returns explicit WAITING.

### Explicit delivery and feedback

- Added `OutboundDeliveryPolicy` and `OutboundDeliveryExecutor`.
- P2S/P2P return explicit WAITING/SENT/AWAITING_RECEIPT/FEEDBACK/POLICY outcomes.
- Invalid truthy values are rejected instead of silently acknowledging queue heads.
- Replaced global previous-content hash and untyped image boolean with typed, expiring one-shot guards.
- Clock rollback and mismatched-copy behavior are tested.

### Generated-source and APK guards

- Rewrote validators around the current ownership/receipt contracts.
- Deleted obsolete ACK source/finalizer/tests instead of leaving dead alternatives.
- Failure artifacts now retain generated runtime/policy/validator files.
- Packaged Hermes validation requires coordinator, receipt, feedback and queue-preservation markers and forbids obsolete transport markers.

## 2026-07-26 — Automated release candidate evidence

Behavioral implementation commit:

```text
349003a994a0f05485a4f86605f9939abd4bcc98
```

Successful CI run:

```text
30187796193
```

Artifact:

```text
Version: 3.2.0-extended.5
versionCode: 320005
Application ID: com.clipcascade.extended
APK size: 93,681,991 bytes
APK SHA-256: 19d2fad3ca85b4d0be7a15e3cb0042327c1d018e1ce33eb0c0281adef4aeb818
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

Run `30187796193` passed:

- exact materialization and all finalizers/validators;
- dependency/repository audit, ESLint and all Jest suites;
- Android Lint, all Extended Kotlin tests and release assembly;
- ZIP integrity, zipalign, v2 signature, Manifest, DEX/Hermes and checksum checks;
- API 35 and API 36 release-APK smoke.

The emulator matrix exercised light/dark launch, text Share, process text, a real PNG inserted into MediaStore and cold-start shared with URI grant, app-owned staging/native-event evidence, HOME/background process survival and crash/ANR/known-regression scans. Both jobs emitted `checkpoint=passed` and exit code `0`.

The downloaded APK was independently checked. Hash, size, signer, Manifest identity, required runtime/receipt/feedback markers and forbidden obsolete/OTP/update markers matched. Both emulator evidence archives were independently inspected.

Documentation and packaged-APK CI assertions were then synchronized to this evidence without changing application behavior. The artifact authority remains the implementation/run/hash above unless application source changes and a new three-job green run replaces it.

## Remaining acceptance boundary

This is a strong automated device-test candidate, not final product acceptance. Still required:

- HONOR 400 Pro in-place update and retained settings/grants;
- complete real-device EN/JA/zh-CN and light/dark visual review;
- Shizuku absent/pending/unauthorized/applied-and-stopped/post-reboot matrix;
- live upstream P2S server and upstream desktop bidirectional text/image/file tests;
- live P2P matching/mismatching encryption/key and peer lifecycle tests;
- foreground/background/screen-off/Doze/network/process/reboot endurance;
- five-app Accessibility copy matrix, rapid ordering and duplicate behavior;
- battery, wakeups and typing-latency evidence.

OTP remains deferred. PR #2 remains Draft until the real-device/live-server matrix is recorded.

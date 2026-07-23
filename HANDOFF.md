# ClipCascade Extended — Canonical Handoff

Last updated: **2026-07-23 JST**

A new thread must resume from only:

> https://github.com/GoodLight999/ClipCascade-Extended ←これを引継いで開発して！

## Authority and active work

- Repository: `GoodLight999/ClipCascade-Extended`
- Branch: `stability-mobile-otp` (historical name; generic clipboard reliability is the product priority)
- Draft PR: `#2`
- Protocol/server authority: `Sathvik-Rao/ClipCascade`
- Primary Android behavior reference: `wuxinkami/ClipCascade_go_fork`
- Shizuku API: `RikkaApps/Shizuku-API`; recommended guided user-facing fork: `thedjchi/Shizuku`
- Permanently excluded: `GoodLight999/Trash-ClipCascade`; never import, inspect, cite, test, or derive facts from it.

## Non-negotiable requirements

1. Stable generic clipboard synchronization is the core product.
2. Preferred text-copy runtime is ADB-free: Accessibility copy signal + ordinary overlay permission.
3. Preferred privileged fallback is Shizuku started once, authorization/grants applied and verified, after which Shizuku may stop.
4. One-time PC ADB is the second fallback.
5. Routine clipboard/network runtime must never require an always-running Shizuku Binder.
6. Preserve upstream authentication, encryption, P2S/P2P, payload and reconnect compatibility.
7. Setup guidance must support English, Japanese and Simplified Chinese.
8. Preserve `com.clipcascade.extended`, the permanent signer and monotonic versionCode for in-place updates.
9. OTP/SMS/email stays deferred until the generic clipboard device matrix is green; later work must target superiority over `jd1378/otphelper`, not a superficial regex feature.

## Current implementation

`UPSTREAM.lock` pins `Sathvik-Rao/ClipCascade` commit
`fd2cbbce69d5e5fa6b9b758d13a7dc6efdcb8a39`, path
`ClipCascade_Mobile/src`. Materialization verifies the exact SHA and applies guarded overlays/finalizers.

### Upstream + Go-fork combination

Upstream remains authoritative for authentication, encryption, P2S/STOMP, P2P/WebRTC, inbound text/image/files, server settings and protocol compatibility.

The successful Go-fork Android concept is reproduced and hardened:

```text
Accessibility copy feedback
→ persistent serialized capture request
→ one-shot transparent overlay/focus
→ text clipboard read
→ persistent native event
→ durable upstream-compatible transport
```

The Go-fork weaknesses were not copied: generic-click capture, one global debounce, dropped service-binding triggers, unbounded/concurrent overlays and Chinese-only onboarding were replaced.

### ADB-free capture reliability

- `ClipCascadeAccessibilityService` ignores Extended's own package and only acts on explicit/localized copy feedback.
- `CopySignalClassifier` covers English, Japanese, Simplified/Traditional Chinese and Korean copy feedback; selection-only events are rejected.
- The Accessibility XML no longer subscribes to selection-change events and declares `canRetrieveWindowContent=false`.
- Frequent ignored Accessibility events do not touch AsyncStorage/SQLite. Sync-request state uses a tested 250 ms monotonic cache.
- `ClipboardCaptureCoordinator` persists the newest request, serializes acquisition, has a launch watchdog, retries finite failures and ignores stale Activity completions.
- `ClipboardFloatingActivity` always removes the overlay in `finally` and preserves the React event when JavaScript is not ready.
- Accessibility and READ_LOGS-denial fallback triggers share the same coordinator.
- Automatic clipboard capture is intentionally text-only. Transient image/file clipboard URIs are rejected with a truthful `nontext-clipboard-use-android-share` status.
- Image/file outbound uses Android Share and immediately streams content into bounded app-owned cache.

### Durable events and transport

- Native events are queued persistently until the JavaScript listener explicitly activates and drains them.
- Outbound items are server/mode/user scoped, bounded, persisted across process death and expired after a finite retention period.
- Consecutive duplicate copies coalesce; manual stop clears the queue; transport loss retains it.
- P2S embeds the durable queue ID in existing `metadata.extendedDeliveryId`; the queue item remains until the server self-echoes that ID.
- P2S has timeout/backoff and accepts a late matching echo by checking the durable queue head, preventing needless duplicate retransmission.
- P2P uses a stable queue ID across retries, UTF-8-safe fragmentation, peer/message-scoped concurrent accumulation, replay/conflict bounds and DataChannel backpressure timeouts.
- P2P status distinguishes signaling-only from an actually open peer DataChannel. Generic signaling traffic cannot restore a false `Connected` state.
- Boot/package-replacement Headless JS startup takes the required WakeLock.

### Shared image/file safety

- Android Share URIs are copied immediately into `cache/shared_outbound` and exposed through Extended's FileProvider.
- URI lists use JSON arrays; legacy comma-separated queued entries remain readable.
- Limits: 64 files, 512 MiB per file, 512 MiB per batch and 768 MiB total staging cache.
- Partial failed batches are removed and expired batches are cleaned on staging/app launch.

### One-time Shizuku / ADB fallback

- Standard Shizuku API/provider `13.1.5` with transient non-daemon AIDL UserService.
- The app detects Binder/API/server UID/authorization, requests authorization, checks every command exit code and verifies its actual retained READ_LOGS and overlay states.
- Setup work runs off the UI thread and rejects stale/late UserService connections after timeout or disconnect.
- Verification uses monotonic time. UserService is removed after setup.
- Status explicitly reports `runtimeDependency=false` and `usage=one-time-setup-only`.
- Guided button opens installed Shizuku; if absent, it opens the recommended `thedjchi/Shizuku` releases page. EN/JA/zh-CN text instructs the user to start Shizuku, return and press one-time setup.
- PC ADB commands remain visible as the second choice.

### OTP boundary

OTP is not merely hidden: the notification-listener Service, extraction class and tests are absent from the canonical overlay and generated app. CI rejects the notification-listener permission/Service and OTP classes in both Manifest and DEX.

## Current validated build

```text
Validated implementation/CI commit: 9beafea87393ee68d2e377addb6770f8cc95cdda
CI run: 29981770558
Version: 3.2.0-extended.3
versionCode: 320003
Application ID: com.clipcascade.extended
APK size: 93,611,651 bytes
APK SHA-256:
07d2a7ebc864415026e39226763f824176f1e3a8d4bffc8b81c15aedf0dad4f0
Signing: APK Signature Scheme v2
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

Run `29981770558` passed:

- exact pinned-upstream materialization and final-scope invariants;
- OTP exclusion and runtime-Shizuku-boundary checks;
- stable signing-key inspection;
- `npm ci`, ESLint and all Jest suites;
- Android Lint and all Extended Kotlin unit tests;
- `assembleExtended`;
- APK ZIP integrity and zipalign;
- APK Signature Scheme v2 verification;
- Manifest package/version/Accessibility/READ_LOGS/overlay/Shizuku API checks;
- non-debuggable, OTP-free Manifest/DEX checks;
- required reliability implementation strings in DEX;
- checksum generation and artifact upload.

APK hashes are run-specific; bit-for-bit reproducibility is not claimed.

## Permission/update semantics

One-time Shizuku or PC ADB grants normally survive Shizuku stopping, reboot and same-package/same-signer in-place updates, but Extended rechecks actual state. Uninstall, signer/package change, manifest removal, user/admin/OEM action or permission reset may revoke them.

Second-choice commands:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

## Exact proof boundary

The **currently identifiable and automatable desk/static gates are green** for the validated code. This does not prove that no latent defect exists.

The following product requirements are still unproven and must not be called complete without HONOR 400 Pro / real-server evidence:

- OEM Accessibility delivery while Extended is hidden;
- one-shot overlay clipboard access under HONOR background restrictions;
- real P2S/P2P interoperability and exactly-once behavior;
- Shizuku-applied grant persistence after Shizuku stop, reboot and update;
- process kill/swipe-away/reboot recovery;
- rapid-copy ordering and long-idle reconnect;
- battery/wakeup/typing-latency impact;
- actual `.2` → `.3` in-place update and settings retention.

## Immediate continuation

1. Install `.3` over `.2` without uninstalling.
2. Record versionCode, signer continuity, settings retention and Self-Test before changing any permissions.
3. Test the pure ADB-free text path from at least five unrelated apps with Extended hidden.
4. Test selection-without-copy, rapid A→B→C, repeated values, app removal from recents and truthful connection states.
5. Test live P2S/P2P, inbound text/image/files, Android Share image/files, reconnect, process kill and reboot.
6. Use the guided Shizuku open/get flow, apply one-time setup, stop Shizuku, repeat tests, reboot without restarting Shizuku and retest.
7. Test one-time PC ADB separately as the second fallback.
8. Run 30-minute rapid-copy and 8-hour idle/reconnect tests, recording battery and typing latency.
9. Preserve Self-Test/log evidence for every miss. Fix the current architecture rather than speculative rewrites.
10. Keep OTP excluded until all generic clipboard device gates are green.

`WORKLOG.md` is chronological evidence and `docs/TEST_PLAN.md` is the executable matrix. Keep PR #2 draft until real-device acceptance is recorded or the user explicitly changes merge strategy.

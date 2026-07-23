# ClipCascade Extended — Worklog

`HANDOFF.md` is the canonical current state. This file preserves chronological engineering evidence.

## 2026-07-23 — Requirement correction

The prior CI-green baseline incorrectly prioritized notification OTP and lacked the Go-fork Accessibility path and Shizuku integration. It was reclassified as a build/lifecycle baseline. Correct priority:

1. generic clipboard reliability;
2. ADB-free Accessibility runtime;
3. one-time Shizuku setup as best fallback;
4. one-time PC ADB as second choice;
5. no always-on Shizuku dependency;
6. OTP/SMS/email only after clipboard acceptance and only as an otphelper superior.

Inspected Go-fork files: Accessibility Service, background service, manifest and accessibility XML. Preserved its event→overlay→read concept, but rejected broad click triggering, one global debounce, service-binding drops, non-serialized overlays, weak loop state and Chinese-only UX.

Correction/documentation commits:

```text
22bd17ca8d97a468b0286dc18c14cbb3752f7e4c
369da2478c6107fda139db1ef75fa7bf708d1937
```

## 2026-07-23 — Accessibility and one-time Shizuku implementation

Implemented:

- localized copy-signal classifier and tests;
- Accessibility Service with `canRetrieveWindowContent=false`;
- persistent serialized capture coordinator with retry/newer-request preservation;
- one-shot overlay Activity and React-not-ready event persistence;
- unified Accessibility and READ_LOGS trigger serialization;
- English/Japanese/Simplified-Chinese setup resources/buttons;
- Shizuku API/provider 13.1.5, AIDL and transient non-daemon UserService;
- in-app authorization and one-time READ_LOGS/overlay application;
- strict command exit-code checking plus Extended-side polling of actual retained grants;
- Shizuku Binder/command/verification work moved to a dedicated worker thread to avoid UI blocking/ANR;
- PC ADB explicitly second choice;
- version `3.2.0-extended.2`, versionCode `320002`, package/signer unchanged.

Implementation commits:

```text
6a01c89889d16c43004706f239e6a4694a071cf1  Accessibility/Shizuku
9d240b08d40a067f3c340f98f2e1a8b771459541  version/UserService correction
9a7dd08e4fb343f6c3946911adbea3dd168e42cf  unified capture serialization
886c155e56187c0b814460c095857845e6a52b1e  strict Shizuku verification
257dc2d83f3f8d2f972c2b7f2dffdea2dc3bde84  Shizuku setup off UI thread
```

CI run `29970990520` passed the earlier `.2` source/npm/test/build/signing gate. It was not considered final device evidence.

## 2026-07-23 — Extended.3 desk reliability audit

The `.2` implementation was not accepted as “all desk debugging complete.” A deeper audit found and fixed the following concrete defects and risk paths:

### Capture/event lifecycle

- Selection-change events could trigger stale clipboard transmission without a real copy.
- React Context existence was incorrectly treated as proof that the JavaScript listener was ready.
- Capture Activity launch/creation failure and Activity destruction could permanently wedge serialization.
- Re-registering the listener could clear a genuinely in-flight capture and launch a duplicate Activity.
- Accessibility ignored-event traffic could synchronously query SQLite and increase typing latency.
- The first sync-state cache attempt contained a monotonic-time overflow bug; state caching was extracted into `SyncRequestCache` and covered by first-read/expiry/rollback/invalidate tests.
- Boot/package replacement startup lacked the required Headless JS WakeLock.

### Transport durability and truthfulness

- Unconnected P2S/P2P copies could be discarded instead of retained.
- Outbound “sent” hashes were committed before transport success, preventing retries.
- P2P UTF-8 byte slicing could corrupt Japanese and emoji at fragment boundaries.
- P2P `forEach(async ...)` lost DataChannel errors.
- P2P send startup erased in-progress receive fragments; inbound traffic could interrupt outbound traffic.
- One global receive-fragment state could corrupt concurrent peer/message deliveries.
- P2P retries generated new message IDs and could duplicate delivery to peers that received an earlier partial attempt.
- DataChannel buffered amount had no bound/backpressure timeout.
- P2S removed queue entries after local `publish()` rather than server receipt.
- P2S now waits for server self-echo of existing `metadata.extendedDeliveryId`; timeout/backoff and late matching echo are handled.
- P2P signaling messages could restore generic `Connected` despite no open peer DataChannel.

### Shared image/file reliability

- ACTION_SEND `content://` grants could expire before React/transport processing.
- File URI lists were comma-delimited, so commas in names/URIs could split one item into several.
- File staging had no batch/total cache limits.
- Android Share now stages bytes immediately into app-owned FileProvider cache with JSON URI arrays, legacy parsing compatibility, cleanup and bounded file/batch/cache sizes.
- Automatic clipboard URI outbound was removed; image/file outbound is Android Share only because clipboard URI permission lifetime is not durable.

### Shizuku/ADB fallback

- Permission/setup timeout states could remain busy or allow late UserService work after the UI had already failed.
- Connection generation is now rechecked before remote execution and throughout verification.
- Verification uses monotonic time and actual Extended permission/app-op state.
- The app can open installed Shizuku or, if missing, open the recommended `thedjchi/Shizuku` releases page; EN/JA/zh-CN guidance instructs the user to return for one-time setup.
- Runtime files are statically forbidden from referencing Shizuku.

### OTP isolation

- OTP had been hidden from the main flow but its notification listener/extractor still existed.
- Notification listener Service, extractor and tests were deleted from the canonical overlay.
- Generated Manifest/NativeBridge remnants are removed by finalization.
- CI rejects notification-listener permission/Service and OTP class strings in Manifest/DEX.

### Build/CI hardening

- React Native 0.80.2 may add Sonatype Snapshot broadly when bundled Hermes is classified as a snapshot, causing stable dependencies such as Guava to query an unstable repository.
- The official Gradle plugin source is patched after `npm ci` so the snapshot repository only includes `com.facebook.react` and `com.facebook.hermes`; CI audits those filters.
- Added Android Lint, guarded final-scope checks, ZIP integrity, zipalign, non-debuggable Manifest, Shizuku API contract, OTP absence and required DEX implementation checks.
- Failure artifacts now retain materialization and generated source diagnostics.

## 2026-07-23 — Validated Extended.3 artifact

Validated implementation/CI commit:

```text
9beafea87393ee68d2e377addb6770f8cc95cdda
```

Successful CI run:

```text
29981770558
```

The run passed exact source materialization, repository scoping/audit, signing-key inspection, ESLint, all Jest suites, Android Lint, all Extended Kotlin tests, `assembleExtended`, ZIP/zipalign, APK Signature Scheme v2, Manifest/DEX assertions, OTP absence, checksum and artifact upload.

```text
Version: 3.2.0-extended.3
versionCode: 320003
Application ID: com.clipcascade.extended
APK size: 93,611,651 bytes
APK SHA-256: 07d2a7ebc864415026e39226763f824176f1e3a8d4bffc8b81c15aedf0dad4f0
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

Desk/static status: all currently identified and automatable gates are green for this code. This is not a proof that no latent defect exists.

Device proof boundary remains unchanged: HONOR/OEM Accessibility delivery, background overlay behavior, live user-server compatibility, real Shizuku grant persistence, rapid-copy/endurance, reboot/update recovery, battery impact, typing latency and actual `.2`→`.3` update require real-device evidence. Next engineering work is device acceptance and evidence-driven correction, not OTP expansion.

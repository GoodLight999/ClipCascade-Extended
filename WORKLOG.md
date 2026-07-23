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
- Automatic clipboard URI outbound was removed because clipboard URI permission lifetime was not considered durable at that stage.

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
- Failure artifacts retain materialization and generated source diagnostics.

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

This desk success was later superseded by real-device failure and is not product acceptance evidence.

## 2026-07-23 — Extended.3 HONOR 400 Pro rejection

Real-device testing disproved the `.3` completion assumptions:

- dark-mode Self-Test was unreadable;
- inherited English UI/footer/update elements remained;
- Shizuku authorization was misdetected;
- ADB guidance was duplicated and not copyable;
- foreground text send/receive and Android Share failed;
- image clipboard/image/file paths failed;
- Foreground Service stopped during background transition;
- `Peers: 21` and repeated AEAD BadTag failures appeared;
- capture looked queued while the outbound queue remained empty.

`.3` was marked **device-failed and forbidden as a test baseline**. The old statement that no desk-identifiable problem remained was removed from the canonical handoff.

## 2026-07-23 — Extended.4 device-failure repair

Concrete repairs added after the device report:

### Event and capture delivery

- Registered native/React listeners before enabling durable native-event drain.
- Added explicit listener-readiness state and active native→React diagnostic probe.
- Added clipboard URI staging to app-owned cache, including image clipboard support.
- Expanded Android Share handling to `CharSequence`, Spanned, HTML, MIME-less text, process text, image, single file and multiple files.
- Cleared pending share state for unsupported intents.

### Foreground runtime

- Enforced one registered foreground handler and one network runtime lease.
- Replaced stale React-state toggle decisions with persisted `wsIsRunning` state.
- Added bounded service-stop waiting, 5-second heartbeat and stale-heartbeat diagnosis.
- Supervised the polling loop and guaranteed cleanup/release after loop failure.
- Added next-copy recovery: when sync is requested and the heartbeat is stale, the visible transparent capture Activity starts Headless JS recovery, with a retry guard and recorded result.

### P2P compatibility

- Quarantined decrypt-incompatible peers instead of poisoning the entire room.
- Removed proprietary DataChannel control frames and a signaling message type that the upstream server did not forward.
- Embedded optional compatibility metadata in upstream-forwarded OFFER/ANSWER fields.
- Excluded quarantined peers from transport recovery and outbound sends.

### Product UI and diagnostics

- Replaced inherited partial UI with Extended-owned login, advanced settings, sync and setup screens.
- Removed upstream footer, update/metadata fetches and obsolete ADB guidance.
- Added adaptive Android colors.
- Unified screen labels, dynamic statuses, diagnostics, notification titles/channels and file-save dialogs across Japanese, English and Simplified Chinese.
- Kept technical exception detail and raw JSON unmodified.
- Made ADB instructions and diagnostic output selectable and one-tap copyable.

### CI corrections found during the repair

- Fixed an escaped-newline marker bug in the localization finalizer.
- Corrected Android Share validation markers.
- Corrected notification replacement counts across P2S/P2P formatting variants.
- Split release APK validation correctly: Kotlin/native evidence in DEX and JavaScript evidence in the Hermes bytecode bundle.
- Kept Japanese source-string validation in materialization/Jest and validated stable localization keys in the release Hermes bundle.

## 2026-07-23 — Validated Extended.4 artifact

Validated implementation commit:

```text
225c15b221c5e33728b7997e34ff9221e9606730
```

Successful CI run:

```text
30015603542
```

The run passed exact materialization and all finalizers, architecture invariants, signing-key inspection, `npm ci`, ESLint, all Jest suites, Android Lint, all Extended Kotlin tests, `assembleExtended`, APK ZIP integrity, zipalign, APK Signature Scheme v2, Manifest checks, non-debuggable/OTP-free checks, native DEX assertions, release Hermes assertions, checksum and artifact upload.

```text
Version: 3.2.0-extended.4
versionCode: 320004
Application ID: com.clipcascade.extended
APK size: 93,636,243 bytes
APK SHA-256: af6fcf2b274c5bd57a08c2632fcb7efaa618dccab78250231b575c3006aefa48
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

After downloading the CI artifact, the APK was independently extracted and checked. SHA-256 matched the CI checksum. ZIP integrity, Manifest package/version/permissions/components, required DEX and Hermes markers, OTP exclusion and upstream update/metadata URL exclusion matched the CI evidence.

Desk/static status: the current `.4` implementation and packaged APK pass the presently defined automated gates. This does not establish device acceptance. HONOR 400 Pro upgrade behavior, OEM background clipboard access, real P2S/P2P interoperability, Shizuku grant persistence, exactly-once behavior, process/reboot recovery, endurance, battery impact and typing latency remain device evidence tasks. OTP remains deferred.
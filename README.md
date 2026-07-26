# ClipCascade Extended

Reliability-first Android client for servers compatible with [`Sathvik-Rao/ClipCascade`](https://github.com/Sathvik-Rao/ClipCascade).

## Runtime/setup order

1. **ADB-free primary path:** Accessibility copy signal → serialized visible capture → clipboard read/staging → durable upstream-compatible transport.
2. **Android Share:** text, process text, image and files are staged immediately where required, then durably queued.
3. **Preferred privileged fallback:** use Shizuku once to apply and verify retained grants, then stop it completely.
4. **Second fallback:** run two PC ADB commands once.
5. Routine runtime has no always-on Shizuku dependency.
6. OTP/SMS/email extraction remains absent until generic clipboard real-device acceptance.

Extended includes Accessibility/overlay controls, guided Shizuku setup, copyable ADB guidance, Reliability Self-Test and active diagnostics. UI, runtime state, diagnostics and notifications support English, Japanese and Simplified Chinese.

## Reliability design

- Pinned upstream remains authoritative for authentication, encryption, P2S/STOMP, P2P/WebRTC, inbound text/image/files and server compatibility.
- Android capture follows the proven Accessibility→visible overlay→clipboard concept in `wuxinkami/ClipCascade_go_fork`, replacing broad clicks, selection false positives, global debounce, dropped binding events and concurrent overlays with tested classification, persistent ordering and watchdog coordination.
- Accessibility uses `canRetrieveWindowContent=false`; ignored high-frequency events avoid storage work.
- `UPSTREAM.lock` + `scripts/materialize_upstream.sh` generate the app from canonical `overlay/` source and deterministic finalizers.

Capture/Share:

- listeners register before native durable-event activation/drain;
- bounded launch/retry/destruction/timeout recovery;
- text and readable clipboard URIs share one native reader, with immediate app-owned staging;
- MIME-less/Spanned/HTML text, process text, image and single/multiple-file Share;
- JSON URI lists, legacy decoding, size/cache/expiry/partial-failure controls.

Durable transport:

- server-scoped queue survives offline/reconnect/process death;
- non-manual replacement/failure preserves work; explicit manual stop clears it;
- explicit delivery outcomes reject ambiguous truthy ACKs.

P2S keeps exact upstream `{payload, type}` body. Standard STOMP `receipt` is primary ACK, with identity-checked upstream self-echo fallback. Late callbacks may acknowledge only the matching durable head. Timeout is transient. Runtime ownership is checked again immediately before `publish()`. Typed expiring feedback guards replace the old global hash/image flag.

P2P uses stable retry IDs, UTF-8-safe fragments, bounded concurrent reassembly/replay/conflict/TTL/backpressure and individual peer quarantine. Optional compatibility metadata travels only in OFFER/ANSWER; no proprietary clipboard control frame is sent.

Foreground runtime:

- one Notifee handler and one network-runtime lease;
- serialized starts;
- forced replacement waits up to 10 seconds for exact old lease;
- startup waits up to 8 seconds for a real callback lease;
- five-second heartbeat/15-second stale threshold;
- explicit WorkManager/boot/update/visible-copy recovery and supervised callbacks.

Shizuku:

- transient UserService for setup only;
- sticky Binder/death/authorization/bounded-start/exit-code handling;
- real retained grant verification and truthful `binder-pending` state;
- CI forbids routine capture/network Shizuku use.

Product integrity:

- Extended-owned complete EN/JA/zh-CN UI and deterministic light/dark palettes;
- selectable/copyable reports and ADB;
- no inherited footer/link/funding/update UI or update requests;
- no OTP notification-listener/extractor code.

## Reproducible signed APK

The signed `extended` variant removes two build-only sources of APK drift:

- React Native 0.80.x build-host IP injection is overridden with loopback only for the signed variant; debug automatic discovery remains unchanged.
- Android Gradle Plugin SDK dependency information is excluded from the APK/Bundle signing metadata.

CI validates both the generated Gradle scope and the packaged APK. It rejects RFC1918 build-host addresses and SDK dependency Signing Block pair `0x504b4453` before artifact upload.

Two separate hosted-runner builds produced byte-identical signed APKs, including all ZIP entries, central directory, v2 signer block and padding:

```text
Application/build implementation commit: 3f7f01d36d19456bd741fb8b2e65b913cc4ddf34
Final harness head: ac34de11c73d4d565542b482739c2b3e5339b304
First deterministic build run: 30192487659
Second identical build and full smoke run: 30192942851
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.5 / 320005
APK size: 93,673,799 bytes
APK SHA-256: 5911acfcba1e0e7a28b3e5cc13f268d5fbeb9c4c1653c9148d0954f8333e557c
Signature: APK Signature Scheme v2
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

Run `30192942851` passed exact materialization, every validator, dependency/repository audit, ESLint/Jest, Android Lint/Kotlin tests, release assembly, ZIP/zipalign/signature/Manifest/DEX/Hermes/checksum, reproducibility gates, artifact upload, API 35 smoke and API 36 smoke.

Both emulator evidence archives independently showed `checkpoint=passed`, exit code `0`, all summary fields passed, numeric MediaStore URI, image staging/native-event evidence, background PID and no app crash/native crash/ANR/known regression.

## Build

```bash
./scripts/materialize_upstream.sh
cd build/mobile
npm ci
python3 ../../scripts/patch_react_native_snapshot_repository.py .
npm run lint
npm test -- --runInBand
cd android
./gradlew lintExtended testExtendedUnitTest assembleExtended
```

Output:

```text
build/mobile/android/app/build/outputs/apk/extended/app-extended.apk
```

## One-time fallback

Preferred: open/get Shizuku from Extended, authorize/apply, verify Self-Test, then stop Shizuku completely.

Second choice:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

This remains an automated device-test candidate, not final product acceptance. HONOR 400 Pro upgrade/OEM behavior, live upstream P2S/P2P/desktop interoperability, Shizuku stop/reboot retention, lifecycle endurance, battery and typing latency remain required. PR #2 stays Draft.

See `HANDOFF.md`, `WORKLOG.md` and `docs/TEST_PLAN.md`. `.3` remains device-failed and is not a baseline.

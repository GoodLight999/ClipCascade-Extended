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
- `UPSTREAM.lock` + `scripts/materialize_upstream.sh` reproducibly generate the app from canonical `overlay/` source and deterministic finalizers.
- The signed Extended variant overrides React Native 0.80.x's build-host dev-server resource with loopback. Source and packaged-APK guards reject missing scope or any RFC1918 runner address while leaving debug automatic discovery unchanged.

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

## Validated deterministic candidate

```text
Implementation commit: 751b8b4bec93a81ecab00c1df5a885b5c844c550
Successful CI run: 30191423570
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.5 / 320005
APK size: 93,681,991 bytes
APK SHA-256: 475d3c3f511852267710da5880c61955c247538701ada534aba2999d172c8b28
Signature: APK Signature Scheme v2
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

Run `30191423570` passed exact materialization, all validators including deterministic resource scope, dependency/repository audit, ESLint/Jest, Android Lint/Kotlin tests, release assembly, ZIP/zipalign/signature/Manifest/DEX/Hermes/checksum, private-build-host-IP rejection and artifact upload.

The identical signed APK passed API 35 and API 36 smoke: light/dark launch, text Share, process text, cold-start real-PNG MediaStore Share with staging/native-event evidence, HOME/background PID survival and crash/ANR/known-regression scans. APK and evidence were independently rechecked.

This is the first deterministic-resource build. The documentation-only build following this update must reproduce the exact hash above before reproducibility is considered proven.

This remains a strong automated device-test candidate, not final product acceptance. HONOR 400 Pro upgrade/OEM behavior, live upstream P2S/P2P/desktop interoperability, Shizuku stop/reboot retention, lifecycle endurance, battery and typing latency remain required. PR #2 stays Draft.

See `HANDOFF.md`, `WORKLOG.md` and `docs/TEST_PLAN.md`. `.3` remains device-failed and is not a baseline.

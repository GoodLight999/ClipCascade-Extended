# ClipCascade Extended

Reliability-first Android client for servers compatible with
[`Sathvik-Rao/ClipCascade`](https://github.com/Sathvik-Rao/ClipCascade).

## Runtime/setup order

1. **ADB-free text runtime:** Accessibility copy signal → persistent serialized one-shot overlay → text clipboard read → durable upstream-compatible transport.
2. **Image/file outbound:** Android Share → immediate bounded app-cache staging → durable transport.
3. **Best privileged fallback:** open/get Shizuku from Extended, start it once, authorize/apply/verify grants, then stop Shizuku.
4. **Second fallback:** run PC ADB commands once.
5. Always-on Shizuku is intentionally not a runtime requirement.

The app provides direct Accessibility/overlay buttons, guided Shizuku open/install and one-time setup, PC ADB guidance and Reliability Self-Test. Core setup text supports English, Japanese and Simplified Chinese.

## Upstream + Go-fork architecture

- Authentication, encryption, P2S/STOMP, P2P/WebRTC, inbound text/image/files and server compatibility remain based on pinned `Sathvik-Rao/ClipCascade` source.
- The Android capture mechanism is based on the successful concept in `wuxinkami/ClipCascade_go_fork`.
- Generic clicks, selection-only capture, global debounce, dropped service-binding triggers, concurrent overlays and fragile state are replaced by a localized classifier, persistent event queue and serialized watchdog-protected coordinator.
- Accessibility declares `canRetrieveWindowContent=false` and ignored high-frequency events do not query AsyncStorage/SQLite.

## Reliability changes

- Native events persist until the JavaScript listener explicitly becomes ready.
- Text copies persist through process death/offline periods in a bounded server-scoped outbound queue.
- P2S keeps an item until the server self-echoes its durable delivery ID; timeout, backoff and late ACK are handled.
- P2P uses stable retry IDs, UTF-8-safe fragmentation, concurrent peer/message reassembly, replay/conflict limits and DataChannel backpressure.
- P2P signaling-only and actual peer connection states are distinct; startup never inherits an old success state.
- One-shot overlay Activity launch/destruction/timeout cannot permanently wedge subsequent copies.
- Boot and package-replacement Headless JS startup takes the required WakeLock.
- Android Share content is copied immediately into bounded app-owned cache. URI lists use JSON; old comma-separated queue entries remain readable.
- Automatic clipboard URI outbound is disabled because image/file URI permission lifetime is not reliably durable. Use Android Share for non-text outbound.
- Shizuku uses a transient UserService only for setup; command exit codes and actual retained grants are verified before success.
- Shizuku timeout/disconnect generations are guarded so late UserService work cannot continue after failure.
- OTP notification-listener/extractor code is absent from the core source and APK. CI rejects its reintroduction.

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

APK: `build/mobile/android/app/build/outputs/apk/extended/app-extended.apk`

```text
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.3 / versionCode 320003
Signer SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

## One-time fallback

Preferred:

1. Press **Open / get Shizuku** in Extended.
2. Start Shizuku, return to Extended and press the one-time setup button.
3. Verify Self-Test, then stop Shizuku.

Second choice:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

A same-package/same-signer in-place update normally retains configuration and grants, but Extended rechecks actual state. Uninstalling resets them.

## Validated desk artifact

```text
Validated implementation/CI commit: 9beafea87393ee68d2e377addb6770f8cc95cdda
CI run: 29981770558
APK size: 93,611,651 bytes
APK SHA-256: 07d2a7ebc864415026e39226763f824176f1e3a8d4bffc8b81c15aedf0dad4f0
Signature: APK Signature Scheme v2
```

The run passed exact materialization, repository scoping/audit, ESLint, all Jest suites, Android Lint, all Extended Kotlin tests, APK assembly, ZIP/zipalign, v2 signature, Manifest/DEX assertions, OTP absence, checksum and artifact upload.

All currently identified and automatable desk/static gates are green for that code. Real-device HONOR acceptance is still required for OEM Accessibility delivery, background overlay access, live server interoperability, Shizuku grant persistence, reboot/update recovery, endurance, battery and typing-latency claims.

See `HANDOFF.md`, `WORKLOG.md` and `docs/TEST_PLAN.md`.

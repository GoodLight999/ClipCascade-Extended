# ClipCascade Extended

Reliability-first Android client for servers compatible with
[`Sathvik-Rao/ClipCascade`](https://github.com/Sathvik-Rao/ClipCascade).

## Setup/runtime order

1. **ADB-free runtime:** Accessibility copy signal → serialized one-shot overlay → clipboard read → upstream-compatible transport.
2. **Best fallback setup:** start Shizuku once, authorize Extended, apply/verify grants, then stop Shizuku.
3. **Second choice:** run PC ADB commands once.
4. Always-on Shizuku is intentionally not a runtime requirement.

The app provides direct Accessibility/overlay buttons, one-time Shizuku setup, PC ADB guidance, and Reliability Self-Test. Core setup text supports English, Japanese, and Simplified Chinese.

## Reliability changes

- Android mechanism is based on `wuxinkami/ClipCascade_go_fork`, but generic clicks, global debounce, dropped service-binding triggers, and concurrent overlays are replaced by a localized classifier and persistent serialized coordinator.
- Accessibility declares `canRetrieveWindowContent=false`.
- Accessibility and READ_LOGS fallback share one acquisition coordinator.
- Native events persist until React Native is ready.
- One-shot capture and notifications never clear the Android task.
- Shizuku uses a transient UserService only for setup; command exit codes and actual retained grants are verified before success.
- Protocol/authentication/encryption/P2S/P2P remain based on pinned `Sathvik-Rao/ClipCascade` source.

## Build

```bash
./scripts/materialize_upstream.sh
cd build/mobile
npm ci && npm run lint && npm test -- --runInBand
cd android
./gradlew testExtendedUnitTest assembleExtended
```

APK: `build/mobile/android/app/build/outputs/apk/extended/app-extended.apk`

```text
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.2 / versionCode 320002
Signer SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

## One-time fallback

Preferred: start Shizuku once → press the in-app one-time setup button → verify Self-Test → stop Shizuku.

Second choice:

```bash
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

An in-place same-signer update normally retains configuration and grants, but the app rechecks actual state. Uninstalling resets them.

## Status

CI run `29970261242` compiles/tests the Accessibility path and transient Shizuku UserService and produces a verified v2-signed APK. Real-device HONOR acceptance is the next gate; compilation is not presented as proof of OEM background reliability. OTP/SMS/email remains deferred.

See `HANDOFF.md`, `WORKLOG.md`, and `docs/TEST_PLAN.md`.

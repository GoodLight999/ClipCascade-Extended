# ClipCascade Extended

A reliability-first Android client for servers compatible with
[`Sathvik-Rao/ClipCascade`](https://github.com/Sathvik-Rao/ClipCascade).

## Reliability model

- **ADB-free first:** Android Share, Process Text, background reception, and
  notification-based OTP capture work without ADB.
- **Honest fallback:** Android 10+ blocks ordinary background clipboard access.
  Automatic generic-copy capture therefore retains `READ_LOGS` plus overlay as a
  supported ADB fallback. Shizuku remains an accepted future setup/runtime
  alternative, but is not falsely claimed as implemented.
- **No silent native-event loss:** share, OTP, and fallback events are queued until
  React Native is ready.
- **No task destruction:** one-shot clipboard capture and health notifications do
  not use `FLAG_ACTIVITY_CLEAR_TASK`.
- **Stable updates:** CI APKs use one repository-pinned sideload certificate so a
  later Extended build can update an earlier Extended build in place.

## Reproducible source model

The repository does not hide a copied mobile tree. `UPSTREAM.lock` pins the exact
verified upstream commit. `scripts/materialize_upstream.sh` fetches that commit,
applies guarded upstream repairs, applies the Extended overlay, and fails if any
expected source marker has drifted.

```bash
./scripts/materialize_upstream.sh
cd build/mobile
npm ci
npm run lint
npm test -- --runInBand
cd android
./gradlew testExtendedUnitTest assembleExtended
```

The installable APK is produced at:

```text
build/mobile/android/app/build/outputs/apk/extended/app-extended.apk
```

## Current validated artifact

The first complete green CI run produced a non-debuggable universal APK with:

```text
APK SHA-256:
23e798e0a6169bbf0b5904f304c2563fa0c87487d5c1ade8c9d902cf7648ecfb

Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

The package name is `com.clipcascade.extended`; it can coexist with the upstream
`com.clipcascade` application.

## Development state

Development is performed on draft pull requests. `HANDOFF.md` on the active
branch is the canonical continuation document. `docs/TEST_PLAN.md` separates
what CI has proven from what still requires a real Android device and live server.

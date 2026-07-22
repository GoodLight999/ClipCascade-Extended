# ClipCascade Extended

ClipCascade Extended is a reliability-first Android client for servers compatible with [Sathvik-Rao/ClipCascade](https://github.com/Sathvik-Rao/ClipCascade).

The Android client is based on the useful ideas from the historical native Android implementation in [wuxinkami/ClipCascade_go_fork](https://github.com/wuxinkami/ClipCascade_go_fork), but replaces its noisy “every click may be a copy” detector, plaintext credential storage, optimistic connection status, and fragile always-on `dataSync` foreground-service design.

## Current scope

- ADB-free clipboard text synchronization through an explicitly enabled Android Accessibility Service.
- Original ClipCascade server protocol compatibility:
  - `POST /login`
  - `GET /api/user-info`
  - WebSocket `/clipsocket`
  - STOMP send `/app/cliptext`
  - STOMP subscription `/user/queue/cliptext`
  - Original PBKDF2 + AES-256-GCM E2EE format
- English, Japanese, and Simplified Chinese UI.
- Android Keystore-backed encrypted credential storage.
- Conservative copy-signal detection and content-fingerprint loop suppression.
- Reconnection with bounded exponential backoff and truthful connection states.
- CI that builds and verifies the Go engine AAR and Android APK.
- Stable release-signing workflow prepared for a one-time GitHub Secrets setup.

## Resume development in another thread

Say only:

> https://github.com/GoodLight999/ClipCascade-Extended←これを引継いで開発して！

Then the next agent must read [`HANDOFF.md`](HANDOFF.md) and [`docs/WORKLOG.md`](docs/WORKLOG.md) before changing code.

## Build

CI is the canonical build path. Locally:

```bash
go test ./engine/...
go install golang.org/x/mobile/cmd/gomobile@latest
gomobile init
mkdir -p android/app/libs
gomobile bind \
  -target=android \
  -androidapi 26 \
  -javapkg ccengine \
  -o android/app/libs/engine.aar \
  ./engine/bridge

gradle -p android :app:lintDebug :app:testDebugUnitTest :app:assembleDebug
```

The unsigned/debug CI artifact is for validation. Do not establish an installation lineage until the repository's fixed release signing key is configured as described in [`docs/SIGNING.md`](docs/SIGNING.md).

## License and attribution

Apache-2.0. See [`NOTICE`](NOTICE) and [`docs/REFERENCE_AUDIT.md`](docs/REFERENCE_AUDIT.md).

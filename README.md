# ClipCascade Extended

ClipCascade Extended is a reliability-first Android client for servers compatible with [Sathvik-Rao/ClipCascade](https://github.com/Sathvik-Rao/ClipCascade).

The complete non-negotiable product contract is [`docs/PRODUCT_REQUIREMENTS.md`](docs/PRODUCT_REQUIREMENTS.md). Every development thread must read it before changing code. The concise current-state entry point is [`HANDOFF.md`](HANDOFF.md).

The project uses the preserved native Android implementation in [wuxinkami/ClipCascade_go_fork](https://github.com/wuxinkami/ClipCascade_go_fork) at commit `084616111aa993c77c9f293811534253b7d3d3f9` as its functional baseline, then rebuilds it around measurable background reliability, truthful status reporting, durable signing, multilingual setup, and explicit recovery paths.

## Absolute requirement

**Stable background send and receive operation takes priority over eliminating ADB.**

The intended runtime has three explicit tiers:

- **Standard:** Android AccessibilityService and normal APIs, without ADB or Shizuku.
- **Enhanced:** Shizuku-backed compatibility path for devices where Standard mode misses clipboard events or is aggressively killed. Prefer or adapt [`thedjchi/Shizuku`](https://github.com/thedjchi/Shizuku); its installation may be delegated to the user, while subsequent setup must be tap-guided.
- **Engineering:** direct ADB for development, diagnostics, stress tests, provisioning, and a documented last resort.

ADB-free operation remains the preferred outcome, but the project will not ship an unstable path merely to advertise “no ADB.” The app must disclose the active tier and must not claim success before its independent background send and receive self-tests pass.

## Required scope

- Original ClipCascade server protocol compatibility:
  - `POST /login`
  - `GET /api/user-info`
  - WebSocket `/clipsocket`
  - STOMP send `/app/cliptext`
  - STOMP subscription `/user/queue/cliptext`
  - Original PBKDF2 + AES-256-GCM E2EE format
- English, Japanese, and Simplified Chinese UI and setup guidance.
- Complete permission/setup/repair wizard for Accessibility, notifications, battery settings, vendor autostart, Shizuku, and ADB when required.
- Android Keystore-backed encrypted credential storage.
- Conservative copy-signal detection and content-fingerprint loop suppression.
- Reconnection with bounded exponential backoff and truthful connection states.
- A capability-based clipboard backend so Accessibility, Shizuku, and direct-ADB mechanisms can be tested independently.
- A self-test that verifies both receive and send paths while the activity is closed.
- CI that builds and verifies the Go engine AAR and Android APK.
- One permanent release-signing identity so every APK can update the previous version.
- Future OTP/SMS/email-notification support as a superset of [`jd1378/otphelper`](https://github.com/jd1378/otphelper), after the clipboard core is stable.

## Stability gate

A release is not considered stable because it compiles or works with the activity open. Every declared device/tier combination must pass the test matrix in [`HANDOFF.md`](HANDOFF.md), including 24-hour background send/receive, process death, reboot, network transitions, server restart, and a 500-copy stress test without duplicate storms or input lag.

## Resume development in another thread

Say only:

> https://github.com/GoodLight999/ClipCascade-Extended←これを引継いで開発して！

The next agent must read [`HANDOFF.md`](HANDOFF.md), [`docs/PRODUCT_REQUIREMENTS.md`](docs/PRODUCT_REQUIREMENTS.md), and [`docs/WORKLOG.md`](docs/WORKLOG.md) before changing code.

## Current repository state

The repository is in foundation bootstrap. Documentation and the stability policy exist; the Android/Go implementation, CI, signed APK, and real-device evidence must still be committed and verified. The canonical current truth is always in `HANDOFF.md`.

## License and attribution

Apache-2.0. Source attribution and the exact reused implementation areas must be maintained as code is imported or adapted.

# Worklog

## 2026-07-22 — Reliability policy and foundation investigation

### Product decisions

- Stable background send and receive operation is the absolute requirement.
- ADB-free operation is preferred but must not be pursued at the cost of reliability.
- Shizuku and direct ADB are approved fallback mechanisms when they produce better real-device results.
- Runtime support is divided into Standard, Enhanced/Shizuku, and Engineering/direct-ADB tiers.
- The application must report the active tier truthfully and pass separate send/receive self-tests before claiming success.

### Repository state

- `GoodLight999/ClipCascade-Extended` began as an empty repository.
- The active branch currently contains bootstrap documentation only.
- Android implementation code, Go engine code, CI, fixed signing configuration, and APK artifacts remain to be committed.

### Source investigation

- Inspected the original `Sathvik-Rao/ClipCascade` protocol and server behavior.
- Inspected `wuxinkami/ClipCascade_go_fork` history and found that Android/mobile files were removed from its later branch state.
- Verified that the Android source remains preserved and directly retrievable at commit `084616111aa993c77c9f293811534253b7d3d3f9`.
- Read the historical manifest, Kotlin activity, background service, accessibility service, boot receiver, history store, Go bridge, Go STOMP engine, crypto, protocol, and Android build scripts.

### Historical implementation findings

Useful baseline mechanisms:

- Native Kotlin Android shell.
- Go protocol/E2EE engine bound through gomobile.
- Accessibility-triggered clipboard reads.
- Temporary overlay-assisted clipboard access.
- Foreground network service and restart support.
- Original ClipCascade STOMP and encryption compatibility.

Required improvements:

- Add English and Japanese alongside Simplified Chinese.
- Replace plaintext SharedPreferences password storage with Android Keystore-backed encryption.
- Replace broad click-triggered clipboard probes with conservative hints and changed-content fingerprinting.
- Strengthen source-aware loop suppression beyond one `lastWrittenText` value.
- Report connection only after successful authentication, WebSocket, STOMP handshake, and subscription.
- Isolate Standard, Shizuku, and direct-ADB clipboard access behind one capability interface.
- Establish a permanent release signing identity rather than using debug signing as the installable lineage.
- Validate foreground-service, reboot, and process-recovery behavior per Android version and device vendor instead of assuming one mechanism is universal.

### Next implementation action

1. Import the required historical Android and Go source into the active branch.
2. Introduce `ClipboardAccessBackend` with Standard, Enhanced/Shizuku, and Engineering/direct-ADB implementations.
3. Add protocol tests, Android tests, CI, and APK assembly.
4. Run HONOR/MagicOS background send and receive tests before declaring any tier stable.

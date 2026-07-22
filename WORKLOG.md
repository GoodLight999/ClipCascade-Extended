# ClipCascade Extended — Worklog

This file is chronological engineering evidence. `HANDOFF.md` is the concise
canonical state and always takes precedence when this file contains older entries.

## 2026-07-23 — Requirement-priority correction

### User correction

The original governing requirements were re-established:

- generic clipboard reliability is the core objective;
- ADB-free operation is the final goal;
- a dependable ADB fallback is required when it improves stability;
- any ADB-capable fallback must be integrated with Shizuku and presented as a
  click-driven setup rather than raw commands;
- `wuxinkami/ClipCascade_go_fork` is the primary Android behavior reference and its
  Accessibility Service mechanism must be reproduced and improved;
- `Sathvik-Rao/ClipCascade` remains the protocol/server compatibility authority;
- English, Japanese, and Simplified Chinese setup/UI are required;
- stable signing and in-place updates are mandatory;
- OTP/SMS/email work is deferred until generic clipboard reliability is complete and
  must ultimately exceed `jd1378/otphelper` rather than duplicate it poorly.

### Error acknowledged

The preceding implementation incorrectly prioritized notification OTP work and
understated the importance of the Go fork and Shizuku. The generated APK was CI-green,
but it did not contain the Go fork's Accessibility Service path or Shizuku integration.
It must be treated as a build/lifecycle baseline, not a requirement-complete release.

### Go fork inspection

Files inspected at `wuxinkami/ClipCascade_go_fork`:

- `mobile/android/app/src/main/java/com/clipcascade/android/ClipCascadeAccessibilityService.kt`
- `mobile/android/app/src/main/java/com/clipcascade/android/ClipCascadeBackgroundService.kt`
- `mobile/android/app/src/main/AndroidManifest.xml`
- `mobile/android/app/src/main/res/xml/accessibility_service_config.xml`

Observed mechanism:

1. Accessibility events outside the app trigger a delayed/debounced copy check.
2. Accessibility Service binds to a sticky foreground background service.
3. The service creates a momentary 1x1 overlay, reads the clipboard, removes the
   overlay, suppresses a simple self-loop, and sends through the Go engine.
4. Boot/package-replacement receiver restarts the service.

Observed weaknesses to improve rather than copy literally:

- broad `TYPE_VIEW_CLICKED` triggering and excessive wakeups;
- one global debounce that may miss legitimate rapid copies;
- incomplete localized copy-signal recognition;
- trigger loss while service binding is unavailable;
- non-serialized overlay operations;
- weak text-only duplicate/loop detection;
- limited retry and durable state;
- Chinese-only user experience and diagnostics.

### Shizuku direction

Primary developer API: `RikkaApps/Shizuku-API`.
Recommended user-facing option under evaluation: `thedjchi/Shizuku`, because its
watchdog and improved start-on-boot behavior may reduce setup failures. The fork
currently states that maintenance is paused, so integration must use standard Shizuku
API contracts and must not depend unnecessarily on fork-only internals.

Implementation must:

- add Shizuku provider/API dependencies;
- detect binder/version/UID/permission/death state;
- request Shizuku authorization inside Extended;
- prefer Binder/UserService operations to text shell commands;
- apply and verify required grants/app-ops through a guided wizard;
- display degraded state after reboot when Shizuku is not active;
- retain Accessibility as the preferred ADB-free path.

### ADB grant update behavior

Working assumption recorded for implementation and device verification:

- an in-place update with the same application ID/signing lineage normally retains
  package permission and app-op state;
- uninstall/fresh install resets it;
- manifest removal, user/admin revocation, OEM policy, or permission auto-reset can
  change it;
- therefore the app must inspect actual state after every start/update and never show
  setup as complete merely because it was completed once.

### Documentation changes

- Replaced `HANDOFF.md` with the corrected source authority, priority, honest current
  gaps, target architecture, acceptance standard, and continuation order.
- Added this chronological `WORKLOG.md`.

### Current branch state after correction

```text
Branch: stability-mobile-otp
Correction commit: 22bd17ca8d97a468b0286dc18c14cbb3752f7e4c
PR: #2 (draft)
```

### Next implementation action

Implement the Accessibility Service, manifest/XML configuration, copy-event classifier,
durable trigger queue, and serialized overlay acquisition coordinator before expanding
OTP functionality or declaring the APK usable.

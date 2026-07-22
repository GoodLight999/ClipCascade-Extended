# ClipCascade Extended — Canonical Handoff

Last materially updated: **2026-07-23 JST**

This is the single canonical continuation document. A new thread must be able to
resume by receiving only:

> https://github.com/GoodLight999/ClipCascade-Extended ←これを引継いで開発して！

Do not reconstruct project state from archived repositories, abandoned branches,
old chat speculation, or superseded CI failures.

## 1. Repository and source authority

- Development repository: `GoodLight999/ClipCascade-Extended`
- Active branch: `stability-mobile-otp` (historical name; clipboard reliability now has priority)
- Active draft PR: `#2 — Build a reliability-first Android client and standalone APK`
- **Protocol/server compatibility authority:** `Sathvik-Rao/ClipCascade`
- **Primary Android behavior reference:** `wuxinkami/ClipCascade_go_fork`
- Shizuku integration/reference: `RikkaApps/Shizuku-API` and, for user-facing
  installation/restart robustness, `thedjchi/Shizuku`
- Permanently excluded: `GoodLight999/Trash-ClipCascade`

The excluded repository must not be imported, copied, migrated, tested as a
baseline, treated as a source of implementation facts, or described as a
canonical/archived original.

Before using any repository, verify exact owner/name, archive status, stated role,
license, and the user's designation.

## 2. Corrected user requirements and priority order

**Stable operation is the absolute requirement. ADB-free generic clipboard sync is
the final goal, but a dependable ADB fallback is preferable to an unreliable
ADB-free claim.**

The governing priority order is:

1. **Generic Android clipboard send/receive reliability.** This is the core product.
2. Reproduce and then harden the Go fork's Android mechanism:
   `AccessibilityService` copy-signal detection -> foreground background service ->
   momentary overlay/focus acquisition -> clipboard read -> upstream-compatible send.
3. Preserve full server-side compatibility with `Sathvik-Rao/ClipCascade`, including
   authentication, P2S/P2P behavior, encryption, payload types, and reconnect semantics.
4. Make ADB-free operation the preferred path using Accessibility Service and normal
   Android permissions.
5. Keep a formal ADB-capable fallback when needed for stability. **ADB fallback and
   Shizuku integration are a package deal:** the application must detect Shizuku,
   request Shizuku permission, apply/check required grants through privileged Binder or
   UserService calls where possible, and guide the user through a click-driven wizard.
   Installing and starting Shizuku may be delegated to the user; raw desktop ADB
   commands must not be the normal user experience.
6. Provide a foolproof permission/setup wizard and self-test in English, Japanese,
   and Simplified Chinese. Every step must expose current state, expected result,
   failure reason, and a direct settings/action button.
7. Use one permanent application ID and one permanent signing lineage so every
   generated APK supports in-place update.
8. **OTP/SMS/email extraction is deferred to the final phase.** It must not distract
   from clipboard reliability. When resumed, it must aim to exceed `jd1378/otphelper`,
   not ship as a superficial regex feature.

Design documents alone are not completion. Every behavioral change must progress
through implementation, automated tests, CI, APK generation, and real-device
acceptance.

## 3. Honest status of the current PR

The current PR is a useful **CI-green build and lifecycle baseline**, but it does
**not yet satisfy the corrected core requirement**.

What is implemented and worth preserving:

- reproducible pinning of `Sathvik-Rao/ClipCascade` mobile source;
- deterministic guarded overlays/patches;
- stable Extended package ID and signing key;
- native-event persistence when React Native is not ready;
- task/lifecycle fixes that remove destructive `FLAG_ACTIVITY_CLEAR_TASK` behavior;
- strict lint, Jest, Android unit tests, signed APK build, signature verification;
- diagnostics scaffolding and a fallback log-denial classifier.

What is **not** implemented yet:

- the Go fork's `ClipCascadeAccessibilityService` equivalent;
- an Accessibility Service configuration and multilingual enablement wizard;
- a hardened accessibility-event classifier for copy operations;
- direct integration between accessibility detection and durable outbound queueing;
- Shizuku API/provider/UserService integration;
- one-tap Shizuku-assisted grant/app-op setup and health checks;
- a complete English/Japanese/Chinese UI;
- real-device proof on the user's HONOR device;
- long-duration, reboot, process-death, rapid-copy, and reconnect acceptance;
- demonstrated behavioral parity or superiority over the historical Go client.

The existing notification OTP code is experimental/non-priority. Do not expand it
until the generic clipboard acceptance matrix is green. It may remain isolated if it
does not destabilize the core, but it must not define the branch's architecture or
completion criteria.

## 4. Go fork findings that must guide implementation

The Go fork contains a concrete Android path that reportedly worked reasonably well
for the user:

- `ClipCascadeAccessibilityService` observes accessibility events outside its own
  package and triggers clipboard acquisition after a delay/debounce;
- it binds to `ClipCascadeBackgroundService`;
- the background service briefly adds a 1x1 overlay to obtain sufficient foreground
  focus, reads the clipboard, suppresses self-loop content, and sends through its
  engine;
- the service is foreground/sticky and is restarted after boot/package replacement.

This is the starting behavior to reproduce, not code to copy blindly. Known weaknesses
that must be improved:

- it triggers on broad `TYPE_VIEW_CLICKED`/selection events, causing needless wakeups;
- one global one-second debounce can miss rapid legitimate copies;
- copy-word matching is incomplete and language/OEM dependent;
- service binding races simply drop triggers;
- overlay add/read/remove is not serialized and is vulnerable to concurrent events;
- failure/retry state is mostly logging rather than a durable queue/state machine;
- text-only assumptions and simplistic `lastWrittenText` loop suppression are weak;
- some task flags and lifecycle handling need the same corrections already made in
  Extended.

Extended must preserve the successful mechanism while replacing these weaknesses with
an explicit state machine, bounded queues, content fingerprints, retry policy,
serialized overlay access, truthful diagnostics, and tests.

## 5. Target Android architecture

### Preferred ADB-free path

1. Foreground synchronization service maintains authenticated P2S/P2P connectivity.
2. Accessibility Service listens only to the minimum required events and packages.
3. A copy-signal classifier combines event type, source package, localized copy
   announcements/toasts, timing, and clipboard fingerprint changes.
4. Trigger requests enter a bounded durable queue; they are never silently discarded
   because a service or React context is not ready.
5. A single serialized clipboard acquisition coordinator briefly obtains focus with
   an overlay, reads clipboard data, removes the overlay in `finally`, fingerprints the
   payload, suppresses loops/duplicates, and submits it to the transport queue.
6. Transport acknowledgements, reconnects, retries, and status shown in UI must reflect
   reality; opening the app must never fabricate `Connected`.

### Shizuku/ADB reliability fallback

- Integrate `dev.rikka.shizuku:api` and provider support.
- Detect binder availability, Shizuku version, server UID (ADB/root), permission state,
  and binder death.
- Request Shizuku authorization from inside Extended.
- Prefer Binder/system-service calls or a Shizuku UserService over spawning textual
  shell commands. Use command execution only where no stable Binder route exists.
- Provide click-driven actions to apply/check `READ_LOGS` and required app-op state,
  with explicit verification after each action.
- Handle reboot/Shizuku-not-running as a visible degraded state and retain the normal
  Accessibility path.
- Support `thedjchi/Shizuku` as the recommended user-facing Shizuku build when its
  watchdog/start-on-boot behavior is useful, but do not couple the app to fork-only
  APIs unless documented and tested.

Raw ADB commands remain developer/emergency documentation, not the primary onboarding
flow.

## 6. Permissions and update semantics

The permanent package is `com.clipcascade.extended`. Later APKs must use the same
application ID, signer/signing lineage, and monotonically increasing versionCode.

A permission or app-op granted to the installed package normally survives an in-place
update because the package installation is replaced rather than uninstalled. This
includes a previously applied `pm grant` such as `READ_LOGS`, provided that:

- the update is accepted as the same app (same application ID and signer/lineage);
- the updated manifest still requests the permission;
- the app is not uninstalled/cleared as part of installation;
- Android/OEM policy, permission auto-reset, or a user/admin action does not revoke it.

Therefore the setup wizard must always **check**, never merely assume, the post-update
state. Uninstalling the app resets grants and app data. Changing the package ID or
signing certificate prevents an in-place update and would require a fresh install.

## 7. Current reproducible baseline and evidence

`UPSTREAM.lock` pins:

```text
Repository: Sathvik-Rao/ClipCascade
Commit: fd2cbbce69d5e5fa6b9b758d13a7dc6efdcb8a39
Mobile path: ClipCascade_Mobile/src
```

Current CI-green baseline:

```text
Implementation commit: f948196bce539022ec047ab1b23de4b7712c418d
Final documentation/CI commit before this correction: 41c51bd60af891aed1297033442676852fd390a8
Workflow run: 29966386455
Application ID: com.clipcascade.extended
Version: 3.2.0-extended.1 / versionCode 320001
Signer certificate SHA-256:
2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
```

The green workflow passed exact materialization, patch drift checks, npm install,
ESLint, Jest, Android unit tests, APK assembly, APK signature verification, checksum,
and artifact upload. This proves build integrity only; it does not prove the missing
Accessibility/Shizuku behavior.

## 8. Immediate continuation order

1. Add a work-tested Accessibility Service modeled on the Go fork.
2. Add the accessibility XML/manifest entries and English/Japanese/Chinese onboarding.
3. Implement a serialized clipboard acquisition coordinator and durable trigger queue.
4. Connect acquired clipboard payloads to the existing upstream-compatible transport.
5. Add unit/instrumentation tests for event classification, debounce/coalescing,
   service-not-ready recovery, overlay cleanup, duplicate suppression, and rapid copy.
6. Build and device-test the ADB-free path on the user's HONOR device.
7. Integrate Shizuku API/provider/UserService and a click-driven fallback wizard.
8. Verify grants/app-ops after setup, app update, process death, and reboot.
9. Run fresh-install, in-place-update, 30-minute rapid-copy, 8-hour idle/reconnect,
   process-kill, reboot, and multiple-source-app tests.
10. Only after the generic clipboard matrix is green, resume OTP/SMS/email work and
    compare behavior directly against `jd1378/otphelper`.

## 9. Acceptance standard

Do not claim success from compilation or a self-test button alone. Completion requires
recorded real-device evidence for:

- truthful connection state;
- background inbound and outbound text;
- screen-off and app-not-open behavior;
- rapid consecutive copies without stale/missed/duplicate sends;
- at least five source apps and major clipboard UI variants;
- service/process death and reconnect;
- reboot and package replacement;
- ADB-free Accessibility path;
- Shizuku-assisted fallback with click-only onboarding;
- in-place APK update with retained configuration and verified permission state;
- acceptable battery and input-latency impact.

## 10. Documentation discipline

- Keep this file as the concise canonical state.
- Keep `WORKLOG.md` as chronological evidence, failed hypotheses, commands, CI runs,
  device observations, and next actions.
- Update both whenever requirements, architecture, package ID, signer, CI state,
  device evidence, or priority changes.
- Keep PR #2 draft until the corrected core acceptance matrix is green or the user
  explicitly chooses another merge strategy.
- Do not erase failed attempts; mark them superseded and record why, without treating
  them as current implementation facts.

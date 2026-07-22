# Worklog

## 2026-07-22 — Stability policy correction

### User decision

- Stable background operation is the absolute requirement.
- ADB-free operation is preferred but must not be pursued at the cost of reliability.
- Shizuku and direct ADB are approved fallback mechanisms when they produce better real-device results.

### Repository changes

- Rewrote `HANDOFF.md` so every future thread uses reliability as the highest-priority criterion.
- Defined three explicit runtime tiers: Standard, Enhanced/Shizuku, and Engineering/direct-ADB.
- Required the application to report the active tier truthfully and pass send/receive self-tests before claiming success.
- Corrected the repository status: implementation code and CI are not yet committed; prior documentation must not be mistaken for completed code.
- Expanded the stability gate to include background send as well as receive, process death, reboot, network transitions, server restart, upgrades, and stress testing.

### Next implementation action

- Add a capability-based clipboard backend so Standard, Shizuku, and direct-ADB mechanisms can be implemented and tested without coupling them to protocol or UI logic.

## 2026-07-22 — Foundation investigation

### Investigated

- Confirmed `GoodLight999/ClipCascade-Extended` was an empty public repository with write/admin access.
- Inspected original `Sathvik-Rao/ClipCascade` protocol paths and Android ADB dependency.
- Inspected `wuxinkami/ClipCascade_go_fork` current history and found mobile removal commits.
- Recovered the historical native Android design from commit `084616111aa993c77c9f293811534253b7d3d3f9`.
- Read its manifest, native Kotlin activity, background service, accessibility service, boot receiver, history store, Go bridge, Go STOMP engine, crypto, protocol, and Android build scripts.

### Defects found in the historical Android design

- UI was Chinese-only.
- Password was stored in plaintext SharedPreferences.
- Accessibility service treated broad click/selection activity as likely copy activity.
- A single `lastWrittenText` value was insufficient loop suppression.
- Service updated “connected” optimistically after `Engine.Start()` rather than using only callback-confirmed state.
- A permanent `dataSync` foreground service and boot restart path are a poor universal modern Android foundation.
- Transparent overlay logic was mixed into the network service.
- Debug signing was used as an “installable” release alias, so update lineage was not durable.

### Foundation documents created

- Reliability and handoff policy.
- Original server compatibility requirements.
- Multilingual and durable-signing requirements.
- Permanent worklog discipline.

### Validation pending

- Android and Go implementation commit.
- GitHub Actions build result.
- Fixed release signing secrets.
- Real-device tests.
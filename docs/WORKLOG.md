# Worklog

## 2026-07-22 — Foundation bootstrap

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
- A permanent `dataSync` foreground service and boot restart path are a poor modern Android foundation.
- Transparent overlay logic was mixed into the network service.
- Debug signing was used as an “installable” release alias, so update lineage was not durable.

### Implemented in this bootstrap

- ADB-free AccessibilityService-first architecture.
- Conservative copy detection plus changed-content fingerprint gate.
- Android Keystore encrypted config.
- Truthful state machine.
- Multilingual resources.
- Original server protocol and E2EE compatibility engine.
- CI build pipeline.
- Permanent handoff and worklog discipline.
- Permission/signing/architecture/server compatibility documentation.

### Validation pending

- GitHub Actions build result.
- Fixed release signing secrets.
- Real-device tests.

# ClipCascade Extended — Worklog

`HANDOFF.md` is the canonical current state. This file preserves chronological engineering evidence.

## 2026-07-23 — Requirement correction

The prior CI-green baseline incorrectly prioritized notification OTP and lacked the Go-fork Accessibility path and Shizuku integration. It was reclassified as a build/lifecycle baseline. Correct priority:

1. generic clipboard reliability;
2. ADB-free Accessibility runtime;
3. one-time Shizuku setup as best fallback;
4. one-time PC ADB as second choice;
5. no always-on Shizuku dependency;
6. OTP/SMS/email only after clipboard acceptance and only as an otphelper superior.

Inspected Go-fork files: Accessibility Service, background service, manifest, and accessibility XML. Preserved its event→overlay→read concept, but rejected broad click triggering, one global debounce, service-binding drops, non-serialized overlays, weak loop state, and Chinese-only UX.

Correction/documentation commits:

```text
22bd17ca8d97a468b0286dc18c14cbb3752f7e4c
369da2478c6107fda139db1ef75fa7bf708d1937
```

## 2026-07-23 — Accessibility and one-time Shizuku implementation

Implemented:

- localized copy-signal classifier and tests;
- Accessibility Service with `canRetrieveWindowContent=false`;
- persistent serialized capture coordinator with retry/newer-request preservation;
- one-shot overlay Activity and React-not-ready event persistence;
- unified Accessibility and READ_LOGS trigger serialization;
- English/Japanese/Simplified-Chinese setup resources/buttons;
- Shizuku API/provider 13.1.5, AIDL, transient non-daemon UserService;
- in-app authorization and one-time READ_LOGS/overlay application;
- strict command exit-code checking plus Extended-side polling of actual retained grants;
- PC ADB explicitly second choice;
- OTP removed from core setup flow;
- version `3.2.0-extended.2`, versionCode `320002`, package/signer unchanged.

Implementation commits:

```text
6a01c89889d16c43004706f239e6a4694a071cf1  Accessibility/Shizuku
9d240b08d40a067f3c340f98f2e1a8b771459541  version/UserService correction
9a7dd08e4fb343f6c3946911adbea3dd168e42cf  unified capture serialization
886c155e56187c0b814460c095857845e6a52b1e  strict Shizuku verification
```

CI run `29970261242` passed all source, npm, lint, Jest, Android tests/build, signing, checksum, and artifact steps.

```text
APK size: 93,595,251 bytes
APK SHA-256: d7ce5149d4503a88f376a0b3902cb5986686951210c2e812364027aa8e14b77f
Signer SHA-256: 2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd
Signature: APK Signature Scheme v2
```

Proof boundary: CI does not establish HONOR/OEM event delivery, background overlay behavior, real Shizuku grant persistence, live server compatibility, endurance, reboot recovery, battery impact, or actual in-place update. Next work is device acceptance, not OTP expansion.

#!/usr/bin/env python3
"""Prevent stale service toggles, unbounded stop waits and unsafe P2P controls."""
from __future__ import annotations

import argparse
from pathlib import Path


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f"missing {label}: {needle!r}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise RuntimeError(f"forbidden {label}: {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root.resolve()
    app = (root / "App.js").read_text(encoding="utf-8")
    service = (root / "StartForegroundService.js").read_text(encoding="utf-8")
    policy = (root / "ServiceControlPolicy.js").read_text(encoding="utf-8")

    require(app, "nextRequestedServiceState(persistedWsIsRunning)", "persisted service toggle")
    require(app, "hasForegroundStopTimedOut", "bounded stop policy")
    require(app, "stop-timeout", "truthful stop timeout state")
    require(app, "FOREGROUND_STOP_TIMEOUT_MS", "explicit stop timeout")
    forbid(app, "wsIsRunning === 'true' ? 'false' : 'true'", "stale React-state toggle")
    require(policy, "FOREGROUND_STOP_TIMEOUT_MS = 10_000", "10 second stop bound")

    require(service, "activeForegroundRuntimeId", "single foreground runtime lease")
    require(service, "duplicate-runtime-suppressed", "duplicate runtime suppression")
    require(service, "localCompatibility", "local compatibility descriptor")
    require(service, "case 'OFFER': {", "OFFER compatibility receiver")
    require(service, "case 'ANSWER': {", "ANSWER compatibility receiver")
    require(service, "compatibility: localCompatibility", "forwarded compatibility metadata")
    require(service, "compatibility.state !== 'incompatible'", "pre-connection mismatch guard")
    require(service, "!quarantinedPeers.has(peerId)", "quarantined outbound peer filter")
    require(service, "Never send private control frames over the clipboard DataChannel", "legacy-safe liveness")
    forbid(service, "type: 'COMPATIBILITY'", "unforwarded custom signaling type")
    forbid(service, "case 'COMPATIBILITY'", "unforwarded custom signaling receiver")
    forbid(service, "P2P_COMPATIBILITY_JSON", "data-channel compatibility frame")
    forbid(service, "P2P_DC_KEEPALIVE_JSON", "data-channel keepalive frame")
    forbid(service, "channel.send(P2P_COMPATIBILITY_JSON)", "compatibility frame send")
    forbid(service, "channel.send(P2P_DC_KEEPALIVE_JSON)", "keepalive frame send")

    print("service state and legacy-safe P2P controls: OK")


if __name__ == "__main__":
    main()

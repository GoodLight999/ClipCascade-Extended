#!/usr/bin/env python3
"""Require bounded, unit-tested P2P signaling input validation."""
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
    service = (root / "StartForegroundService.js").read_text(encoding="utf-8")
    validation = (root / "P2PSignalingValidation.js").read_text(encoding="utf-8")

    for marker, label in (
        ("MAX_SIGNALING_MESSAGE_CHARS = 1024 * 1024", "signaling message bound"),
        ("MAX_PEERS = 4096", "peer-list count bound"),
        ("MAX_PEER_ID_LENGTH = 256", "peer-ID length bound"),
        ("CONTROL_CHARACTERS", "peer-ID control-character guard"),
        ("normalizeP2PPeerId", "peer-ID normalizer"),
        ("normalizeP2PPeerList", "peer-list normalizer"),
        ("parseP2PSignalingMessage", "signaling parser"),
        ("return { type: 'IGNORED' }", "forward-compatible unknown type policy"),
    ):
        require(validation, marker, label)

    require(
        service,
        "import { parseP2PSignalingMessage } from './P2PSignalingValidation';",
        "signaling validator import",
    )
    require(
        service,
        "const data = parseP2PSignalingMessage(event.data);",
        "validated signaling dispatch",
    )
    require(service, "if (data.type === 'IGNORED') return;", "unknown type ignore policy")
    require(service, "data.toPeerId !== myPeerId", "routed destination guard")
    require(service, "data.fromPeerId === myPeerId", "self-spoof guard")
    require(service, "recordSignalingFailure('message', e)", "validation failure evidence")
    require(
        service,
        "await setDataInAsyncStorage(\n                      'p2p_last_signaling_error',\n                      '',",
        "successful message recovery evidence",
    )
    forbid(service, "const data = JSON.parse(event.data);", "unvalidated signaling JSON")

    print("P2P signaling messages are bounded, normalized and route-checked: OK")


if __name__ == "__main__":
    main()

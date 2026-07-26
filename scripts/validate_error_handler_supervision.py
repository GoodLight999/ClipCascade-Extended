#!/usr/bin/env python3
"""Reject error handlers that can themselves create unhandled rejections."""
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

    for marker, label in (
        ("`peer-operation-record:${peerId}`", "peer-operation recorder"),
        ("runDetached('foreground-poll-loop-failure'", "poll-loop failure handler"),
        (
            "runDetached('foreground-handler-unhandled-failure'",
            "terminal foreground failure handler",
        ),
    ):
        require(service, marker, f"supervised {label}")

    forbid(
        service,
        "peerOpChains[peerId] = current.catch(async error => {",
        "async peer-operation error recorder",
    )
    forbid(
        service,
        "pollFlagsLoop().catch(async error => {",
        "async poll-loop failure handler",
    )
    forbid(
        service,
        "          .catch(async error => {\n            const detail = String(error?.stack || error);",
        "async terminal foreground failure handler",
    )

    print("foreground error handlers use supervised non-rejecting boundaries: OK")


if __name__ == "__main__":
    main()

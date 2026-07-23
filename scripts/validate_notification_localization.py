#!/usr/bin/env python3
"""Reject inherited English Foreground Service notifications and channels."""
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
    i18n = (root / "ExtendedI18n.js").read_text(encoding="utf-8")

    require(service, "const RUNTIME_TEXT = getExtendedStrings();", "foreground locale dictionary")
    require(service, "RUNTIME_TEXT.notificationConnectionRestored", "restored notification")
    require(service, "RUNTIME_TEXT.notificationConnectionLost", "lost notification")
    require(service, "RUNTIME_TEXT.notificationDownloadFiles", "received-file notification")
    require(service, "RUNTIME_TEXT.notificationDownloadingFiles", "file-save notification")
    require(service, "RUNTIME_TEXT.downloadFilesFailed", "file-save failure dialog")
    require(service, "RUNTIME_TEXT.notificationMonitorChannel", "monitor channel")
    require(service, "RUNTIME_TEXT.notificationDownloadProgressChannel", "progress channel")
    require(service, "RUNTIME_TEXT.notificationConnectionChannel", "connection channel")

    for key in (
        "notificationMonitorChannel",
        "notificationDownloadProgressChannel",
        "notificationConnectionChannel",
        "notificationConnectionRestored",
        "notificationConnectionLost",
        "notificationDownloadFiles",
        "notificationDownloadingFiles",
        "downloadFilesFailed",
    ):
        require(i18n, f"{key}:", f"localized notification key {key}")

    for inherited in (
        "WebSocket Connection Restored",
        "WebSocket Connection Lost",
        "📥 Download File(s)",
        "Downloading File(s)...",
        "ClipCascade Monitor",
        "ClipCascade Download Progress",
        "ClipCascade Connection Status",
        "Failed to download files",
    ):
        forbid(service, inherited, f"inherited notification text {inherited}")

    print("foreground notification localization: OK")


if __name__ == "__main__":
    main()

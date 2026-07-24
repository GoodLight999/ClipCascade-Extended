#!/usr/bin/env python3
"""Connect inherited Foreground Service notifications to canonical locale keys."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_exact(path: Path, old: str, new: str, expected: int, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} markers, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    service = root / "StartForegroundService.js"

    replace_once(
        service,
        "} from './AsyncStorageManagement';",
        """} from './AsyncStorageManagement';
import { getExtendedStrings } from './ExtendedI18n';

const RUNTIME_TEXT = getExtendedStrings();""",
        "foreground notification locale import",
    )
    replace_exact(
        service,
        "'WebSocket Connection Restored 🔗'",
        "RUNTIME_TEXT.notificationConnectionRestored",
        2,
        "localized restored notifications",
    )
    replace_exact(
        service,
        "'WebSocket Connection Lost ⛓️‍💥'",
        "RUNTIME_TEXT.notificationConnectionLost",
        2,
        "localized lost notifications",
    )
    replace_exact(
        service,
        "'📥 Download File(s)'",
        "RUNTIME_TEXT.notificationDownloadFiles",
        2,
        "localized P2S/P2P received-file notifications",
    )
    replace_once(
        service,
        "title: 'Downloading File(s)...',",
        "title: RUNTIME_TEXT.notificationDownloadingFiles,",
        "localized file-save progress notification",
    )
    replace_once(
        service,
        "Alert.alert('Error', 'Failed to download files: ' + e);",
        """Alert.alert(
                  RUNTIME_TEXT.errorTitle,
                  `${RUNTIME_TEXT.downloadFilesFailed}: ${String(e)}`,
                );""",
        "localized file-save failure dialog",
    )
    replace_once(
        service,
        "name: 'ClipCascade Monitor',",
        "name: RUNTIME_TEXT.notificationMonitorChannel,",
        "localized foreground channel",
    )
    replace_once(
        service,
        "name: 'ClipCascade Download Progress',",
        "name: RUNTIME_TEXT.notificationDownloadProgressChannel,",
        "localized progress channel",
    )
    replace_once(
        service,
        "name: 'ClipCascade Connection Status',",
        "name: RUNTIME_TEXT.notificationConnectionChannel,",
        "localized connection channel",
    )

    text = service.read_text(encoding="utf-8")
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
        if inherited in text:
            raise RuntimeError(f"inherited notification text remained: {inherited}")


if __name__ == "__main__":
    main()

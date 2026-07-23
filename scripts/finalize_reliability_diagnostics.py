#!/usr/bin/env python3
"""Add guarded diagnostics for the hardened reliability phase."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()

    replace_once(
        root / "android/app/src/main/java/com/clipcascade/NativeBridgeModule.kt",
        '''                put("captureCoordinator", ClipboardCaptureCoordinator.status(reactApplicationContext))
                put("readLogs", readLogs)''',
        '''                put("captureCoordinator", ClipboardCaptureCoordinator.status(reactApplicationContext))
                put("nativeDeliveryReady", PendingReactEventStore.isDeliveryReady())
                put("sharedPayloadStatus", bridge.getValue("shared_payload_status").orEmpty())
                put("readLogs", readLogs)''',
        "native reliability diagnostics",
    )

    replace_once(
        root / "App.js",
        '''                        `Coordinator: ${status.captureCoordinator}`,
                        `READ_LOGS: ${status.readLogs}`,''',
        '''                        `Coordinator: ${status.captureCoordinator}`,
                        `JS event listener ready: ${status.nativeDeliveryReady}`,
                        `Shared payload staging: ${status.sharedPayloadStatus || 'idle'}`,
                        `READ_LOGS: ${status.readLogs}`,''',
        "self-test reliability diagnostics",
    )


if __name__ == "__main__":
    main()

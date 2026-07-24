#!/usr/bin/env python3
"""Add guarded native status fields for the hardened reliability phase.

The final user-facing diagnostics are canonical in overlay/AutoDebug.js and
ExtendedControlPanel.js; materialization must not patch temporary App UI.
"""
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
                put("outboundQueueStatus", bridge.getValue("outbound_queue_status").orEmpty())
                put("restartReceiverStatus", bridge.getValue("restart_receiver_status").orEmpty())
                put("readLogs", readLogs)''',
        "native reliability diagnostics",
    )


if __name__ == "__main__":
    main()

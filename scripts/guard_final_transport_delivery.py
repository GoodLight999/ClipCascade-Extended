#!/usr/bin/env python3
"""Close the final P2S publish race after all transport semantics are generated."""
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
    service = root / "StartForegroundService.js"

    replace_once(
        service,
        """              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ Connected - Broadcasting',
              );
              try {
                stompClient.publish({""",
        """              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ Connected - Broadcasting',
              );
              // Base64 conversion, encryption and storage writes above may yield.
              // Re-check ownership immediately before the irreversible publish.
              if (!runtimeCanAcceptEvents()) {
                toggle = false;
                p2sReceiptTracker.cancel();
                p2sEchoGuard.clear();
                return OUTBOUND_DELIVERY.WAITING;
              }
              try {
                stompClient.publish({""",
        "P2S publish-time runtime ownership guard",
    )


if __name__ == "__main__":
    main()

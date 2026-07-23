#!/usr/bin/env python3
"""Prevent signaling traffic from fabricating a live P2P peer connection."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")
    old = '''                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '✅ Connected',
                  );'''
    new = '''                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    liveConnectionsCount > 0
                      ? '✅ P2P peer connected'
                      : '✅ Signaling connected; waiting for peer',
                  );'''
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"P2P signaling inbound status: expected one marker, found {count}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


if __name__ == "__main__":
    main()

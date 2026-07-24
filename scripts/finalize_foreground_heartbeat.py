#!/usr/bin/env python3
"""Persist a low-frequency heartbeat from the actual foreground-service loop."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")
    old = """        async function pollFlagsLoop() {
          const POLL_KEYS = [
            'wsIsRunning',
            'echo',
            'downloadFiles',
            'filesAvailableToDownload',
          ];

          while (true) {
            const json = NativeBridgeModule.getFlagsSync(POLL_KEYS);"""
    new = """        async function pollFlagsLoop() {
          const POLL_KEYS = [
            'wsIsRunning',
            'echo',
            'downloadFiles',
            'filesAvailableToDownload',
          ];
          let heartbeatCounter = 0;

          while (true) {
            if (heartbeatCounter === 0) {
              await setDataInAsyncStorage(
                'foreground_service_heartbeat_at',
                String(Date.now()),
              );
            }
            heartbeatCounter = (heartbeatCounter + 1) % 5;
            const json = NativeBridgeModule.getFlagsSync(POLL_KEYS);"""
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"foreground heartbeat marker: expected one, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


if __name__ == "__main__":
    main()

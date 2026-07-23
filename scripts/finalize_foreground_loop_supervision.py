#!/usr/bin/env python3
"""Ensure asynchronous foreground polling failures cannot orphan the runtime lease."""
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
        """        pollFlagsLoop();""",
        """        void pollFlagsLoop().catch(async error => {
          const detail = String(error?.stack || error);
          await setDataInAsyncStorage(
            'foreground_service_error',
            detail.slice(0, 4000),
          );
          await setDataInAsyncStorage('foreground_service_state', 'loop-failed');
          await setDataInAsyncStorage(
            'foreground_service_loop_failed_at',
            String(Date.now()),
          );
          await setDataInAsyncStorage(
            'wsStatusMessage',
            '❌ Foreground service: ' + detail,
          );
          await setDataInAsyncStorage('wsIsRunning', 'false');
          await setDataInAsyncStorage('wsForegroundServiceTerminated', 'true');
          await setDataInAsyncStorage(
            'foreground_service_last_stopped_at',
            String(Date.now()),
          );
          cleanupClipboardListeners();
          try {
            await notifee.stopForegroundService();
          } finally {
            await finishForegroundRuntime('failed');
          }
        });""",
        "supervised foreground polling loop",
    )


if __name__ == "__main__":
    main()

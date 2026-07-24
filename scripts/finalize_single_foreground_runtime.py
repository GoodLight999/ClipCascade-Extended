#!/usr/bin/env python3
"""Allow only one live clipboard/network runtime per JavaScript process."""
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
    path = root / "StartForegroundService.js"

    replace_once(
        path,
        """let foregroundServiceHandlerRegistered = false;

module.exports = async (inputData = null) => {""",
        """let foregroundServiceHandlerRegistered = false;
let activeForegroundRuntimeId = null;

module.exports = async (inputData = null) => {""",
        "foreground runtime singleton state",
    )

    replace_once(
        path,
        """    notifee.registerForegroundService(notification => {
    return new Promise(async () => {
      try {
        await setDataInAsyncStorage('foreground_service_state', 'handler-starting');""",
        """    notifee.registerForegroundService(notification => {
      return new Promise(resolve => {
        void (async () => {
          const runtimeId = `runtime-${Date.now()}-${Math.random()}`;
          if (activeForegroundRuntimeId != null) {
            await setDataInAsyncStorage(
              'foreground_service_state',
              'duplicate-runtime-suppressed',
            );
            await setDataInAsyncStorage(
              'foreground_service_duplicate_suppressed_at',
              String(Date.now()),
            );
            resolve();
            return;
          }
          activeForegroundRuntimeId = runtimeId;
          const finishForegroundRuntime = async state => {
            if (activeForegroundRuntimeId !== runtimeId) {
              resolve();
              return;
            }
            activeForegroundRuntimeId = null;
            await setDataInAsyncStorage('foreground_service_state', state);
            await setDataInAsyncStorage('foreground_service_instance_id', '');
            resolve();
          };
          try {
            await setDataInAsyncStorage('foreground_service_instance_id', runtimeId);
            await setDataInAsyncStorage('foreground_service_state', 'handler-starting');""",
        "foreground runtime lease",
    )

    replace_once(
        path,
        """        cleanupClipboardListeners();
        await notifee.stopForegroundService();
      }""",
        """        cleanupClipboardListeners();
        try {
          await notifee.stopForegroundService();
        } finally {
          await finishForegroundRuntime('failed');
        }
      }""",
        "release foreground runtime after fatal failure",
    )

    replace_exact(
        path,
        """            cleanupClipboardListeners();
            await notifee.stopForegroundService();
          };""",
        """            cleanupClipboardListeners();
            try {
              await notifee.stopForegroundService();
            } finally {
              await finishForegroundRuntime('stopped');
            }
          };""",
        2,
        "release P2S/P2P foreground runtime on stop",
    )

    replace_once(
        path,
        """      }
      });
    });""",
        """      }
        })().catch(async error => {
          const detail = String(error?.stack || error);
          if (activeForegroundRuntimeId === runtimeId) {
            activeForegroundRuntimeId = null;
          }
          try {
            await setDataInAsyncStorage(
              'foreground_service_error',
              detail.slice(0, 4000),
            );
            await setDataInAsyncStorage(
              'foreground_service_state',
              'handler-unhandled-failure',
            );
            await setDataInAsyncStorage('foreground_service_instance_id', '');
            await setDataInAsyncStorage('wsIsRunning', 'false');
            await setDataInAsyncStorage(
              'wsForegroundServiceTerminated',
              'true',
            );
          } finally {
            cleanupClipboardListeners();
            resolve();
          }
        });
      });
    });""",
        "synchronous Promise executor with terminal async catch",
    )


if __name__ == "__main__":
    main()

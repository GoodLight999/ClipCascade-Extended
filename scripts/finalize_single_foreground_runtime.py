#!/usr/bin/env python3
"""Allow one runtime and serialize forced restart handoff before replacement."""
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
        "import notifee, { AndroidImportance } from '@notifee/react-native';",
        """import notifee, { AndroidImportance } from '@notifee/react-native';
import {
  createForegroundRuntimeCoordinator,
  shouldPreserveOutboundQueue,
} from './ForegroundRuntimeCoordinator';""",
        "foreground runtime coordinator import",
    )

    replace_once(
        path,
        """let foregroundServiceHandlerRegistered = false;

module.exports = async (inputData = null) => {""",
        """let foregroundServiceHandlerRegistered = false;
const foregroundRuntimeCoordinator = createForegroundRuntimeCoordinator();

module.exports = async (inputData = null) => {""",
        "foreground runtime coordinator state",
    )

    replace_once(
        path,
        """    notifee.registerForegroundService(notification => {
    return new Promise(async () => {
      try {
        await setDataInAsyncStorage('foreground_service_state', 'handler-starting');""",
        """    notifee.registerForegroundService(notification => {
      return new Promise(resolve => {
        let runtimeLease = null;
        Promise.resolve()
          .then(async () => {
            const runtimeId = `runtime-${Date.now()}-${Math.random()}`;
            let runtimeAcceptingEvents = true;
            let runtimeStopReason = 'manual';
            const runtimeCanAcceptEvents = () =>
              runtimeAcceptingEvents && runtimeLease?.isActive() === true;
            const shouldPreserveRuntimeQueue = () =>
              shouldPreserveOutboundQueue(runtimeStopReason);
            const stopAcceptingRuntimeEvents = () => {
              runtimeAcceptingEvents = false;
            };
            const finishForegroundRuntime = async state => {
              stopAcceptingRuntimeEvents();
              if (!runtimeLease?.isActive()) {
                resolve();
                return;
              }
              await setDataInAsyncStorage('foreground_service_state', state);
              await setDataInAsyncStorage('foreground_service_instance_id', '');
              runtimeLease.finish();
              resolve();
            };
            runtimeLease = foregroundRuntimeCoordinator.acquire(
              runtimeId,
              async reason => {
                runtimeStopReason = String(reason || 'restart');
                stopAcceptingRuntimeEvents();
                await setDataInAsyncStorage(
                  'foreground_service_state',
                  `restart-stop-requested:${runtimeStopReason}`,
                );
                await setDataInAsyncStorage('wsIsRunning', 'false');
              },
            );
            if (!runtimeLease) {
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
            try {
              await setDataInAsyncStorage('foreground_service_instance_id', runtimeId);
              await setDataInAsyncStorage('foreground_service_state', 'handler-starting');""",
        "foreground runtime coordinated lease",
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
          })
          .catch(async error => {
            const detail = String(error?.stack || error);
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
              runtimeLease?.finish();
              resolve();
            }
          });
      });
    });""",
        "synchronous Promise executor with coordinated terminal cleanup",
    )

    replace_once(
        path,
        """  try {
    await setDataInAsyncStorage('foreground_service_state', 'notification-starting');""",
        """  try {
    if (inputData?.forceRestart === true) {
      await setDataInAsyncStorage(
        'foreground_service_state',
        'restart-waiting-for-old-runtime',
      );
      const restart = await foregroundRuntimeCoordinator.requestRestart(
        'forced-share-recovery',
      );
      if (!restart.stopped) {
        throw new Error(
          `Foreground runtime restart failed: ${restart.error || restart.runtimeId}`,
        );
      }
      await setDataInAsyncStorage('wsIsRunning', 'true');
      await setDataInAsyncStorage('wsForegroundServiceTerminated', 'false');
      await setDataInAsyncStorage(
        'foreground_service_state',
        restart.hadActiveRuntime
          ? 'restart-old-runtime-stopped'
          : 'restart-no-active-runtime',
      );
    }
    await setDataInAsyncStorage('foreground_service_state', 'notification-starting');""",
        "forced foreground runtime stop-before-start handoff",
    )


if __name__ == "__main__":
    main()

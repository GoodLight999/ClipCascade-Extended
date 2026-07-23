#!/usr/bin/env python3
"""Use persisted service state and bound UI stop waiting."""
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
    app = root / "App.js"

    replace_once(
        app,
        "import { getExtendedStrings, localizeRuntimeMessage } from './ExtendedI18n';",
        """import { getExtendedStrings, localizeRuntimeMessage } from './ExtendedI18n';
import {
  FOREGROUND_STOP_TIMEOUT_MS,
  hasForegroundStopTimedOut,
  nextRequestedServiceState,
} from './ServiceControlPolicy';""",
        "service control policy imports",
    )

    replace_once(
        app,
        """        const wsIsRunning_s =
          wsIsRunning === 'true' ? 'false' : 'true'; // toggle""",
        """        const persistedWsIsRunning = await getDataFromAsyncStorage(
          'wsIsRunning',
        );
        const wsIsRunning_s = nextRequestedServiceState(persistedWsIsRunning);""",
        "persisted foreground service toggle",
    )

    replace_once(
        app,
        """          // wait for 1 sec so that foreground service can be terminated
          setWsPageMessage('⌛ Stopping foreground service...');
          while (
            (await getDataFromAsyncStorage('wsForegroundServiceTerminated')) ===
            'false'
          ) {
            await new Promise(resolve => setTimeout(resolve, 100)); //100 ms
          }
          await notifee.cancelAllNotifications();
          setWsPageMessage('');
          setWsPageP2PMessage('');""",
        """          setWsPageMessage('⌛ Stopping foreground service...');
          const stopStartedAt = Date.now();
          let stopTimedOut = false;
          while (
            (await getDataFromAsyncStorage('wsForegroundServiceTerminated')) ===
            'false'
          ) {
            if (hasForegroundStopTimedOut(stopStartedAt, Date.now())) {
              stopTimedOut = true;
              break;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
          }
          if (stopTimedOut) {
            const timeoutDetail = `Foreground service did not acknowledge stop within ${FOREGROUND_STOP_TIMEOUT_MS} ms`;
            await setDataInAsyncStorage('foreground_service_error', timeoutDetail);
            await setDataInAsyncStorage('foreground_service_state', 'stop-timeout');
            await setDataInAsyncStorage('wsForegroundServiceTerminated', 'true');
            await setDataInAsyncStorage('wsIsRunning', 'false');
            await notifee.stopForegroundService();
            setWsPageMessage(`❌ ${timeoutDetail}`);
          } else {
            await setDataInAsyncStorage('foreground_service_error', '');
            setWsPageMessage('');
          }
          await notifee.cancelAllNotifications();
          setWsPageP2PMessage('');""",
        "bounded foreground service stop wait",
    )


if __name__ == "__main__":
    main()

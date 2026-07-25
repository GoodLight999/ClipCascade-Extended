#!/usr/bin/env python3
"""Use explicit service intents, owned control locking, and bounded stop waiting."""
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
import { planPendingShareStart } from './PendingShareStartPolicy';
import {
  FOREGROUND_STOP_TIMEOUT_MS,
  hasForegroundStopTimedOut,
  resolveRequestedServiceState,
} from './ServiceControlPolicy';""",
        "service and pending-share policy imports",
    )

    replace_once(
        app,
        """  const foregroundService = async () => {
    try {
      if ((await getDataFromAsyncStorage('enableWSButton')) === 'true') {
        await setDataInAsyncStorage('enableWSButton', 'false');""",
        """  const foregroundService = async (
    desiredState = null,
    forceRestart = false,
  ) => {
    let controlLockAcquired = false;
    try {
      if ((await getDataFromAsyncStorage('enableWSButton')) !== 'true') return;
      await setDataInAsyncStorage('enableWSButton', 'false');
      controlLockAcquired = true;""",
        "explicit foreground service intent and owned lock acquisition",
    )

    replace_once(
        app,
        """        const wsIsRunning_s =
          wsIsRunning === 'true' ? 'false' : 'true'; // toggle""",
        """        const persistedWsIsRunning = await getDataFromAsyncStorage(
          'wsIsRunning',
        );
        const requested = resolveRequestedServiceState(
          persistedWsIsRunning,
          desiredState,
          forceRestart,
        );
        const wsIsRunning_s = requested.nextState;
        if (requested.noOp) {
          setWsIsRunning(requested.persistedState);
          return;
        }""",
        "persisted explicit foreground service state",
    )

    replace_once(
        app,
        """        setWsIsRunning(wsIsRunning_s);
      }
    } catch (error) {""",
        """        setWsIsRunning(wsIsRunning_s);
    } catch (error) {""",
        "remove obsolete conditional lock scope",
    )

    replace_once(
        app,
        """    } finally {
      await setDataInAsyncStorage('enableWSButton', 'true');
    }""",
        """    } finally {
      if (controlLockAcquired) {
        await setDataInAsyncStorage('enableWSButton', 'true');
      }
    }""",
        "owner-only foreground control unlock",
    )

    replace_once(
        app,
        """            onPress={foregroundService}""",
        """            onPress={() => foregroundService()}""",
        "UI-only service toggle",
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

#!/usr/bin/env python3
"""Use explicit service intents, owned locking, and coordinated restart handoff."""
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
        """  const onDisplayNotification = async () => {""",
        """  const onDisplayNotification = async (
    forceRestart = false,
    restartReason = 'manual-start',
  ) => {""",
        "coordinated notification start API",
    )
    replace_once(
        app,
        """      // remove work manager notification if exists
      await notifee.cancelAllNotifications();

      // stop foreground service(if any)
      await notifee.stopForegroundService();

      // start foreground service
      const result = await StartForegroundService();""",
        """      // StartForegroundService serializes the transition and waits until
      // the Notifee callback owns a live runtime lease.
      const result = await StartForegroundService({
        forceRestart,
        restartReason,
      });""",
        "coordinated foreground start handoff",
    )

    replace_once(
        app,
        """        // start polling UI flags
        isMountedRef.current = true;
        pollUIFlags();""",
        """        // start polling UI flags with observable failure evidence
        isMountedRef.current = true;
        pollUIFlags().catch(error => {
          setInItError([true, String(error?.stack || error)]);
        });""",
        "supervised UI polling",
    )

    replace_once(
        app,
        """            setEnableWSPage(true);
            setDataInAsyncStorage('wsIsRunning', 'false');
            // start foreground service (work manager notification click handler)
            if (
              foregroundServiceStoppedRunning &&
              foregroundServiceStoppedRunning === 'true'
            ) {
              foregroundService();
            }""",
        """            setEnableWSPage(true);
            await setDataInAsyncStorage('wsIsRunning', 'false');
            // A recovered WorkManager request is an explicit start, never a
            // toggle based on stale persisted state.
            if (foregroundServiceStoppedRunning === 'true') {
              await foregroundService(
                'true',
                true,
                'work-manager-recovery',
              );
            }""",
        "explicit WorkManager recovery",
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
    restartReason = null,
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
        """        setWsPageMessage('');
        setWsPageP2PMessage('');
        await clearFiles();
        const wsIsRunning = await getDataFromAsyncStorage('wsIsRunning');""",
        """        setWsPageMessage('');
        setWsPageP2PMessage('');
        const wsIsRunning = await getDataFromAsyncStorage('wsIsRunning');""",
        "delay clearFiles until requested state is known",
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
        }
        if (desiredState == null) {
          await clearFiles();
        }""",
        "persisted explicit foreground service state",
    )

    replace_once(
        app,
        """          await onDisplayNotification();""",
        """          await onDisplayNotification(
            requested.forcedStart,
            restartReason ||
              (requested.forcedStart ? 'stale-runtime' : 'manual-start'),
          );""",
        "forward restart intent to runtime coordinator",
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

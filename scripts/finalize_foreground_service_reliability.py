#!/usr/bin/env python3
"""Make foreground-service registration idempotent and auto-start pending shares."""
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
        """function cleanupClipboardListeners() {
  DeviceEventEmitter.removeAllListeners('SHARED_TEXT');
  DeviceEventEmitter.removeAllListeners('SHARED_IMAGE');
  DeviceEventEmitter.removeAllListeners('SHARED_FILES');
  DeviceEventEmitter.removeAllListeners('onClipboardChange');
}

module.exports = async (inputData = null) => {""",
        """function cleanupClipboardListeners() {
  DeviceEventEmitter.removeAllListeners('SHARED_TEXT');
  DeviceEventEmitter.removeAllListeners('SHARED_IMAGE');
  DeviceEventEmitter.removeAllListeners('SHARED_FILES');
  DeviceEventEmitter.removeAllListeners('onClipboardChange');
}

let foregroundServiceHandlerRegistered = false;

module.exports = async (inputData = null) => {""",
        "foreground handler singleton state",
    )
    replace_once(
        service,
        """  // forground service
  notifee.registerForegroundService(notification => {""",
        """  // Register exactly once per JavaScript runtime. Re-registering the Notifee
  // handler on every Start press creates duplicate/stale service callbacks.
  if (!foregroundServiceHandlerRegistered) {
    foregroundServiceHandlerRegistered = true;
    notifee.registerForegroundService(notification => {""",
        "idempotent foreground handler registration",
    )
    replace_once(
        service,
        """    });
  });

  try {
    // Create a notification channel for the foreground service""",
        """      });
    });
  }

  try {
    await setDataInAsyncStorage('foreground_service_state', 'notification-starting');
    await setDataInAsyncStorage('foreground_service_error', '');
    // Create a notification channel for the foreground service""",
        "close foreground registration guard",
    )

    replace_once(
        service,
        """      try {
        const { NativeBridgeModule } = NativeModules;""",
        """      try {
        await setDataInAsyncStorage('foreground_service_state', 'handler-starting');
        await setDataInAsyncStorage('foreground_service_error', '');
        await setDataInAsyncStorage(
          'foreground_service_last_started_at',
          String(Date.now()),
        );
        const { NativeBridgeModule } = NativeModules;""",
        "foreground callback start evidence",
    )
    replace_once(
        service,
        """        pollFlagsLoop();
      } catch (error) {
        await setDataInAsyncStorage('wsStatusMessage', '❌ Error:' + error);
        cleanupClipboardListeners();
        await notifee.stopForegroundService();
      }""",
        """        await setDataInAsyncStorage('foreground_service_state', 'running');
        await setDataInAsyncStorage('foreground_service_error', '');
        pollFlagsLoop();
      } catch (error) {
        const detail = String(error?.stack || error);
        await setDataInAsyncStorage('foreground_service_error', detail.slice(0, 4000));
        await setDataInAsyncStorage('foreground_service_state', 'failed');
        await setDataInAsyncStorage('wsStatusMessage', '❌ Foreground service: ' + detail);
        await setDataInAsyncStorage('wsIsRunning', 'false');
        await setDataInAsyncStorage('wsForegroundServiceTerminated', 'true');
        await setDataInAsyncStorage(
          'foreground_service_last_stopped_at',
          String(Date.now()),
        );
        cleanupClipboardListeners();
        await notifee.stopForegroundService();
      }""",
        "foreground callback failure evidence",
    )
    replace_once(
        service,
        """    await notifee.displayNotification({
      title: 'ClipCascade',""",
        """    await notifee.displayNotification({
      title: 'ClipCascade Extended',""",
        "foreground notification product title",
    )
    replace_once(
        service,
        """    return [true, 'Foreground service is running'];
  } catch (error) {
    return [false, error];
  }""",
        """    await setDataInAsyncStorage('foreground_service_state', 'notification-displayed');
    await setDataInAsyncStorage('foreground_service_error', '');
    return [true, 'Foreground service is running'];
  } catch (error) {
    const detail = String(error?.stack || error);
    await setDataInAsyncStorage('foreground_service_error', detail.slice(0, 4000));
    await setDataInAsyncStorage('foreground_service_state', 'start-failed');
    await setDataInAsyncStorage('wsStatusMessage', '❌ Foreground service: ' + detail);
    await setDataInAsyncStorage('wsIsRunning', 'false');
    await setDataInAsyncStorage('wsForegroundServiceTerminated', 'true');
    return [false, detail];
  }""",
        "foreground notification start failure state",
    )

    for event_name, call, status in (
        (
            "SHARED_TEXT",
            "await enqueueOutboundClipboard(clipContent, 'text');",
            "share-text-enqueued",
        ),
        (
            "SHARED_IMAGE",
            "await enqueueOutboundClipboard(clipContent, 'image');",
            "share-image-enqueued",
        ),
        (
            "SHARED_FILES",
            "await enqueueOutboundClipboard(clipContent, 'files');",
            "share-files-enqueued",
        ),
    ):
        replace_once(
            service,
            call,
            call
            + "\n              await setDataInAsyncStorage('shared_payload_pending', 'false');"
            + f"\n              await setDataInAsyncStorage('shared_payload_status', '{status}');",
            f"{event_name} pending-share completion",
        )

    app = root / "App.js"
    replace_once(
        app,
        """            // start foreground service (work manager notification click handler)
            if (
              foregroundServiceStoppedRunning &&
              foregroundServiceStoppedRunning === 'true'
            ) {
              foregroundService();
            }""",
        """            const sharedPayloadPending = await getDataFromAsyncStorage(
              'shared_payload_pending',
            );
            if (sharedPayloadPending === 'true') {
              wsIsRunning_s = 'true';
              await setDataInAsyncStorage('wsIsRunning', 'true');
              await setDataInAsyncStorage('wsForegroundServiceTerminated', 'false');
              setWsIsRunning('true');
              await onDisplayNotification();
              await setDataInAsyncStorage('shared_payload_status', 'service-started-for-share');
            } else if (
              foregroundServiceStoppedRunning &&
              foregroundServiceStoppedRunning === 'true'
            ) {
              foregroundService();
            }""",
        "auto-start service for share on restored session",
    )
    replace_once(
        app,
        """        // Save data_s in data state hook
        setData(data_s);

        // Navigation to the websocket screen""",
        """        // Save data_s in data state hook
        setData(data_s);

        const sharedPayloadPending = await getDataFromAsyncStorage(
          'shared_payload_pending',
        );
        if (sharedPayloadPending === 'true') {
          await setDataInAsyncStorage('wsIsRunning', 'true');
          await setDataInAsyncStorage('wsForegroundServiceTerminated', 'false');
          setWsIsRunning('true');
          await onDisplayNotification();
          await setDataInAsyncStorage('shared_payload_status', 'service-started-after-login');
        }

        // Navigation to the websocket screen""",
        "auto-start service for share after login",
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Make foreground runtime ownership deterministic and recover pending shares."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_after_once(path: Path, marker: str, insertion: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(marker)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    end = text.index(marker) + len(marker)
    path.write_text(text[:end] + insertion + text[end:], encoding="utf-8")


def replace_exact(
    path: Path,
    old: str,
    new: str,
    expected: int,
    label: str,
) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} markers, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def insert_array_items(
    path: Path,
    declaration: str,
    items: tuple[str, ...],
    label: str,
) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(declaration) != 1:
        raise RuntimeError(
            f"{label}: expected one array declaration, found {text.count(declaration)}"
        )
    start = text.index(declaration)
    end = text.find("];", start)
    if end < 0:
        raise RuntimeError(f"{label}: array terminator not found")
    block = text[start:end]
    for item in items:
        if f"'{item}'" in block:
            raise RuntimeError(f"{label}: duplicate item already present: {item}")
    closing_line_start = text.rfind("\n", start, end) + 1
    indentation = text[closing_line_start:end]
    if indentation.strip() != "":
        raise RuntimeError(f"{label}: unexpected array terminator prefix")
    insertion = "".join(f"{indentation}'{item}',\n" for item in items)
    path.write_text(
        text[:closing_line_start] + insertion + text[closing_line_start:],
        encoding="utf-8",
    )


def wrap_listener_call(
    path: Path,
    start_marker: str,
    close_marker: str,
    wrapped_start: str,
    wrapped_close: str,
    label: str,
) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(start_marker) != 1:
        raise RuntimeError(
            f"{label}: expected one listener start, found {text.count(start_marker)}"
        )
    start = text.index(start_marker)
    close = text.find(close_marker, start)
    if close < 0:
        raise RuntimeError(f"{label}: listener close marker not found")
    text = (
        text[:start]
        + wrapped_start
        + text[start + len(start_marker) : close]
        + wrapped_close
        + text[close + len(close_marker) :]
    )
    path.write_text(text, encoding="utf-8")


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
        """const activeClipboardSubscriptions = new Set();

function trackClipboardSubscription(subscription) {
  if (subscription && typeof subscription.remove === 'function') {
    activeClipboardSubscriptions.add(subscription);
  }
  return subscription;
}

function removeClipboardSubscription(subscription) {
  if (!subscription) return;
  activeClipboardSubscriptions.delete(subscription);
  try {
    subscription.remove();
  } catch (_) {
    // Removing an already-closed native subscription is harmless.
  }
}

function cleanupClipboardListeners() {
  const subscriptions = Array.from(activeClipboardSubscriptions);
  activeClipboardSubscriptions.clear();
  for (const subscription of subscriptions) {
    try {
      subscription.remove();
    } catch (_) {
      // Best-effort cleanup must not hide the original service failure.
    }
  }
}

let foregroundServiceHandlerRegistered = false;

module.exports = async (inputData = null) => {""",
        "owned clipboard listener registry",
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
        marker = f"DeviceEventEmitter.addListener('{event_name}',"
        wrap_listener_call(
            service,
            marker,
            "\n        });",
            f"trackClipboardSubscription({marker}",
            "\n        }));",
            f"{event_name} owned subscription",
        )

    wrap_listener_call(
        service,
        "const clipboardOnChange = clipboardListener.addListener(",
        "\n        );",
        "const clipboardOnChange = trackClipboardSubscription(clipboardListener.addListener(",
        "\n        ));",
        "native clipboard owned subscription",
    )
    replace_exact(
        service,
        """              if (clipboardOnChange) {
                clipboardOnChange.remove();
              }""",
        """              removeClipboardSubscription(clipboardOnChange);""",
        2,
        "owned native clipboard stop cleanup",
    )

    app = root / "App.js"
    replace_once(
        app,
        """  const isMountedRef = useRef(true);""",
        """  const isMountedRef = useRef(true);
  const sessionReadyRef = useRef(false);
  const pendingShareStartInFlightRef = useRef(false);
  const pendingShareLastAttemptAtRef = useRef(null);""",
        "pending-share runtime refs",
    )
    insert_after_once(
        app,
        """  const [enableWSPage, setEnableWSPage] = useState(false);""",
        """

  useEffect(() => {
    sessionReadyRef.current = enableWSPage;
  }, [enableWSPage]);""",
        "session-ready synchronization after state declaration",
    )
    insert_array_items(
        app,
        "const POLL_KEYS = [",
        (
            "shared_payload_pending",
            "enableWSButton",
            "foreground_service_state",
            "foreground_service_heartbeat_at",
            "foreground_service_last_started_at",
        ),
        "pending-share polling fields",
    )
    insert_after_once(
        app,
        "      const latest = JSON.parse(json);",
        """
      const pendingShareNow = Date.now();
      const pendingSharePlan = planPendingShareStart({
        sessionReady: sessionReadyRef.current,
        payloadPending: latest.shared_payload_pending === 'true',
        serviceRequested: latest.wsIsRunning === 'true',
        serviceState: latest.foreground_service_state,
        heartbeatAt: latest.foreground_service_heartbeat_at,
        lastStartedAt: latest.foreground_service_last_started_at,
        buttonEnabled: latest.enableWSButton !== 'false',
        startInFlight: pendingShareStartInFlightRef.current,
        lastAttemptAt: pendingShareLastAttemptAtRef.current,
        now: pendingShareNow,
      });
      if (pendingSharePlan.start) {
        pendingShareStartInFlightRef.current = true;
        pendingShareLastAttemptAtRef.current = pendingShareNow;
        await setDataInAsyncStorage(
          'shared_payload_status',
          `service-start-requested:${pendingSharePlan.reason}`,
        );
        try {
          await foregroundService('true', pendingSharePlan.forceRestart);
        } finally {
          pendingShareStartInFlightRef.current = false;
        }
      }""",
        "unified heartbeat-aware pending-share runtime start",
    )


if __name__ == "__main__":
    main()

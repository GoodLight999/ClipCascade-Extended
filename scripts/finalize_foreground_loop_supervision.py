#!/usr/bin/env python3
"""Ensure asynchronous foreground work cannot orphan the runtime lease."""
from __future__ import annotations

import argparse
from pathlib import Path

from foreground_async_supervision import apply as apply_detached_supervision
from guard_runtime_queue_admission import apply as guard_runtime_queue_admission
from guard_runtime_transport_activity import apply as guard_runtime_transport_activity
from supervise_error_handlers import apply as supervise_error_handlers
from supervise_host_callbacks import apply as supervise_host_callbacks
from wire_detached_task_supervisor import apply as wire_detached_supervisor
from wire_p2p_signaling_validation import apply as wire_p2p_signaling_validation


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
        """        pollFlagsLoop().catch(async error => {
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
        "foreground polling-loop failure body",
    )
    apply_detached_supervision(root)
    wire_detached_supervisor(root)
    guard_runtime_queue_admission(root)
    supervise_host_callbacks(root)
    supervise_error_handlers(root)
    guard_runtime_transport_activity(root)
    wire_p2p_signaling_validation(root)


if __name__ == "__main__":
    main()

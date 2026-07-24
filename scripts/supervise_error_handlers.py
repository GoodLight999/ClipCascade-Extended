"""Prevent error-reporting Promise chains from creating new unhandled failures."""
from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def apply(root: Path) -> None:
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        """            peerOpChains[peerId] = current.catch(async error => {
              await setDataInAsyncStorage(
                'p2p_last_peer_operation_error',
                `${peerId}:${String(error?.stack || error)}`.slice(0, 1000),
              );
            });""",
        """            peerOpChains[peerId] = current.catch(error => {
              runDetached(`peer-operation-record:${peerId}`, () =>
                setDataInAsyncStorage(
                  'p2p_last_peer_operation_error',
                  `${peerId}:${String(error?.stack || error)}`.slice(0, 1000),
                ),
              );
            });""",
        "supervised peer-operation error recorder",
    )

    text = replace_once(
        text,
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
        """        pollFlagsLoop().catch(error => {
          runDetached('foreground-poll-loop-failure', async () => {
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
          });
        });""",
        "supervised polling-loop failure handler",
    )

    text = replace_once(
        text,
        """          })
          .catch(async error => {
            const detail = String(error?.stack || error);
            if (
              runtimeId != null &&
              activeForegroundRuntimeId === runtimeId
            ) {
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
          });""",
        """          })
          .catch(error => {
            runDetached('foreground-handler-unhandled-failure', async () => {
              const detail = String(error?.stack || error);
              if (
                runtimeId != null &&
                activeForegroundRuntimeId === runtimeId
              ) {
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
          });""",
        "supervised terminal foreground error handler",
    )

    path.write_text(text, encoding="utf-8")

"""Prevent callbacks from appending durable items after runtime shutdown begins."""
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
        """            activeForegroundRuntimeId = runtimeId;
            const finishForegroundRuntime = async state => {
              if (activeForegroundRuntimeId !== runtimeId) {
                resolve();
                return;
              }
              activeForegroundRuntimeId = null;
              await setDataInAsyncStorage('foreground_service_state', state);
              await setDataInAsyncStorage('foreground_service_instance_id', '');
              resolve();
            };""",
        """            activeForegroundRuntimeId = runtimeId;
            let runtimeAcceptingEvents = true;
            const runtimeCanAcceptEvents = () =>
              runtimeAcceptingEvents && activeForegroundRuntimeId === runtimeId;
            const stopAcceptingRuntimeEvents = () => {
              runtimeAcceptingEvents = false;
            };
            const finishForegroundRuntime = async state => {
              stopAcceptingRuntimeEvents();
              if (activeForegroundRuntimeId !== runtimeId) {
                resolve();
                return;
              }
              activeForegroundRuntimeId = null;
              await setDataInAsyncStorage('foreground_service_state', state);
              await setDataInAsyncStorage('foreground_service_instance_id', '');
              resolve();
            };""",
        "runtime event-admission lease",
    )

    text = replace_once(
        text,
        """        const enqueueOutboundClipboard = async (
          clipContent,
          type_ = 'text',
        ) => {
          await outboundQueue.enqueue(String(clipContent), type_);
          await updateOutboundQueueStatus('queued');
          await flushOutboundQueue();
        };""",
        """        const enqueueOutboundClipboard = async (
          clipContent,
          type_ = 'text',
        ) => {
          const enqueueResult = await outboundQueue.enqueue(
            String(clipContent),
            type_,
            runtimeCanAcceptEvents,
          );
          if (enqueueResult.cancelled) {
            await updateOutboundQueueStatus('ignored-after-runtime-stop');
            return false;
          }
          await updateOutboundQueueStatus('queued');
          if (!runtimeCanAcceptEvents()) {
            await updateOutboundQueueStatus('queued-before-runtime-stop');
            return false;
          }
          await flushOutboundQueue();
          return true;
        };""",
        "runtime-guarded outbound enqueue",
    )

    text = replace_once(
        text,
        """          stopServicesP2S = async () => {
            p2sAckTracker.cancel();""",
        """          stopServicesP2S = async () => {
            stopAcceptingRuntimeEvents();
            p2sAckTracker.cancel();""",
        "close P2S event admission before queue clear",
    )
    text = replace_once(
        text,
        """          stopServicesP2P = async () => {
            clearSignalingReconnect();""",
        """          stopServicesP2P = async () => {
            stopAcceptingRuntimeEvents();
            clearSignalingReconnect();""",
        "close P2P event admission before queue clear",
    )

    text = replace_once(
        text,
        """      } catch (error) {
        const detail = String(error?.stack || error);
        await setDataInAsyncStorage('foreground_service_error', detail.slice(0, 4000));""",
        """      } catch (error) {
        stopAcceptingRuntimeEvents();
        const detail = String(error?.stack || error);
        await setDataInAsyncStorage('foreground_service_error', detail.slice(0, 4000));""",
        "close event admission on foreground callback failure",
    )

    path.write_text(text, encoding="utf-8")

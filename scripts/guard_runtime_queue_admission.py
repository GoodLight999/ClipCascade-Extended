"""Prevent callbacks from appending durable items after runtime shutdown begins."""
from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def replace_exact(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} markers, found {count}")
    return text.replace(old, new)


def require(text: str, marker: str, label: str) -> None:
    if marker not in text:
        raise RuntimeError(f"{label}: missing marker {marker!r}")


def apply(root: Path) -> None:
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    # The single-runtime finalizer owns the canonical lease, stop reason and
    # admission predicate. Queue hardening attaches to that one ownership model.
    for marker, label in (
        ("foregroundRuntimeCoordinator.acquire(", "coordinated runtime lease"),
        ("const runtimeCanAcceptEvents = () =>", "runtime admission predicate"),
        (
            "runtimeAcceptingEvents && runtimeLease?.isActive() === true",
            "null-safe active lease admission",
        ),
        ("let runtimeStopReason = 'manual'", "explicit runtime stop reason"),
        ("const shouldPreserveRuntimeQueue = () =>", "queue preservation predicate"),
        ("shouldPreserveOutboundQueue(runtimeStopReason)", "tested stop-reason policy"),
        ("const stopAcceptingRuntimeEvents = () =>", "runtime admission close"),
        ("const finishForegroundRuntime = async state =>", "runtime terminal release"),
    ):
        require(text, marker, label)

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
            toggle = false;
            // 1) Stop clipboard listening""",
        """          stopServicesP2S = async () => {
            toggle = false;
            stopAcceptingRuntimeEvents();
            // 1) Stop clipboard listening""",
        "close P2S event admission after in-flight reset and before queue handling",
    )
    text = replace_once(
        text,
        """          stopServicesP2P = async () => {
            clearSignalingReconnect();""",
        """          stopServicesP2P = async () => {
            stopAcceptingRuntimeEvents();
            clearSignalingReconnect();""",
        "close P2P event admission before queue handling",
    )

    text = replace_exact(
        text,
        """            cancelOutboundRetry();
            await outboundQueue.clear();
            await updateOutboundQueueStatus('cleared-on-manual-stop');""",
        """            cancelOutboundRetry();
            if (shouldPreserveRuntimeQueue()) {
              await updateOutboundQueueStatus(
                `preserved-for-${runtimeStopReason}`,
              );
            } else {
              await outboundQueue.clear();
              await updateOutboundQueueStatus('cleared-on-manual-stop');
            }""",
        2,
        "P2S/P2P stop-aware queue preservation",
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

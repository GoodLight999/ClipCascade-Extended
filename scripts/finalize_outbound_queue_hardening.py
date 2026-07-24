#!/usr/bin/env python3
"""Apply guarded post-integration fixes to the durable outbound queue."""
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
    service = root / "StartForegroundService.js"

    replace_once(
        service,
        """        let sendClipBoardTransport = null;
        let outboundFlushRunning = false;
        let outboundFlushRequested = false;""",
        """        let sendClipBoardTransport = null;
        let p2pTransportReady = () => false;
        let outboundFlushRunning = false;
        let outboundFlushRequested = false;
        let outboundRetryTimer = null;""",
        "declare queue runtime controls",
    )
    replace_once(
        service,
        """        const flushOutboundQueue = async () => {""",
        """        const cancelOutboundRetry = () => {
          if (outboundRetryTimer != null) {
            clearTimeout(outboundRetryTimer);
            outboundRetryTimer = null;
          }
        };

        const scheduleOutboundRetry = failures => {
          cancelOutboundRetry();
          const exponent = Math.max(0, Number(failures || 1) - 1);
          const delay = Math.min(60000, 1000 * 2 ** exponent);
          outboundRetryTimer = setTimeout(() => {
            outboundRetryTimer = null;
            flushOutboundQueue();
          }, delay);
        };

        const flushOutboundQueue = async () => {""",
        "queue retry helpers",
    )
    replace_once(
        service,
        """          outboundFlushRunning = true;
          try {""",
        """          cancelOutboundRetry();
          outboundFlushRunning = true;
          try {""",
        "cancel stale retry before flush",
    )
    replace_once(
        service,
        """                  await outboundQueue.acknowledge(item.id);
                  await updateOutboundQueueStatus('sent');""",
        """                  await outboundQueue.acknowledge(item.id);
                  cancelOutboundRetry();
                  await updateOutboundQueueStatus('sent');""",
        "cancel retry after successful send",
    )
    replace_once(
        service,
        """                  if (!failure.dropped) {
                    break;
                  }""",
        """                  if (!failure.dropped) {
                    scheduleOutboundRetry(failure.item?.failures);
                    break;
                  }""",
        "schedule retry after send exception",
    )
    replace_once(
        service,
        """          let liveConnectionsCount = 0; // Track open DataChannels""",
        """          let liveConnectionsCount = 0; // Track open DataChannels
          p2pTransportReady = () => liveConnectionsCount > 0;""",
        "bind P2P readiness probe",
    )
    replace_once(
        service,
        """            if (liveConnectionsCount <= 0) return false;""",
        """            if (!p2pTransportReady()) return false;""",
        "use P2P readiness probe",
    )
    replace_once(
        service,
        """          await setDataInAsyncStorage(
            'outbound_queue_status',
            JSON.stringify({...snapshot, state}),
          );""",
        """          await setDataInAsyncStorage(
            'outbound_queue_status',
            {...snapshot, state},
          );""",
        "store queue diagnostics as an object",
    )
    replace_once(
        service,
        """        await updateOutboundQueueStatus('service-started');""",
        """        await updateOutboundQueueStatus('service-started');
        await flushOutboundQueue();""",
        "flush after transport function initialization",
    )
    replace_exact(
        service,
        """            await outboundQueue.clear();""",
        """            cancelOutboundRetry();
            await outboundQueue.clear();""",
        2,
        "cancel retry on manual stop",
    )


if __name__ == "__main__":
    main()

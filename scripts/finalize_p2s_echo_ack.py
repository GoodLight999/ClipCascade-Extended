#!/usr/bin/env python3
"""Keep P2S items durable until the server echoes their delivery metadata."""
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
        "import { createDurableOutboundQueue } from './DurableOutboundQueue';",
        """import { createDurableOutboundQueue } from './DurableOutboundQueue';
import { createP2SAckTracker } from './P2SAckTracker';""",
        "P2S ACK tracker import",
    )
    replace_once(
        service,
        """        const outboundQueue = createDurableOutboundQueue(outboundQueueScope);
        let sendClipBoardTransport = null;""",
        """        const outboundQueue = createDurableOutboundQueue(outboundQueueScope);
        const p2sAckTracker = createP2SAckTracker({timeoutMs: 10000});
        let sendClipBoardTransport = null;""",
        "P2S ACK tracker instance",
    )
    replace_once(
        service,
        """                  if (!sent) {
                    await updateOutboundQueueStatus('waiting-for-transport');
                    break;
                  }
                  await outboundQueue.acknowledge(item.id);""",
        """                  if (!sent) {
                    await updateOutboundQueueStatus('waiting-for-transport');
                    break;
                  }
                  if (sent === 'awaiting-p2s-ack') {
                    await updateOutboundQueueStatus('awaiting-p2s-ack');
                    break;
                  }
                  await outboundQueue.acknowledge(item.id);""",
        "retain P2S item until echo ACK",
    )

    replace_once(
        service,
        """                  await clearFiles();
                  toggle = false;
                  await setDataInAsyncStorage(""",
        """                  await clearFiles();
                  await setDataInAsyncStorage(""",
        "do not unlock P2S queue for unrelated inbound messages",
    )
    replace_once(
        service,
        """                    const body = JSON.parse(message.body);
                    let cb = String(body.payload);""",
        """                    const body = JSON.parse(message.body);
                    const echoedDeliveryId =
                      body.metadata?.extendedDeliveryId ?? null;
                    const activeAck = p2sAckTracker.acknowledge(
                      echoedDeliveryId,
                    );
                    const queuedForAck = echoedDeliveryId
                      ? await outboundQueue.peek()
                      : null;
                    if (activeAck || queuedForAck?.id === echoedDeliveryId) {
                      toggle = false;
                      await outboundQueue.acknowledge(echoedDeliveryId);
                      await updateOutboundQueueStatus(
                        activeAck
                          ? 'p2s-echo-acknowledged'
                          : 'p2s-late-echo-acknowledged',
                      );
                    }
                    let cb = String(body.payload);""",
        "acknowledge active or late matching P2S echo",
    )

    replace_once(
        service,
        """          sendClipBoardP2S = async (clipContent, type_ = 'text') => {
            try {
              await clearFiles();""",
        """          sendClipBoardP2S = async (
            clipContent,
            type_ = 'text',
            deliveryId = null,
          ) => {
            try {
              await clearFiles();
              const p2sDeliveryId = deliveryId || (await generateUuid());""",
        "P2S delivery ID signature",
    )
    replace_once(
        service,
        """                          payload: String(clipContent),
                          type: type_,
                        }),
                      });
                      previous_clipboard_content_hash = hcb;
                      toggle = true;""",
        """                          payload: String(clipContent),
                          type: type_,
                          metadata: {
                            extendedDeliveryId: p2sDeliveryId,
                          },
                        }),
                      });
                      previous_clipboard_content_hash = hcb;
                      toggle = true;
                      p2sAckTracker.begin(p2sDeliveryId, timedOutId => {
                        toggle = false;
                        Promise.resolve()
                          .then(async () => {
                            const failure = await outboundQueue.recordFailure(
                              timedOutId,
                              'P2S server echo acknowledgement timed out',
                            );
                            await updateOutboundQueueStatus(
                              failure.dropped
                                ? 'p2s-ack-timeout-dropped'
                                : 'p2s-ack-timeout',
                            );
                            if (!failure.dropped) {
                              scheduleOutboundRetry(failure.item?.failures);
                            }
                          })
                          .catch(async error => {
                            await setDataInAsyncStorage(
                              'wsStatusMessage',
                              '❌ P2S ACK Error: ' + error,
                            );
                          });
                      });
                      return 'awaiting-p2s-ack';""",
        "P2S delivery metadata and timeout",
    )

    replace_once(
        service,
        """          if (server_mode === 'P2S') {
            if (!stompClient || !stompClient.connected || toggle) return false;
            const result = await sendClipBoardP2S(clipContent, type_);
            return result !== false;
          }""",
        """          if (server_mode === 'P2S') {
            if (!stompClient || !stompClient.connected || toggle) return false;
            const result = await sendClipBoardP2S(
              clipContent,
              type_,
              deliveryId,
            );
            return result === 'awaiting-p2s-ack'
              ? result
              : result !== false;
          }""",
        "forward P2S delivery ID",
    )

    # Any transport loss invalidates the in-memory flight but not the durable item.
    replace_once(
        service,
        """            onDisconnect: async () => {
              block_image_once = false;""",
        """            onDisconnect: async () => {
              p2sAckTracker.cancel();
              toggle = false;
              block_image_once = false;""",
        "cancel P2S ACK on STOMP disconnect",
    )
    replace_once(
        service,
        """            onWebSocketClose: async event => {
              block_image_once = false;""",
        """            onWebSocketClose: async event => {
              p2sAckTracker.cancel();
              toggle = false;
              block_image_once = false;""",
        "cancel P2S ACK on WebSocket close",
    )
    replace_once(
        service,
        """          stopServicesP2S = async () => {
            // 1) Stop clipboard listening""",
        """          stopServicesP2S = async () => {
            p2sAckTracker.cancel();
            toggle = false;
            // 1) Stop clipboard listening""",
        "cancel P2S ACK on manual stop",
    )


if __name__ == "__main__":
    main()

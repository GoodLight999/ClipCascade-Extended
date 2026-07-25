#!/usr/bin/env python3
"""Install explicit durable transport outcomes and upstream-compatible P2S ACKs."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def replace_block(text: str, start: str, end: str, new: str, label: str) -> str:
    start_index = text.find(start)
    if start_index < 0:
        raise RuntimeError(f"{label}: start marker not found")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise RuntimeError(f"{label}: end marker not found")
    return text[:start_index] + new + text[end_index:]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "import { createDurableOutboundQueue } from './DurableOutboundQueue';",
        """import { createDurableOutboundQueue } from './DurableOutboundQueue';
import {
  createP2SReceiptTracker,
  shouldAcknowledgeP2SDelivery,
} from './P2SReceiptTracker';
import { OUTBOUND_DELIVERY } from './OutboundDeliveryPolicy';
import { applyOutboundDeliveryResult } from './OutboundDeliveryExecutor';
import {
  LOCAL_FEEDBACK_WINDOW_MS,
  P2S_ECHO_WINDOW_MS,
  createOneShotContentGuard,
} from './OneShotContentGuard';""",
        "delivery policy imports",
    )

    text = replace_once(
        text,
        """        let previous_clipboard_content_hash = '';
        let toggle = false; // p2s toggle
        let block_image_once = false;""",
        """        const clipboardFeedbackGuard = createOneShotContentGuard({
          windowMs: LOCAL_FEEDBACK_WINDOW_MS,
          clearOnMismatch: true,
        });
        const p2sEchoGuard = createOneShotContentGuard({
          windowMs: P2S_ECHO_WINDOW_MS,
          clearOnMismatch: false,
        });
        let toggle = false; // one in-flight P2S receipt
        let acknowledgeP2SDelivery = null;""",
        "typed clipboard feedback guards",
    )

    text = replace_once(
        text,
        """        const outboundQueue = createDurableOutboundQueue(outboundQueueScope);
        const p2sInboundErrorPolicy = createInboundErrorCoalescer({""",
        """        const outboundQueue = createDurableOutboundQueue(outboundQueueScope);
        const p2sReceiptTracker = createP2SReceiptTracker({timeoutMs: 10000});
        let p2sReceiptTimeoutFailures = 0;
        const p2sInboundErrorPolicy = createInboundErrorCoalescer({""",
        "P2S receipt tracker instance",
    )

    text = replace_once(
        text,
        """        // hash clipboard content
        const hashCB = async (input, seed = 0) => {
          return String(xxHash32(input, seed));
        };

        //check if clipboard content changed
        const newCB = async hcb => {
          return previous_clipboard_content_hash !== hcb;
        };

""",
        """        // Typed one-shot guards use byte length plus xxHash. The length makes
        // an accidental 32-bit collision materially less likely to suppress a user copy.
        const hashCB = async (input, seed = 0) => {
          const content = String(input);
          return `${Buffer.byteLength(content, 'utf8')}:${String(
            xxHash32(content, seed),
          )}`;
        };

""",
        "typed clipboard fingerprint",
    )

    text = replace_once(
        text,
        """                  const sent = await sendClipBoardTransport(
                    item.content,
                    item.type,
                    item.id,
                  );
                  if (!sent) {
                    await updateOutboundQueueStatus('waiting-for-transport');
                    break;
                  }
                  await outboundQueue.acknowledge(item.id);
                  cancelOutboundRetry();
                  await updateOutboundQueueStatus('sent');""",
        """                  const transportResult = await sendClipBoardTransport(
                    item.content,
                    item.type,
                    item.id,
                  );
                  const delivery = await applyOutboundDeliveryResult({
                    deliveryId: item.id,
                    transportResult,
                    peek: () => outboundQueue.peek(),
                    acknowledge: id => outboundQueue.acknowledge(id),
                    updateStatus: updateOutboundQueueStatus,
                  });
                  if (delivery.action === 'wait') break;""",
        "explicit outbound delivery result",
    )

    marker = """        if (server_mode === 'P2S') {
          // websocket stomp client"""
    helper = """        const applyInboundClipboard = async (content, type, hashValue) => {
          const marksFeedback = type === 'text' || type === 'image';
          if (marksFeedback) {
            clipboardFeedbackGuard.mark(type, hashValue, Date.now());
          }
          try {
            if (type === 'text') {
              Clipboard.setString(content);
            } else if (type === 'image') {
              await NativeBridgeModule.copyBase64ImageToClipboardUsingCache(
                content,
              );
            } else if (type === 'files') {
              await showFilesDownloadNotification(
                RUNTIME_TEXT.notificationDownloadFiles,
              );
              files_in_memory = content;
              await setDataInAsyncStorage('filesAvailableToDownload', 'true');
            }
          } catch (error) {
            if (marksFeedback) clipboardFeedbackGuard.clear();
            throw error;
          }
        };

        const initializeP2SAcknowledgement = () => {
          acknowledgeP2SDelivery = async (deliveryId, source) => {
            const activeReceipt = p2sReceiptTracker.acknowledge(deliveryId);
            const queued = await outboundQueue.peek();
            if (
              !shouldAcknowledgeP2SDelivery({
                activeReceiptMatched: activeReceipt,
                queuedHeadId: queued?.id || null,
                deliveryId,
              })
            ) {
              return false;
            }
            toggle = false;
            p2sReceiptTimeoutFailures = 0;
            await setDataInAsyncStorage('p2s_receipt_timeout_count', '0');
            await outboundQueue.acknowledge(deliveryId);
            await updateOutboundQueueStatus(
              activeReceipt
                ? `p2s-${source}-acknowledged`
                : `p2s-late-${source}-acknowledged`,
            );
            await flushOutboundQueue();
            return true;
          };
        };

"""
    if text.count(marker) != 1:
        raise RuntimeError("inbound helper insertion marker missing or duplicated")
    text = text.replace(marker, helper + marker, 1)
    text = replace_once(
        text,
        marker,
        """        if (server_mode === 'P2S') {
          initializeP2SAcknowledgement();
          // websocket stomp client""",
        "initialize P2S acknowledgement",
    )

    text = replace_block(
        text,
        "                      if (message && message.body) {",
        "                      p2sInboundErrorPolicy.reset();",
        """                      if (message && message.body) {
                        const body = JSON.parse(message.body);
                        let cb = String(body.payload);
                        const type_ = body.type ?? 'text';

                        if (cipher_enabled === 'true') {
                          try {
                            cb = await decrypt(JSON.parse(cb));
                          } catch (error) {
                            throw new Error(
                              `Unable to decrypt P2S payload. Check the encryption setting and shared key: ${error.message}`,
                            );
                          }
                        }

                        const hcb = await hashCB(cb);
                        const echo = p2sEchoGuard.consume(type_, hcb, Date.now());
                        if (echo.suppress) {
                          const ownDeliveryId = echo.metadata?.deliveryId;
                          if (ownDeliveryId && acknowledgeP2SDelivery) {
                            await acknowledgeP2SDelivery(ownDeliveryId, 'echo');
                          }
                          await updateOutboundQueueStatus(
                            'p2s-self-echo-suppressed',
                          );
                        } else if (
                          await validateClipboardSize(cb, type_, 'Inbound')
                        ) {
                          if (!runtimeCanAcceptEvents()) return;
                          await applyInboundClipboard(cb, type_, hcb);
                        }
                      }
""",
        "P2S inbound receipt and feedback handling",
    )

    text = replace_block(
        text,
        "          sendClipBoardP2S = async",
        "          // stop events and connection P2S",
        """          sendClipBoardP2S = async (
            clipContent,
            type_ = 'text',
            deliveryId = null,
          ) => {
            try {
              if (!runtimeCanAcceptEvents()) return OUTBOUND_DELIVERY.WAITING;
              await clearFiles();
              if (!stompClient || !stompClient.connected || toggle) {
                return OUTBOUND_DELIVERY.WAITING;
              }
              if (
                (type_ === 'image' && enable_image_sharing === 'false') ||
                (type_ === 'files' && enable_file_sharing === 'false')
              ) {
                await updateOutboundQueueStatus(
                  `policy-discarded-${type_}-disabled`,
                );
                return OUTBOUND_DELIVERY.POLICY_DISCARDED;
              }
              if (!(await validateClipboardSize(clipContent, type_, 'Outbound'))) {
                return OUTBOUND_DELIVERY.POLICY_DISCARDED;
              }

              if (type_ === 'image') {
                clipContent = await NativeBridgeModule.getFileAsBase64(
                  clipContent,
                );
              } else if (type_ === 'files') {
                const temp = {};
                const file_paths = parseOutboundFileUris(clipContent);
                for (const file_path of file_paths) {
                  temp[await NativeBridgeModule.getFileName(file_path)] =
                    await NativeBridgeModule.getFileAsBase64(file_path);
                }
                clipContent = JSON.stringify(temp);
              }

              const hcb = await hashCB(clipContent);
              const feedback = clipboardFeedbackGuard.consume(
                type_,
                hcb,
                Date.now(),
              );
              if (feedback.suppress) {
                await updateOutboundQueueStatus('feedback-suppressed');
                return OUTBOUND_DELIVERY.FEEDBACK_SUPPRESSED;
              }

              const receiptId = deliveryId || (await generateUuid());
              let outboundContent = clipContent;
              if (cipher_enabled === 'true') {
                outboundContent = await encrypt(outboundContent);
              }

              toggle = true;
              p2sReceiptTracker.begin(receiptId, timedOutId => {
                toggle = false;
                runRuntimeDetached('p2s-receipt-timeout', async () => {
                  const queued = await outboundQueue.peek();
                  if (queued?.id !== timedOutId) return;
                  p2sReceiptTimeoutFailures += 1;
                  await setDataInAsyncStorage(
                    'p2s_receipt_timeout_count',
                    String(p2sReceiptTimeoutFailures),
                  );
                  await updateOutboundQueueStatus('p2s-receipt-timeout');
                  // A missing receipt is a transport failure, not proof of a bad
                  // payload. Never consume the finite permanent-error budget.
                  scheduleOutboundRetry(p2sReceiptTimeoutFailures);
                });
              });
              stompClient.watchForReceipt(receiptId, () => {
                runRuntimeDetached('p2s-receipt', async () => {
                  await acknowledgeP2SDelivery?.(receiptId, 'receipt');
                });
              });
              p2sEchoGuard.mark(type_, hcb, Date.now(), {
                deliveryId: receiptId,
              });
              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ Connected - Broadcasting',
              );
              try {
                stompClient.publish({
                  destination: SEND_DESTINATION,
                  headers: {receipt: receiptId},
                  body: JSON.stringify({
                    payload: String(outboundContent),
                    type: type_,
                  }),
                });
              } catch (error) {
                toggle = false;
                p2sReceiptTracker.cancel();
                p2sEchoGuard.clear();
                if (!stompClient?.connected) return OUTBOUND_DELIVERY.WAITING;
                throw error;
              }
              return OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT;
            } catch (error) {
              toggle = false;
              p2sReceiptTracker.cancel();
              p2sEchoGuard.clear();
              throw error;
            }
          };

""",
        "P2S receipt-based send",
    )

    text = replace_once(
        text,
        """            onDisconnect: () => {
              runRuntimeDetached('p2s-disconnect', async () => {
                toggle = false;""",
        """            onDisconnect: () => {
              runRuntimeDetached('p2s-disconnect', async () => {
                p2sReceiptTracker.cancel();
                p2sEchoGuard.clear();
                acknowledgeP2SDelivery = null;
                toggle = false;""",
        "P2S disconnect receipt cleanup",
    )
    text = replace_once(
        text,
        """            onWebSocketClose: event => {
              runRuntimeDetached('p2s-websocket-close', async () => {
                toggle = false;""",
        """            onWebSocketClose: event => {
              runRuntimeDetached('p2s-websocket-close', async () => {
                p2sReceiptTracker.cancel();
                p2sEchoGuard.clear();
                acknowledgeP2SDelivery = null;
                toggle = false;""",
        "P2S WebSocket close receipt cleanup",
    )
    text = replace_once(
        text,
        """          stopServicesP2S = async () => {
            stopAcceptingRuntimeEvents();
            toggle = false;""",
        """          stopServicesP2S = async () => {
            stopAcceptingRuntimeEvents();
            p2sReceiptTracker.cancel();
            p2sEchoGuard.clear();
            acknowledgeP2SDelivery = null;
            toggle = false;""",
        "P2S stop receipt cleanup",
    )

    text = replace_block(
        text,
        "          sendClipBoardP2P = async",
        "          // stop events and connection P2P",
        """          sendClipBoardP2P = async (
            clipContent,
            type_ = 'text',
            deliveryId = null,
          ) => {
            try {
              if (!runtimeCanAcceptEvents()) return OUTBOUND_DELIVERY.WAITING;
              await clearFiles();
              if (
                (type_ === 'image' && enable_image_sharing === 'false') ||
                (type_ === 'files' && enable_file_sharing === 'false')
              ) {
                await updateOutboundQueueStatus(
                  `policy-discarded-${type_}-disabled`,
                );
                return OUTBOUND_DELIVERY.POLICY_DISCARDED;
              }
              if (!(await validateClipboardSize(clipContent, type_, 'Outbound'))) {
                return OUTBOUND_DELIVERY.POLICY_DISCARDED;
              }

              if (type_ === 'image') {
                clipContent = await NativeBridgeModule.getFileAsBase64(
                  clipContent,
                );
              } else if (type_ === 'files') {
                const temp = {};
                const file_paths = parseOutboundFileUris(clipContent);
                for (const file_path of file_paths) {
                  temp[await NativeBridgeModule.getFileName(file_path)] =
                    await NativeBridgeModule.getFileAsBase64(file_path);
                }
                clipContent = JSON.stringify(temp);
              }

              const hcb = await hashCB(clipContent);
              const feedback = clipboardFeedbackGuard.consume(
                type_,
                hcb,
                Date.now(),
              );
              if (feedback.suppress) {
                await updateOutboundQueueStatus('feedback-suppressed');
                return OUTBOUND_DELIVERY.FEEDBACK_SUPPRESSED;
              }

              await resetSendingFragmentId();
              const rawPayloadSizeInBytes = Buffer.byteLength(
                clipContent,
                'utf8',
              );
              if (cipher_enabled === 'true') {
                clipContent = await encrypt(clipContent);
              }

              const fragments = await fragmentString(clipContent, FRAGMENT_SIZE);
              const metadata = {
                id: deliveryId || (await generateUuid()),
                isFragmented: fragments.length > 1,
                index: 0,
                totalFragments: fragments.length,
                combinedRawPayloadSizeInBytes: rawPayloadSizeInBytes,
              };
              const openChannels = Object.entries(dataChannels)
                .filter(
                  ([peerId, channel]) =>
                    channel &&
                    channel.readyState === 'open' &&
                    !quarantinedPeers.has(peerId),
                )
                .map(([, channel]) => channel);
              if (openChannels.length === 0) {
                return OUTBOUND_DELIVERY.WAITING;
              }

              sendingFragmentId = metadata.id;
              for (let i = 0; i < fragments.length; i++) {
                if (!runtimeCanAcceptEvents()) return OUTBOUND_DELIVERY.WAITING;
                if (sendingFragmentId !== metadata.id) {
                  return OUTBOUND_DELIVERY.WAITING;
                }
                const messageJson = JSON.stringify({
                  payload: fragments[i],
                  type: type_,
                  metadata,
                });
                metadata.index += 1;
                try {
                  await sendP2PFragment(openChannels, messageJson);
                } catch (error) {
                  p2pMsg = `⚠️ P2P send will retry: ${String(error)}`;
                  await p2pStatusMessageChanged();
                  return OUTBOUND_DELIVERY.WAITING;
                }
                if (metadata.isFragmented) {
                  sendingFragmentStats = `${metadata.index}/${metadata.totalFragments}`;
                  await p2pStatusMessageChanged();
                }
              }
              await resetSendingFragmentId();
              return OUTBOUND_DELIVERY.SENT;
            } catch (error) {
              p2pMsg =
                '❌ P2P Outbound Error: ' + JSON.stringify(error, null, 2);
              await p2pStatusMessageChanged();
              throw error;
            }
          };

""",
        "explicit P2P delivery result",
    )

    text = replace_block(
        text,
        "              // hash clipboard content\n              const hcb = await hashCB(cb);",
        "            } catch (e) {",
        """              const hcb = await hashCB(cb);
              if (await validateClipboardSize(cb, type_, 'Inbound')) {
                if (!runtimeCanAcceptEvents()) return;
                await applyInboundClipboard(cb, type_, hcb);
              }
""",
        "typed P2P inbound feedback",
    )

    text = replace_block(
        text,
        "        sendClipBoardTransport = async",
        "\n\n        await updateOutboundQueueStatus('service-started');",
        """        sendClipBoardTransport = async (
          clipContent,
          type_ = 'text',
          deliveryId = null,
        ) => {
          if (!runtimeCanAcceptEvents()) return OUTBOUND_DELIVERY.WAITING;
          if (server_mode === 'P2S') {
            return sendClipBoardP2S(clipContent, type_, deliveryId);
          }
          if (server_mode === 'P2P') {
            if (!p2pTransportReady()) return OUTBOUND_DELIVERY.WAITING;
            return sendClipBoardP2P(clipContent, type_, deliveryId);
          }
          throw new Error(`Unsupported server mode: ${server_mode}`);
        };""",
        "explicit transport dispatcher",
    )

    # Obsolete global suppression state must not survive in callbacks or errors.
    lines = []
    for line in text.splitlines(keepends=True):
        if "block_image_once = false;" in line:
            continue
        lines.append(line)
    text = "".join(lines)

    for forbidden in (
        "previous_clipboard_content_hash",
        "block_image_once",
        "newCB(",
        "extendedDeliveryId",
        "awaiting-p2s-ack",
        "p2s-echo-acknowledged",
        "p2s-ack-timeout-dropped",
        "result !== false",
    ):
        if forbidden in text:
            raise RuntimeError(f"forbidden legacy delivery marker remains: {forbidden}")

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

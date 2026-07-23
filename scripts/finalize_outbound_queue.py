#!/usr/bin/env python3
"""Integrate a bounded durable outbound queue without changing server protocol."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "import { fragmentUtf8String } from './Utf8Fragmenter';",
        """import { fragmentUtf8String } from './Utf8Fragmenter';
import { createDurableOutboundQueue } from './DurableOutboundQueue';""",
        "outbound queue import",
    )
    text = replace_once(
        text,
        """          websocket_url,
          cipher_enabled,""",
        """          websocket_url,
          username,
          cipher_enabled,""",
        "queue scope username destructuring",
    )
    text = replace_once(
        text,
        """          'websocket_url',
          'cipher_enabled',""",
        """          'websocket_url',
          'username',
          'cipher_enabled',""",
        "queue scope username storage key",
    )

    queue_runtime = r'''

        const outboundQueueScope = [
          server_mode,
          websocket_url,
          username || '',
        ].join('|');
        const outboundQueue = createDurableOutboundQueue(outboundQueueScope);
        let sendClipBoardTransport = null;
        let outboundFlushRunning = false;
        let outboundFlushRequested = false;

        const updateOutboundQueueStatus = async state => {
          const snapshot = await outboundQueue.snapshot();
          await setDataInAsyncStorage(
            'outbound_queue_status',
            JSON.stringify({...snapshot, state}),
          );
        };

        const flushOutboundQueue = async () => {
          if (outboundFlushRunning) {
            outboundFlushRequested = true;
            return;
          }
          if (sendClipBoardTransport == null) {
            return;
          }

          outboundFlushRunning = true;
          try {
            do {
              outboundFlushRequested = false;
              while (true) {
                const item = await outboundQueue.peek();
                if (item == null) {
                  await updateOutboundQueueStatus('idle');
                  break;
                }
                try {
                  const sent = await sendClipBoardTransport(
                    item.content,
                    item.type,
                  );
                  if (!sent) {
                    await updateOutboundQueueStatus('waiting-for-transport');
                    break;
                  }
                  await outboundQueue.acknowledge(item.id);
                  await updateOutboundQueueStatus('sent');
                } catch (error) {
                  const failure = await outboundQueue.recordFailure(
                    item.id,
                    error,
                  );
                  await updateOutboundQueueStatus(
                    failure.dropped ? 'dropped-permanent-error' : 'send-error',
                  );
                  if (!failure.dropped) {
                    break;
                  }
                }
              }
            } while (outboundFlushRequested);
          } finally {
            outboundFlushRunning = false;
          }
        };
'''
    text = replace_once(
        text,
        """        if (max_clipboard_size_local_limit_bytes === 0) {
          max_clipboard_size_local_limit_bytes = maxsize;
        }

        // encrption""",
        """        if (max_clipboard_size_local_limit_bytes === 0) {
          max_clipboard_size_local_limit_bytes = maxsize;
        }"""
        + queue_runtime
        + """
        // encrption""",
        "outbound queue runtime",
    )

    text = replace_once(
        text,
        """              await clearFiles();
              if (stompClient && stompClient.connected && !toggle) {""",
        """              await clearFiles();
              if (!stompClient || !stompClient.connected || toggle) {
                return false;
              }
              {""",
        "P2S transport readiness return",
    )

    text = replace_once(
        text,
        """                } catch (e) {
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '❌ Inbound Error: ' + e,
                  );
                }
              });

              if (enable_websocket_status_notification === 'true') {""",
        """                } catch (e) {
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '❌ Inbound Error: ' + e,
                  );
                } finally {
                  await flushOutboundQueue();
                }
              });

              await flushOutboundQueue();
              if (enable_websocket_status_notification === 'true') {""",
        "P2S queue flush after connect and echo",
    )

    text = replace_once(
        text,
        """            } catch (e) {
              block_image_once = false;
              p2pMsg = '❌ P2P Outbound Error: ' + JSON.stringify(e, null, 2);
              await p2pStatusMessageChanged();
            }
          };""",
        """            } catch (e) {
              block_image_once = false;
              p2pMsg = '❌ P2P Outbound Error: ' + JSON.stringify(e, null, 2);
              await p2pStatusMessageChanged();
              throw e;
            }
          };""",
        "P2P send failure propagation",
    )

    text = replace_once(
        text,
        """              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ P2P peer connected',
              );
            };""",
        """              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ P2P peer connected',
              );
              await flushOutboundQueue();
            };""",
        "P2P queue flush on channel open",
    )
    text = replace_once(
        text,
        """              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ P2P peer connected',
              );
            }
          };""",
        """              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ P2P peer connected',
              );
              await flushOutboundQueue();
            }
          };""",
        "P2P queue flush for already-open channel",
    )

    old_dispatch = '''        // send clipboard content
        const sendClipBoard = async (clipContent, type_ = 'text') => {
          if (server_mode === 'P2S') {
            await sendClipBoardP2S(clipContent, type_);
          } else if (server_mode === 'P2P') {
            await sendClipBoardP2P(clipContent, type_);
          }
        };
'''
    new_dispatch = '''        // Queue first; transport delivery is retried after reconnect/process restart.
        sendClipBoardTransport = async (clipContent, type_ = 'text') => {
          if (server_mode === 'P2S') {
            if (!stompClient || !stompClient.connected || toggle) return false;
            const result = await sendClipBoardP2S(clipContent, type_);
            return result !== false;
          }
          if (server_mode === 'P2P') {
            if (liveConnectionsCount <= 0) return false;
            const result = await sendClipBoardP2P(clipContent, type_);
            return result !== false;
          }
          throw new Error(`Unsupported server mode: ${server_mode}`);
        };

        const sendClipBoard = async (clipContent, type_ = 'text') => {
          await outboundQueue.enqueue(String(clipContent), type_);
          await updateOutboundQueueStatus('queued');
          await flushOutboundQueue();
        };

        await updateOutboundQueueStatus('service-started');
'''
    text = replace_once(text, old_dispatch, new_dispatch, "durable transport dispatch")

    text = replace_once(
        text,
        """            await setDataInAsyncStorage('wsStatusMessage', '✅ Disconnected');
            cleanupClipboardListeners();""",
        """            await outboundQueue.clear();
            await updateOutboundQueueStatus('cleared-on-manual-stop');
            await setDataInAsyncStorage('wsStatusMessage', '✅ Disconnected');
            cleanupClipboardListeners();""",
        "clear P2S queue on manual stop",
    )
    text = replace_once(
        text,
        """            await setDataInAsyncStorage('wsStatusMessage', '✅ Disconnected');
            await setDataInAsyncStorage('p2pStatusMessage', '');
            cleanupClipboardListeners();""",
        """            await outboundQueue.clear();
            await updateOutboundQueueStatus('cleared-on-manual-stop');
            await setDataInAsyncStorage('wsStatusMessage', '✅ Disconnected');
            await setDataInAsyncStorage('p2pStatusMessage', '');
            cleanupClipboardListeners();""",
        "clear P2P queue on manual stop",
    )

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

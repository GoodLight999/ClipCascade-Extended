"""Wrap Promise-returning host callbacks in the canonical detached supervisor."""
from __future__ import annotations

from pathlib import Path


def indent_body(body: str, spaces: int = 2) -> str:
    prefix = " " * spaces
    return "".join(
        prefix + line if line.strip() else line
        for line in body.splitlines(keepends=True)
    )


def wrap_between(
    text: str,
    *,
    start_marker: str,
    next_marker: str,
    close_token: str,
    replacement_start: str,
    replacement_close: str,
    label: str,
) -> str:
    if text.count(start_marker) != 1:
        raise RuntimeError(
            f"{label}: expected one callback start, found {text.count(start_marker)}"
        )
    start = text.index(start_marker)
    next_index = text.find(next_marker, start + len(start_marker))
    if next_index < 0:
        raise RuntimeError(f"{label}: next callback marker not found")
    segment = text[start + len(start_marker) : next_index]
    close = segment.rfind(close_token)
    if close < 0:
        raise RuntimeError(f"{label}: callback close token not found")
    tail = segment[close + len(close_token) :]
    if tail.strip():
        raise RuntimeError(f"{label}: unexpected content after callback close")
    body = indent_body(segment[:close])
    return (
        text[:start]
        + replacement_start
        + body
        + replacement_close
        + text[next_index:]
    )


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def apply(root: Path) -> None:
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    shared_callbacks = (
        (
            "SHARED_TEXT",
            "shared-text",
            "        // Event listener triggered when image is shared with the app.",
        ),
        (
            "SHARED_IMAGE",
            "shared-image",
            "        // Event listener triggered when files are shared with the app.",
        ),
        (
            "SHARED_FILES",
            "shared-files",
            "        //clipboard monitor",
        ),
    )
    for event_name, scope, next_marker in shared_callbacks:
        start = (
            "        trackClipboardSubscription(DeviceEventEmitter.addListener("
            f"'{event_name}', async event => {{"
        )
        replacement = (
            "        trackClipboardSubscription(DeviceEventEmitter.addListener("
            f"'{event_name}', event => {{\n"
            f"          runDetached('{scope}', async () => {{"
        )
        text = wrap_between(
            text,
            start_marker=start,
            next_marker=next_marker,
            close_token="\n        }));\n\n",
            replacement_start=replacement,
            replacement_close="\n          });\n        }));\n\n",
            label=f"{event_name} callback supervision",
        )

    text = wrap_between(
        text,
        start_marker="          async params => {",
        next_marker="        ));\n        await ClipboardListener.startListening();",
        close_token="\n          },\n",
        replacement_start=(
            "          params => {\n"
            "            runDetached('native-clipboard-change', async () => {"
        ),
        replacement_close="\n            });\n          },\n",
        label="native clipboard callback supervision",
    )

    stomp_callbacks = (
        (
            "            onConnect: async () => {",
            "            onDisconnect: async () => {",
            "            onConnect: () => {\n"
            "              runDetached('p2s-connect', async () => {",
            "P2S connect callback",
        ),
        (
            "            onDisconnect: async () => {",
            "            onStompError: async frame => {",
            "            onDisconnect: () => {\n"
            "              runDetached('p2s-disconnect', async () => {",
            "P2S disconnect callback",
        ),
        (
            "            onStompError: async frame => {",
            "            onWebSocketError: async event => {",
            "            onStompError: frame => {\n"
            "              runDetached('p2s-stomp-error', async () => {",
            "P2S STOMP error callback",
        ),
        (
            "            onWebSocketError: async event => {",
            "            onWebSocketClose: async event => {",
            "            onWebSocketError: event => {\n"
            "              runDetached('p2s-websocket-error', async () => {",
            "P2S WebSocket error callback",
        ),
        (
            "            onWebSocketClose: async event => {",
            "          });\n\n          // start websocket stomp connection",
            "            onWebSocketClose: event => {\n"
            "              runDetached('p2s-websocket-close', async () => {",
            "P2S WebSocket close callback",
        ),
    )
    for start, next_marker, replacement, label in stomp_callbacks:
        text = wrap_between(
            text,
            start_marker=start,
            next_marker=next_marker,
            close_token="\n            },\n",
            replacement_start=replacement,
            replacement_close="\n              });\n            },\n",
            label=label,
        )

    text = wrap_between(
        text,
        start_marker=(
            "              stompClient.subscribe("
            "SUBSCRIPTION_DESTINATION, async message => {"
        ),
        next_marker="\n\n              await flushOutboundQueue();",
        close_token="\n              });",
        replacement_start=(
            "              stompClient.subscribe("
            "SUBSCRIPTION_DESTINATION, message => {\n"
            "                runDetached('p2s-subscription-message', async () => {"
        ),
        replacement_close="\n                });\n              });",
        label="P2S subscription callback",
    )

    text = replace_once(
        text,
        """                      p2sAckTracker.begin(p2sDeliveryId, timedOutId => {
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
                      });""",
        """                      p2sAckTracker.begin(p2sDeliveryId, timedOutId => {
                        toggle = false;
                        runDetached('p2s-ack-timeout', async () => {
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
                        });
                      });""",
        "P2S ACK timeout supervision",
    )

    path.write_text(text, encoding="utf-8")

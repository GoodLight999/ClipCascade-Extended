#!/usr/bin/env python3
"""Replace single-stream P2P fragment state with a bounded accumulator."""
from __future__ import annotations

import argparse
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
import { createP2PFragmentAccumulator } from './P2PFragmentAccumulator';""",
        "P2P accumulator import",
    )
    text = replace_once(
        text,
        """          // Fragment variables
          let sendingFragmentId = '';
          let receivingFragments = {}; // Map: fragmentId -> array of strings (ordered)
          let sendingFragmentStats = null;
          let receivingFragmentStats = null;""",
        """          // Fragment state is independent per peer/message and bounded.
          let sendingFragmentId = '';
          const fragmentAccumulator = createP2PFragmentAccumulator({
            maxActive: 8,
            maxFragments: 8192,
            maxAgeMs: 2 * 60 * 1000,
            maxPayloadBytes:
              max_clipboard_size_local_limit_bytes >= 0
                ? Math.min(max_clipboard_size_local_limit_bytes, 128 * 1024 * 1024)
                : 128 * 1024 * 1024,
          });
          let sendingFragmentStats = null;
          let receivingFragmentStats = null;""",
        "P2P fragment variables",
    )
    text = replace_once(
        text,
        """          const resetReceivingFragments = async () => {
            receivingFragments = {};
            receivingFragmentStats = null;
            await resetP2PMsg();
          };""",
        """          const resetReceivingFragments = async peerId => {
            if (peerId == null) {
              fragmentAccumulator.clear();
            } else {
              fragmentAccumulator.clearPeer(peerId);
            }
            receivingFragmentStats = null;
            await resetP2PMsg();
          };""",
        "P2P fragment reset",
    )
    text = replace_once(
        text,
        """                    await resetSendingFragmentId();
                    await resetReceivingFragments();

                    const rawPayloadSizeInBytes =""",
        """                    await resetSendingFragmentId();

                    const rawPayloadSizeInBytes =""",
        "outbound send must not destroy inbound fragments",
    )
    text = replace_once(
        text,
        """          const onDataChannelMessage = async messageJson => {
            try {""",
        """          const onDataChannelMessage = async (messageJson, remotePeerId) => {
            try {""",
        "peer-scoped P2P message handler",
    )
    text = replace_once(
        text,
        """              await clearFiles(true);
              await resetSendingFragmentId();

              let cb = String(message.payload);""",
        """              await clearFiles(true);

              let cb = String(message.payload);""",
        "inbound message must not cancel outbound fragments",
    )
    text = replace_once(
        text,
        """                await resetReceivingFragments();
                p2pMsg = `⚠️ Payload size limit exceeded: ${metadata.combinedRawPayloadSizeInBytes} bytes exceeds ${max_clipboard_size_local_limit_bytes} bytes`;""",
        """                if (
                  metadata.isFragmented === true &&
                  typeof metadata.id === 'string'
                ) {
                  fragmentAccumulator.drop(remotePeerId, metadata.id);
                }
                receivingFragmentStats = null;
                p2pMsg = `⚠️ Payload size limit exceeded: ${metadata.combinedRawPayloadSizeInBytes} bytes exceeds ${max_clipboard_size_local_limit_bytes} bytes`;""",
        "drop only oversized P2P message",
    )

    old_fragment_block = """              // Fragmented message handling
              if (metadata != null && metadata.isFragmented) {
                receivingFragmentStats = `${metadata.index + 1}/${
                  metadata.totalFragments
                }`;
                await p2pStatusMessageChanged();

                if (metadata.id in receivingFragments) {
                  receivingFragments[metadata.id][metadata.index] = cb;

                  // If this is the last fragment, try to combine
                  if (metadata.index === metadata.totalFragments - 1) {
                    // Check if all fragments are present (none is empty)
                    if (
                      receivingFragments[metadata.id].every(frag => frag !== '')
                    ) {
                      // Join them all together into one payload
                      cb = receivingFragments[metadata.id].join('');
                    } else {
                      // Missing fragment(s): error out
                      await resetReceivingFragments();
                      p2pMsg =
                        'Failed to receive: One or more fragments are missing or the clipboard changed before completion.';
                      await p2pStatusMessageChanged();
                      return;
                    }
                  } else {
                    // Not the last fragment, so we don't proceed further
                    return;
                  }
                } else {
                  await resetReceivingFragments();
                  receivingFragments[metadata.id] = Array(
                    metadata.totalFragments,
                  ).fill('');
                  receivingFragments[metadata.id][metadata.index] = cb;
                  return;
                }
              }"""
    new_fragment_block = """              // Fragmented messages may arrive out of order and overlap with
              // other peers/messages. The accumulator isolates each stream.
              if (metadata != null && metadata.isFragmented) {
                const result = fragmentAccumulator.add(
                  remotePeerId,
                  metadata,
                  cb,
                );
                if (result.status === 'duplicate-complete') {
                  return;
                }
                receivingFragmentStats = `${remotePeerId}: ${result.progress}`;
                await p2pStatusMessageChanged();
                if (result.status !== 'complete') {
                  return;
                }
                cb = result.payload;
                receivingFragmentStats = null;
              }"""
    text = replace_once(
        text,
        old_fragment_block,
        new_fragment_block,
        "P2P fragment assembly",
    )
    text = replace_once(
        text,
        """                previous_clipboard_content_hash = hcb;

                await resetReceivingFragments();
                // validate clipboard size""",
        """                previous_clipboard_content_hash = hcb;

                // validate clipboard size""",
        "completed P2P stream is already removed",
    )
    text = replace_once(
        text,
        """            channel.onmessage = async e => {
              await onDataChannelMessage(e.data);
            };""",
        """            channel.onmessage = async e => {
              await onDataChannelMessage(e.data, remotePeerId);
            };""",
        "pass peer identity to fragment accumulator",
    )
    text = replace_once(
        text,
        """              delete dataChannels[oldPid];
              }

              if (peerConnections[oldPid]) {""",
        """              delete dataChannels[oldPid];
              }
              fragmentAccumulator.clearPeer(oldPid);

              if (peerConnections[oldPid]) {""",
        "clear stale peer fragments",
    )
    text = replace_once(
        text,
        """              delete dataChannels[peerId];
            }
            const pc = peerConnections[peerId];""",
        """              delete dataChannels[peerId];
            }
            fragmentAccumulator.clearPeer(peerId);
            const pc = peerConnections[peerId];""",
        "clear disposed peer fragments",
    )

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

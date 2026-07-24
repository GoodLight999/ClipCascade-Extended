"""Block stale callbacks from mutating clipboard or transport after stop begins."""
from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def replace_exact(
    text: str,
    old: str,
    new: str,
    expected: int,
    label: str,
) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} markers, found {count}")
    return text.replace(old, new)


def apply(root: Path) -> None:
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        """            const stopAcceptingRuntimeEvents = () => {
              runtimeAcceptingEvents = false;
            };
            const finishForegroundRuntime = async state => {""",
        """            const stopAcceptingRuntimeEvents = () => {
              runtimeAcceptingEvents = false;
            };
            const runRuntimeDetached = (scope, task) =>
              runDetached(scope, async () => {
                if (!runtimeCanAcceptEvents()) return;
                await task();
              });
            const finishForegroundRuntime = async state => {""",
        "runtime-scoped detached callback helper",
    )

    literal_scopes = (
        "shared-text",
        "shared-image",
        "shared-files",
        "native-clipboard-change",
        "outbound-retry",
        "p2s-connect",
        "p2s-disconnect",
        "p2s-stomp-error",
        "p2s-websocket-error",
        "p2s-websocket-close",
        "p2s-subscription-message",
        "p2s-ack-timeout",
        "signaling-reconnect",
        "signaling-open",
        "signaling-message",
        "signaling-error",
        "signaling-close",
    )
    for scope in literal_scopes:
        text = replace_once(
            text,
            f"runDetached('{scope}'",
            f"runRuntimeDetached('{scope}'",
            f"runtime guard for {scope}",
        )

    template_scopes = (
        "ice-candidate",
        "datachannel-received",
        "peer-recovery",
        "datachannel-open",
        "datachannel-message",
        "datachannel-close",
        "datachannel-error",
    )
    for scope in template_scopes:
        text = replace_once(
            text,
            f"runDetached(`{scope}:${{remotePeerId}}`",
            f"runRuntimeDetached(`{scope}:${{remotePeerId}}`",
            f"runtime guard for {scope}",
        )

    text = replace_once(
        text,
        """        const flushOutboundQueue = async () => {
          if (outboundFlushRunning) {""",
        """        const flushOutboundQueue = async () => {
          if (!runtimeCanAcceptEvents()) {
            cancelOutboundRetry();
            return;
          }
          if (outboundFlushRunning) {""",
        "guard outbound flush entry",
    )
    text = replace_once(
        text,
        """              while (true) {
                const item = await outboundQueue.peek();""",
        """              while (runtimeCanAcceptEvents()) {
                const item = await outboundQueue.peek();""",
        "guard outbound flush loop",
    )
    text = replace_once(
        text,
        """                try {
                  const sent = await sendClipBoardTransport(""",
        """                try {
                  if (!runtimeCanAcceptEvents()) break;
                  const sent = await sendClipBoardTransport(""",
        "guard outbound transport dispatch",
    )

    text = replace_once(
        text,
        """        sendClipBoardTransport = async (
          clipContent,
          type_ = 'text',
          deliveryId = null,
        ) => {
          if (server_mode === 'P2S') {""",
        """        sendClipBoardTransport = async (
          clipContent,
          type_ = 'text',
          deliveryId = null,
        ) => {
          if (!runtimeCanAcceptEvents()) return false;
          if (server_mode === 'P2S') {""",
        "guard transport dispatcher",
    )

    text = replace_once(
        text,
        """                      // send
                      stompClient.publish({""",
        """                      // Do not publish after this runtime begins stopping.
                      if (!runtimeCanAcceptEvents()) return false;
                      // send
                      stompClient.publish({""",
        "guard P2S publish",
    )
    text = replace_once(
        text,
        """          sendClipBoardP2P = async (
            clipContent,
            type_ = 'text',
            deliveryId = null,
          ) => {
            try {
              await clearFiles();""",
        """          sendClipBoardP2P = async (
            clipContent,
            type_ = 'text',
            deliveryId = null,
          ) => {
            try {
              if (!runtimeCanAcceptEvents()) return false;
              await clearFiles();""",
        "guard P2P send entry",
    )
    text = replace_once(
        text,
        """                    for (let i = 0; i < fragments.length; i++) {
                      if (sendingFragmentId !== metadata.id) {""",
        """                    for (let i = 0; i < fragments.length; i++) {
                      if (!runtimeCanAcceptEvents()) return false;
                      if (sendingFragmentId !== metadata.id) {""",
        "guard every P2P fragment send",
    )

    text = replace_once(
        text,
        """          const signalingSend = async obj => {
            try {""",
        """          const signalingSend = async obj => {
            if (!runtimeCanAcceptEvents()) return false;
            try {""",
        "guard signaling send",
    )
    text = replace_once(
        text,
        """              }
            } catch (e) {
              await setDataInAsyncStorage(
                'wsStatusMessage',
                '❌ Outbound Error: ' + e,
              );
            }
          };

          // receive clipboard content P2P""",
        """                return true;
              }
              return false;
            } catch (e) {
              await setDataInAsyncStorage(
                'wsStatusMessage',
                '❌ Outbound Error: ' + e,
              );
              return false;
            }
          };

          // receive clipboard content P2P""",
        "truthful signaling send result",
    )

    text = replace_once(
        text,
        """          const onDataChannelMessage = async (messageJson, remotePeerId) => {
            try {""",
        """          const onDataChannelMessage = async (messageJson, remotePeerId) => {
            if (!runtimeCanAcceptEvents()) return;
            try {""",
        "guard P2P inbound entry",
    )
    text = replace_exact(
        text,
        """                          if (await validateClipboardSize(cb, type_, 'Inbound')) {
                            // set clipboard content""",
        """                          if (await validateClipboardSize(cb, type_, 'Inbound')) {
                            if (!runtimeCanAcceptEvents()) return;
                            // set clipboard content""",
        1,
        "guard P2S inbound apply",
    )
    text = replace_exact(
        text,
        """                if (await validateClipboardSize(cb, type_, 'Inbound')) {
                  // set clipboard content""",
        """                if (await validateClipboardSize(cb, type_, 'Inbound')) {
                  if (!runtimeCanAcceptEvents()) return;
                  // set clipboard content""",
        1,
        "guard P2P inbound apply",
    )

    text = replace_once(
        text,
        """          const handlePeerList = async peerList => {
            if (!myPeerId) {""",
        """          const handlePeerList = async peerList => {
            if (!runtimeCanAcceptEvents()) return;
            if (!Array.isArray(peerList)) {
              throw new Error('Invalid P2P peer list');
            }
            if (!myPeerId) {""",
        "guard and validate peer list",
    )
    text = replace_once(
        text,
        """            await removeStalePeers(updatedPeers);
            await syncP2PCompatibilityStatus();

            for (const pid of peers) {""",
        """            await removeStalePeers(updatedPeers);
            if (!runtimeCanAcceptEvents()) return;
            await syncP2PCompatibilityStatus();

            for (const pid of peers) {
              if (!runtimeCanAcceptEvents()) break;""",
        "guard peer reconciliation after cleanup",
    )

    text = replace_exact(
        text,
        """            if (p2pShuttingDown || !myPeerId || !peers.has(remotePeerId)) {""",
        """            if (
              !runtimeCanAcceptEvents() ||
              p2pShuttingDown ||
              !myPeerId ||
              !peers.has(remotePeerId)
            ) {""",
        3,
        "guard peer transport recovery",
    )

    text = replace_once(
        text,
        """          const handleOffer = async (fromPeerId, offer) => {
            if (p2pShuttingDown) {""",
        """          const handleOffer = async (fromPeerId, offer) => {
            if (!runtimeCanAcceptEvents() || p2pShuttingDown) {""",
        "guard OFFER entry",
    )
    text = replace_once(
        text,
        """            await runSerializedPeerOp(fromPeerId, async () => {
              if (p2pShuttingDown) {""",
        """            await runSerializedPeerOp(fromPeerId, async () => {
              if (!runtimeCanAcceptEvents() || p2pShuttingDown) {""",
        "guard serialized OFFER operation",
    )
    text = replace_once(
        text,
        """              if (peerConnections[fromPeerId]) {
                await disposePeerConnection(fromPeerId);
              }
              const pc = await createPeerConnection(fromPeerId);""",
        """              if (peerConnections[fromPeerId]) {
                await disposePeerConnection(fromPeerId);
              }
              if (!runtimeCanAcceptEvents()) return;
              const pc = await createPeerConnection(fromPeerId);""",
        "guard OFFER connection recreation",
    )

    text = replace_once(
        text,
        """          const handleAnswer = async (fromPeerId, answer) => {
            const pc = peerConnections[fromPeerId];""",
        """          const handleAnswer = async (fromPeerId, answer) => {
            if (!runtimeCanAcceptEvents()) return;
            const pc = peerConnections[fromPeerId];""",
        "guard ANSWER handling",
    )
    text = replace_once(
        text,
        """          const handleIceCandidate = async (fromPeerId, candidateData) => {
            const pc = peerConnections[fromPeerId];""",
        """          const handleIceCandidate = async (fromPeerId, candidateData) => {
            if (!runtimeCanAcceptEvents()) return;
            const pc = peerConnections[fromPeerId];""",
        "guard ICE handling",
    )
    text = replace_once(
        text,
        """          const setupDataChannel = async (remotePeerId, channel) => {
            channel.onopen = () => {""",
        """          const setupDataChannel = async (remotePeerId, channel) => {
            if (!runtimeCanAcceptEvents()) {
              try {
                channel.close();
              } catch (_) {
                // The stale channel may already be closed.
              }
              return;
            }
            channel.onopen = () => {""",
        "guard DataChannel setup",
    )
    text = replace_once(
        text,
        """            if (channel.readyState === 'open') {
              startDataChannelHeartbeat(remotePeerId, channel);""",
        """            if (channel.readyState === 'open') {
              if (!runtimeCanAcceptEvents()) {
                try {
                  channel.close();
                } catch (_) {
                  // The stale channel may already be closed.
                }
                return;
              }
              startDataChannelHeartbeat(remotePeerId, channel);""",
        "guard already-open DataChannel",
    )

    text = replace_once(
        text,
        """                  await cleanupPeerConnections();

                  await setDataInAsyncStorage(""",
        """                  await cleanupPeerConnections();
                  if (!runtimeCanAcceptEvents()) return;

                  await setDataInAsyncStorage(""",
        "guard signaling open after cleanup",
    )
    text = replace_once(
        text,
        """                toggle = false;
                // Subscribe to a topic""",
        """                toggle = false;
                if (!runtimeCanAcceptEvents()) return;
                // Subscribe to a topic""",
        "guard P2S subscription creation",
    )

    path.write_text(text, encoding="utf-8")

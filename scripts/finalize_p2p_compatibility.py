#!/usr/bin/env python3
"""Generate the final legacy-safe P2P compatibility implementation.

Compatibility travels only as optional OFFER/ANSWER metadata that the upstream
server already forwards. Clipboard DataChannels never carry private control
frames. The hello contains protocol and encryption mode only; a wrong key is
learned from authenticated decryption and quarantined per peer. Signaling
reconnects are supervised by one cancellable timer.
"""
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
        "import { sendP2PFragment } from './P2PChannelSender';",
        """import { sendP2PFragment } from './P2PChannelSender';
import {
  evaluateP2PCompatibility,
  isEncryptedEnvelope,
} from './P2PCompatibility';""",
        "P2P compatibility helper imports",
    )

    replace_once(
        service,
        """          const peerOpChains = {};
          const dataChannelHeartbeatTimers = {};
          const P2P_DC_KEEPALIVE_JSON = JSON.stringify({ _cc_keepalive: true });""",
        """          const peerOpChains = {};
          const dataChannelHeartbeatTimers = {};
          const compatibilityByPeer = new Map();
          const quarantinedPeers = new Set();
          const P2P_COMPATIBILITY_PROTOCOL = 1;
          const localCompatibility = {
            protocol: P2P_COMPATIBILITY_PROTOCOL,
            cipherEnabled: cipher_enabled === 'true',
          };

          const syncP2PCompatibilityStatus = async () => {
            const candidateCount = Math.max(
              0,
              peers.size - (myPeerId != null && peers.has(myPeerId) ? 1 : 0),
            );
            const states = Array.from(compatibilityByPeer.values());
            const compatibleCount = states.filter(value => value === 'compatible').length;
            const incompatibleCount = states.filter(value => value === 'incompatible').length;
            await setDataInAsyncStorage('p2p_candidate_peers', String(candidateCount));
            await setDataInAsyncStorage('p2p_compatible_peers', String(compatibleCount));
            await setDataInAsyncStorage('p2p_incompatible_peers', String(incompatibleCount));
          };

          const markPeerCompatibility = async (peerId, state, reason = '') => {
            if (!peerId) return;
            const previous = compatibilityByPeer.get(peerId);
            if (previous === state && state === 'incompatible') return;
            compatibilityByPeer.set(peerId, state);
            if (state === 'incompatible') {
              quarantinedPeers.add(peerId);
              await setDataInAsyncStorage(
                'p2p_last_compatibility_error',
                `${peerId}:${reason}`.slice(0, 500),
              );
              const incompatibleCount = Array.from(compatibilityByPeer.values()).filter(
                value => value === 'incompatible',
              ).length;
              p2pMsg = `⚠️ Ignored ${incompatibleCount} incompatible P2P peer(s)`;
              await p2pStatusMessageChanged();
              setTimeout(() => disposePeerConnection(peerId), 0);
            }
            await syncP2PCompatibilityStatus();
          };""",
        "final P2P compatibility runtime",
    )

    replace_once(
        service,
        """          const syncLiveConnectionsCount = async () => {
            liveConnectionsCount = Object.values(dataChannels).filter(
              c => c && c.readyState === 'open',
            ).length;
            isP2PStatusMsgChanged = true;
            await p2pStatusMessageChanged();
          };""",
        """          const syncLiveConnectionsCount = async () => {
            liveConnectionsCount = Object.entries(dataChannels).filter(
              ([peerId, channel]) =>
                channel &&
                channel.readyState === 'open' &&
                !quarantinedPeers.has(peerId),
            ).length;
            isP2PStatusMsgChanged = true;
            await syncP2PCompatibilityStatus();
            await p2pStatusMessageChanged();
          };""",
        "P2P live compatible connection count",
    )

    replace_once(
        service,
        """          const runSerializedPeerOp = (peerId, op) => {
            const prev = peerOpChains[peerId] || Promise.resolve();
            const next = prev.then(() => op()).catch(() => {});
            peerOpChains[peerId] = next;
            return next;
          };""",
        """          const clearPeerErrorIfOwned = async (key, peerId) => {
            const current = String((await getDataFromAsyncStorage(key)) || '');
            if (current.startsWith(`${peerId}:`)) {
              await setDataInAsyncStorage(key, '');
            }
          };

          const runSerializedPeerOp = (peerId, op) => {
            const previous = peerOpChains[peerId] || Promise.resolve();
            const current = previous.catch(() => undefined).then(async () => {
              const result = await op();
              await clearPeerErrorIfOwned(
                'p2p_last_peer_operation_error',
                peerId,
              );
              return result;
            });
            peerOpChains[peerId] = current.catch(async error => {
              await setDataInAsyncStorage(
                'p2p_last_peer_operation_error',
                `${peerId}:${String(error?.stack || error)}`.slice(0, 1000),
              );
            });
            return current;
          };""",
        "observable serialized peer operation",
    )

    replace_once(
        service,
        """          const startDataChannelHeartbeat = (remotePeerId, channel) => {
            if (dataChannelHeartbeatTimers[remotePeerId]) {
              clearInterval(dataChannelHeartbeatTimers[remotePeerId]);
            }
            dataChannelHeartbeatTimers[remotePeerId] = setInterval(() => {
              try {
                if (channel.readyState === 'open') {
                  channel.send(P2P_DC_KEEPALIVE_JSON);
                }
              } catch (e) {
                // no-op
              }
            }, HEARTBEAT_INTERVAL);
          };""",
        """          const startDataChannelHeartbeat = (remotePeerId, channel) => {
            if (dataChannelHeartbeatTimers[remotePeerId]) {
              clearInterval(dataChannelHeartbeatTimers[remotePeerId]);
            }
            // Never send private control frames over the clipboard DataChannel:
            // upstream clients would parse them as clipboard payloads. Liveness is
            // observed through readyState/onclose and the signaling-server heartbeat.
            dataChannelHeartbeatTimers[remotePeerId] = setInterval(() => {
              if (channel.readyState !== 'open') {
                clearInterval(dataChannelHeartbeatTimers[remotePeerId]);
                delete dataChannelHeartbeatTimers[remotePeerId];
              }
            }, HEARTBEAT_INTERVAL);
          };""",
        "legacy-safe data channel liveness",
    )

    # Accept private compatibility frames from older Extended builds so a staged
    # upgrade cannot leak them into clipboard parsing, but never send such frames.
    replace_once(
        service,
        """              if (message && message._cc_keepalive === true) {
                return;
              }

              await clearFiles(true);""",
        """              if (message && message._cc_compat === true) {
                const compatibility = evaluateP2PCompatibility(
                  localCompatibility,
                  message,
                );
                await markPeerCompatibility(
                  remotePeerId,
                  compatibility.state,
                  compatibility.reason,
                );
                return;
              }
              if (message && message._cc_keepalive === true) {
                if (message.compatibility) {
                  const compatibility = evaluateP2PCompatibility(
                    localCompatibility,
                    message.compatibility,
                  );
                  await markPeerCompatibility(
                    remotePeerId,
                    compatibility.state,
                    compatibility.reason,
                  );
                }
                return;
              }
              if (quarantinedPeers.has(remotePeerId)) return;

              await clearFiles(true);""",
        "P2P compatibility control-frame receive compatibility",
    )

    replace_once(
        service,
        """              // decrypt
              if (cipher_enabled === 'true') {
                try {
                  cb = await decrypt(JSON.parse(cb));
                } catch (error) {
                  throw new Error(
                    `Encryption must be enabled on all devices if enabled. JSON parsing failed: ${error.message}`,
                  );
                }
              }

              // hash clipboard content""",
        """              // Decrypt only for this peer. A wrong key or mode must not flood
              // the room with repeated AEAD errors or stop compatible peers.
              if (cipher_enabled === 'true') {
                try {
                  cb = await decrypt(JSON.parse(cb));
                  await markPeerCompatibility(remotePeerId, 'compatible');
                } catch (error) {
                  await markPeerCompatibility(
                    remotePeerId,
                    'incompatible',
                    `encryption-key:${String(error?.message || error)}`,
                  );
                  return;
                }
              } else {
                if (isEncryptedEnvelope(cb)) {
                  await markPeerCompatibility(
                    remotePeerId,
                    'incompatible',
                    'remote-encryption-enabled',
                  );
                  return;
                }
                await markPeerCompatibility(remotePeerId, 'compatible');
              }

              // hash clipboard content""",
        "P2P peer-scoped decrypt quarantine",
    )

    replace_once(
        service,
        """            peers.forEach(async pid => {
              if (pid === myPeerId) return; // skip self
              if (!peerConnections[pid]) {
                // Create new PeerConnection
                const pc = await createPeerConnection(pid);
                peerConnections[pid] = pc;

                // Tie-breaker: only the "lower" ID makes the offer to avoid collisions
                if (myPeerId < pid) {
                  const channel = await pc.createDataChannel('cliptext');
                  dataChannels[pid] = channel;
                  await setupDataChannel(pid, channel);
                  await createOffer(pid);
                }
              }
            });""",
        """            for (const pid of peers) {
              if (pid === myPeerId) continue; // skip self
              if (quarantinedPeers.has(pid)) continue;
              if (peerConnections[pid]) {
                await clearPeerErrorIfOwned('p2p_last_peer_setup_error', pid);
                continue;
              }
              try {
                const pc = await createPeerConnection(pid);
                peerConnections[pid] = pc;

                // Tie-breaker: only the "lower" ID makes the offer to avoid collisions.
                if (myPeerId < pid) {
                  const channel = await pc.createDataChannel('cliptext');
                  dataChannels[pid] = channel;
                  await setupDataChannel(pid, channel);
                  await createOffer(pid);
                }
                await clearPeerErrorIfOwned('p2p_last_peer_setup_error', pid);
              } catch (error) {
                await setDataInAsyncStorage(
                  'p2p_last_peer_setup_error',
                  `${pid}:${String(error?.stack || error)}`.slice(0, 1000),
                );
                await disposePeerConnection(pid);
              }
            }""",
        "awaited P2P peer-list reconciliation",
    )

    replace_once(
        service,
        """                    case 'OFFER':
                      await handleOffer(data.fromPeerId, data.offer);
                      break;

                    case 'ANSWER':
                      await handleAnswer(data.fromPeerId, data.answer);
                      break;""",
        """                    case 'OFFER': {
                      const compatibility = evaluateP2PCompatibility(
                        localCompatibility,
                        data.compatibility,
                      );
                      await markPeerCompatibility(
                        data.fromPeerId,
                        compatibility.state,
                        compatibility.reason,
                      );
                      if (compatibility.state !== 'incompatible') {
                        await handleOffer(data.fromPeerId, data.offer);
                      }
                      break;
                    }

                    case 'ANSWER': {
                      const compatibility = evaluateP2PCompatibility(
                        localCompatibility,
                        data.compatibility,
                      );
                      await markPeerCompatibility(
                        data.fromPeerId,
                        compatibility.state,
                        compatibility.reason,
                      );
                      if (compatibility.state !== 'incompatible') {
                        await handleAnswer(data.fromPeerId, data.answer);
                      }
                      break;
                    }""",
        "OFFER/ANSWER compatibility receiver",
    )

    replace_once(
        service,
        """            await signalingSend({
              type: 'OFFER',
              fromPeerId: myPeerId,
              toPeerId: remotePeerId,
              offer: pc.localDescription,
            });""",
        """            await signalingSend({
              type: 'OFFER',
              fromPeerId: myPeerId,
              toPeerId: remotePeerId,
              offer: pc.localDescription,
              compatibility: localCompatibility,
            });""",
        "OFFER compatibility metadata",
    )

    replace_once(
        service,
        """              await signalingSend({
                type: 'ANSWER',
                fromPeerId: myPeerId,
                toPeerId: fromPeerId,
                answer: pc.localDescription,
              });""",
        """              await signalingSend({
                type: 'ANSWER',
                fromPeerId: myPeerId,
                toPeerId: fromPeerId,
                answer: pc.localDescription,
                compatibility: localCompatibility,
              });""",
        "ANSWER compatibility metadata",
    )

    replace_once(
        service,
        """            channel.onopen = async () => {
              startDataChannelHeartbeat(remotePeerId, channel);""",
        """            channel.onopen = async () => {
              if (!compatibilityByPeer.has(remotePeerId)) {
                compatibilityByPeer.set(remotePeerId, 'unknown');
              }
              startDataChannelHeartbeat(remotePeerId, channel);""",
        "preserve negotiated compatibility on channel open",
    )

    replace_once(
        service,
        """                    const openChannels = Object.values(dataChannels).filter(
                      channel => channel && channel.readyState === 'open',
                    );""",
        """                    const openChannels = Object.entries(dataChannels)
                      .filter(
                        ([peerId, channel]) =>
                          channel &&
                          channel.readyState === 'open' &&
                          !quarantinedPeers.has(peerId),
                      )
                      .map(([, channel]) => channel);""",
        "exclude quarantined peers from outbound P2P send",
    )

    replace_once(
        service,
        """              await recoverPeerTransport(remotePeerId, null);""",
        """              if (!quarantinedPeers.has(remotePeerId)) {
                await recoverPeerTransport(remotePeerId, null);
              }""",
        "do not reconnect quarantined peer",
    )

    replace_once(
        service,
        """              fragmentAccumulator.clearPeer(oldPid);

              if (peerConnections[oldPid]) {""",
        """              fragmentAccumulator.clearPeer(oldPid);
              compatibilityByPeer.delete(oldPid);
              quarantinedPeers.delete(oldPid);

              if (peerConnections[oldPid]) {""",
        "clear compatibility state for departed peers",
    )

    replace_once(
        service,
        """            peers = updatedPeers;
            await removeStalePeers(updatedPeers);""",
        """            peers = updatedPeers;
            await removeStalePeers(updatedPeers);
            await syncP2PCompatibilityStatus();""",
        "persist P2P candidate peer count",
    )

    replace_once(
        service,
        """          const initializeWebSocketSignalingClient = async () => {""",
        """          let signalingReconnectTimer = null;

          const clearSignalingReconnect = () => {
            if (signalingReconnectTimer != null) {
              clearTimeout(signalingReconnectTimer);
              signalingReconnectTimer = null;
            }
          };

          const recordSignalingFailure = async (phase, error) => {
            const detail = `${phase}:${String(error?.stack || error)}`.slice(0, 1500);
            await setDataInAsyncStorage('p2p_last_signaling_error', detail);
            await setDataInAsyncStorage(
              'wsStatusMessage',
              `❌ P2P signaling error: ${detail}`,
            );
          };

          let initializeWebSocketSignalingClient;
          const startSignalingConnection = async () => {
            try {
              await initializeWebSocketSignalingClient();
            } catch (error) {
              await recordSignalingFailure('connect', error);
              throw error;
            }
          };

          const scheduleSignalingReconnect = () => {
            clearSignalingReconnect();
            signalingReconnectTimer = setTimeout(() => {
              signalingReconnectTimer = null;
              void (async () => {
                if (
                  wsSignalingClient == null &&
                  (await getDataFromAsyncStorage('wsIsRunning')) === 'true'
                ) {
                  await startSignalingConnection();
                }
              })().catch(error => recordSignalingFailure('reconnect', error));
            }, RECONNECT_WS_TIMER);
          };

          initializeWebSocketSignalingClient = async () => {""",
        "supervised signaling reconnect helpers",
    )

    replace_once(
        service,
        """                wsSignalingClient = null;
                setTimeout(async () => {
                  if (
                    wsSignalingClient == null &&
                    (await getDataFromAsyncStorage('wsIsRunning')) === 'true'
                  ) {
                    initializeWebSocketSignalingClient();
                  }
                }, RECONNECT_WS_TIMER);""",
        """                wsSignalingClient = null;
                scheduleSignalingReconnect();""",
        "single cancellable signaling reconnect timer",
    )

    replace_once(
        service,
        """              wsSignalingClient.onopen = async () => {
                await cleanupPeerConnections();""",
        """              wsSignalingClient.onopen = async () => {
                clearSignalingReconnect();
                await setDataInAsyncStorage('p2p_last_signaling_error', '');
                await cleanupPeerConnections();""",
        "clear reconnect state after signaling open",
    )

    replace_once(
        service,
        """          // start websocket signaling connection
          initializeWebSocketSignalingClient();""",
        """          // Start through the same supervised path used by reconnects.
          await startSignalingConnection();""",
        "supervised initial signaling connection",
    )

    replace_once(
        service,
        """          stopServicesP2P = async () => {
            // 1) Stop listening to clipboard events""",
        """          stopServicesP2P = async () => {
            clearSignalingReconnect();
            // 1) Stop listening to clipboard events""",
        "cancel signaling reconnect on service stop",
    )

    text = service.read_text(encoding="utf-8")
    for forbidden in (
        "P2P_COMPATIBILITY_JSON",
        "P2P_DC_KEEPALIVE_JSON",
        "type: 'COMPATIBILITY'",
        "case 'COMPATIBILITY'",
        "channel.send(P2P_COMPATIBILITY_JSON)",
        "keyFingerprint",
        "localKeyFingerprint",
        "setTimeout(async () =>",
        "\n          initializeWebSocketSignalingClient();",
    ):
        if forbidden in text:
            raise RuntimeError(
                f"legacy-unsafe, detached or secret-derived signaling remained: {forbidden}"
            )


if __name__ == "__main__":
    main()

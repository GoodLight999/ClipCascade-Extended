#!/usr/bin/env python3
"""Negotiate P2P compatibility through forwarded OFFER/ANSWER metadata.

The upstream signaling server forwards only OFFER, ANSWER and ICE_CANDIDATE.
Unknown message types are discarded. Compatibility therefore travels as an
optional top-level field on OFFER/ANSWER: Extended peers consume it, while
legacy peers ignore it and continue to read only the SDP field. The metadata
contains protocol and encryption mode only; wrong keys are detected by AEAD.
Signaling reconnect uses one supervised, cancellable timer.
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
        """          const P2P_COMPATIBILITY_PROTOCOL = 1;
          const P2P_COMPATIBILITY_JSON = JSON.stringify({
            _cc_compat: true,
            protocol: P2P_COMPATIBILITY_PROTOCOL,
            cipherEnabled: cipher_enabled === 'true',
          });
          const P2P_DC_KEEPALIVE_JSON = JSON.stringify({
            _cc_keepalive: true,
            compatibility: {
              protocol: P2P_COMPATIBILITY_PROTOCOL,
              cipherEnabled: cipher_enabled === 'true',
            },
          });""",
        """          const P2P_COMPATIBILITY_PROTOCOL = 1;
          const localCompatibility = {
            protocol: P2P_COMPATIBILITY_PROTOCOL,
            cipherEnabled: cipher_enabled === 'true',
          };""",
        "legacy-safe local compatibility descriptor",
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
              compatibilityByPeer.set(remotePeerId, 'unknown');
              channel.send(P2P_COMPATIBILITY_JSON);
              startDataChannelHeartbeat(remotePeerId, channel);""",
        """            channel.onopen = async () => {
              if (!compatibilityByPeer.has(remotePeerId)) {
                compatibilityByPeer.set(remotePeerId, 'unknown');
              }
              startDataChannelHeartbeat(remotePeerId, channel);""",
        "do not overwrite negotiated compatibility on channel open",
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

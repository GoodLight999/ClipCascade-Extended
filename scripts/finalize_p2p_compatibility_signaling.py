#!/usr/bin/env python3
"""Negotiate P2P compatibility through forwarded OFFER/ANSWER metadata.

The upstream signaling server forwards only OFFER, ANSWER and ICE_CANDIDATE.
Unknown message types are discarded. Compatibility therefore travels as an
optional top-level field on OFFER/ANSWER: Extended peers consume it, while
legacy peers ignore it and continue to read only the SDP field. The metadata
contains protocol and encryption mode only; wrong keys are detected by AEAD.
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

    text = service.read_text(encoding="utf-8")
    for forbidden in (
        "P2P_COMPATIBILITY_JSON",
        "P2P_DC_KEEPALIVE_JSON",
        "type: 'COMPATIBILITY'",
        "case 'COMPATIBILITY'",
        "channel.send(P2P_COMPATIBILITY_JSON)",
        "keyFingerprint",
        "localKeyFingerprint",
    ):
        if forbidden in text:
            raise RuntimeError(
                f"legacy-unsafe, secret-derived or unforwarded control remained: {forbidden}"
            )


if __name__ == "__main__":
    main()

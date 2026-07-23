#!/usr/bin/env python3
"""Negotiate compatibility through signaling so legacy peers never parse control frames as clipboard data."""
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
            keyFingerprint: localKeyFingerprint,
          });
          const P2P_DC_KEEPALIVE_JSON = JSON.stringify({
            _cc_keepalive: true,
            compatibility: {
              protocol: P2P_COMPATIBILITY_PROTOCOL,
              cipherEnabled: cipher_enabled === 'true',
              keyFingerprint: localKeyFingerprint,
            },
          });""",
        """          const P2P_COMPATIBILITY_PROTOCOL = 1;
          const localCompatibility = {
            protocol: P2P_COMPATIBILITY_PROTOCOL,
            cipherEnabled: cipher_enabled === 'true',
            keyFingerprint: localKeyFingerprint,
          };""",
        "signaling-only compatibility payload",
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
            // observed through readyState/onclose and the signaling server heartbeat.
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
        """                    case 'ICE_CANDIDATE':
                      await handleIceCandidate(data.fromPeerId, data.candidate);
                      break;""",
        """                    case 'ICE_CANDIDATE':
                      await handleIceCandidate(data.fromPeerId, data.candidate);
                      break;

                    case 'COMPATIBILITY': {
                      const compatibility = evaluateP2PCompatibility(
                        localCompatibility,
                        data.compatibility,
                      );
                      await markPeerCompatibility(
                        data.fromPeerId,
                        compatibility.state,
                        compatibility.reason,
                      );
                      break;
                    }""",
        "signaling compatibility receiver",
    )

    replace_once(
        service,
        """            channel.onopen = async () => {
              compatibilityByPeer.set(remotePeerId, 'unknown');
              channel.send(P2P_COMPATIBILITY_JSON);
              startDataChannelHeartbeat(remotePeerId, channel);""",
        """            channel.onopen = async () => {
              compatibilityByPeer.set(remotePeerId, 'unknown');
              await signalingSend({
                type: 'COMPATIBILITY',
                fromPeerId: myPeerId,
                toPeerId: remotePeerId,
                compatibility: localCompatibility,
              });
              startDataChannelHeartbeat(remotePeerId, channel);""",
        "send compatibility through signaling",
    )

    # New clients still understand control frames emitted by already-installed .3 builds,
    # but this build does not create any such frames itself.
    text = service.read_text(encoding="utf-8")
    for forbidden in ("P2P_COMPATIBILITY_JSON", "P2P_DC_KEEPALIVE_JSON", "channel.send(P2P_COMPATIBILITY_JSON)"):
        if forbidden in text:
            raise RuntimeError(f"legacy-unsafe data channel control remained: {forbidden}")


if __name__ == "__main__":
    main()

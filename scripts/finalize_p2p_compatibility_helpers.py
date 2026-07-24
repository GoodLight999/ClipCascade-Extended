#!/usr/bin/env python3
"""Replace inline P2P compatibility decisions with unit-tested helpers.

Compatibility signaling contains only protocol and encryption-mode metadata.
Wrong keys are detected by authenticated decryption and quarantined per peer;
no password-derived fingerprint is generated or transmitted. Peer setup and
per-peer operation failures remain observable instead of being detached.
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
        """          websocket_url,
          username,
          hashed_password,
          cipher_enabled,""",
        """          websocket_url,
          username,
          cipher_enabled,""",
        "remove password-derived compatibility input",
    )
    replace_once(
        service,
        """          'websocket_url',
          'username',
          'hashed_password',
          'cipher_enabled',""",
        """          'websocket_url',
          'username',
          'cipher_enabled',""",
        "remove password-derived compatibility storage key",
    )

    replace_once(
        service,
        """          const localKeyFingerprint =
            cipher_enabled === 'true'
              ? await hashCB(hashed_password || '', 7342)
              : 'none';
          const P2P_COMPATIBILITY_PROTOCOL = 1;
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
        "remove password-derived P2P fingerprint descriptor",
    )

    inline_message = """                const mismatch =
                  Number(message.protocol) !== P2P_COMPATIBILITY_PROTOCOL
                    ? 'protocol-version'
                    : Boolean(message.cipherEnabled) !== (cipher_enabled === 'true')
                      ? 'encryption-mode'
                      : cipher_enabled === 'true' &&
                          String(message.keyFingerprint || '') !== localKeyFingerprint
                        ? 'encryption-key'
                        : '';
                await markPeerCompatibility(
                  remotePeerId,
                  mismatch ? 'incompatible' : 'compatible',
                  mismatch,
                );"""
    helper_message = """                const compatibility = evaluateP2PCompatibility(
                  {
                    protocol: P2P_COMPATIBILITY_PROTOCOL,
                    cipherEnabled: cipher_enabled === 'true',
                  },
                  message,
                );
                await markPeerCompatibility(
                  remotePeerId,
                  compatibility.state,
                  compatibility.reason,
                );"""
    replace_once(service, inline_message, helper_message, "direct P2P hello policy")

    inline_keepalive = """                  const mismatch =
                    Number(hello.protocol) !== P2P_COMPATIBILITY_PROTOCOL
                      ? 'protocol-version'
                      : Boolean(hello.cipherEnabled) !== (cipher_enabled === 'true')
                        ? 'encryption-mode'
                        : cipher_enabled === 'true' &&
                            String(hello.keyFingerprint || '') !== localKeyFingerprint
                          ? 'encryption-key'
                          : '';
                  await markPeerCompatibility(
                    remotePeerId,
                    mismatch ? 'incompatible' : 'compatible',
                    mismatch,
                  );"""
    helper_keepalive = """                  const compatibility = evaluateP2PCompatibility(
                    {
                      protocol: P2P_COMPATIBILITY_PROTOCOL,
                      cipherEnabled: cipher_enabled === 'true',
                    },
                    hello,
                  );
                  await markPeerCompatibility(
                    remotePeerId,
                    compatibility.state,
                    compatibility.reason,
                  );"""
    replace_once(service, inline_keepalive, helper_keepalive, "keepalive P2P hello policy")

    inline_envelope = """                try {
                  const maybeEncrypted = JSON.parse(cb);
                  if (
                    maybeEncrypted &&
                    maybeEncrypted.nonce &&
                    maybeEncrypted.ciphertext &&
                    maybeEncrypted.tag
                  ) {
                    await markPeerCompatibility(
                      remotePeerId,
                      'incompatible',
                      'remote-encryption-enabled',
                    );
                    return;
                  }
                } catch (_) {
                  // Plaintext clipboard data is expected when encryption is disabled.
                }
                await markPeerCompatibility(remotePeerId, 'compatible');"""
    helper_envelope = """                if (isEncryptedEnvelope(cb)) {
                  await markPeerCompatibility(
                    remotePeerId,
                    'incompatible',
                    'remote-encryption-enabled',
                  );
                  return;
                }
                await markPeerCompatibility(remotePeerId, 'compatible');"""
    replace_once(service, inline_envelope, helper_envelope, "encrypted-envelope detection")

    replace_once(
        service,
        """                    `decrypt:${String(error?.message || error)}`""",
        """                    `encryption-key:${String(error?.message || error)}`""",
        "post-decrypt key mismatch classification",
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
        """            peers.forEach(async pid => {
              if (pid === myPeerId) return; // skip self
              if (quarantinedPeers.has(pid)) return;
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
        "awaited peer-list reconciliation",
    )


if __name__ == "__main__":
    main()

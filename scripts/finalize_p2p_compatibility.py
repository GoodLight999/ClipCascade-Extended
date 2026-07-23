#!/usr/bin/env python3
"""Negotiate P2P encryption compatibility and quarantine only mismatched peers."""
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
        """          websocket_url,
          username,
          cipher_enabled,""",
        """          websocket_url,
          username,
          hashed_password,
          cipher_enabled,""",
        "P2P compatibility key destructuring",
    )
    replace_once(
        service,
        """          'websocket_url',
          'username',
          'cipher_enabled',""",
        """          'websocket_url',
          'username',
          'hashed_password',
          'cipher_enabled',""",
        "P2P compatibility key storage",
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
          const localKeyFingerprint =
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
          });

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
        "P2P compatibility runtime",
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
        """              if (message && message._cc_keepalive === true) {
                return;
              }

              await clearFiles(true);""",
        """              if (message && message._cc_compat === true) {
                const mismatch =
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
                );
                return;
              }
              if (message && message._cc_keepalive === true) {
                if (message.compatibility) {
                  const hello = message.compatibility;
                  const mismatch =
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
                  );
                }
                return;
              }
              if (quarantinedPeers.has(remotePeerId)) return;

              await clearFiles(true);""",
        "P2P compatibility control messages",
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
        """              // Decrypt only for this peer. A wrong key/mode must not flood the
              // entire room with repeated AEAD errors or stop compatible peers.
              if (cipher_enabled === 'true') {
                try {
                  cb = await decrypt(JSON.parse(cb));
                  await markPeerCompatibility(remotePeerId, 'compatible');
                } catch (error) {
                  await markPeerCompatibility(
                    remotePeerId,
                    'incompatible',
                    `decrypt:${String(error?.message || error)}`,
                  );
                  return;
                }
              } else {
                try {
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
                await markPeerCompatibility(remotePeerId, 'compatible');
              }

              // hash clipboard content""",
        "P2P peer-scoped decrypt quarantine",
    )

    replace_once(
        service,
        """            peers.forEach(async pid => {
              if (pid === myPeerId) return; // skip self
              if (!peerConnections[pid]) {""",
        """            peers.forEach(async pid => {
              if (pid === myPeerId) return; // skip self
              if (quarantinedPeers.has(pid)) return;
              if (!peerConnections[pid]) {""",
        "skip quarantined peers during peer-list reconciliation",
    )

    replace_once(
        service,
        """            channel.onopen = async () => {
              startDataChannelHeartbeat(remotePeerId, channel);""",
        """            channel.onopen = async () => {
              compatibilityByPeer.set(remotePeerId, 'unknown');
              channel.send(P2P_COMPATIBILITY_JSON);
              startDataChannelHeartbeat(remotePeerId, channel);""",
        "send P2P compatibility hello",
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


if __name__ == "__main__":
    main()

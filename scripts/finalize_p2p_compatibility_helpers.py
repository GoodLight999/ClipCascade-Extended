#!/usr/bin/env python3
"""Replace inline P2P compatibility decisions with unit-tested helpers."""
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
                    keyFingerprint: localKeyFingerprint,
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
                      keyFingerprint: localKeyFingerprint,
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


if __name__ == "__main__":
    main()

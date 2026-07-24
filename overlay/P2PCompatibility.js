function parseCipherEnabled(value) {
  if (value === true || value === 'true') return true;
  if (value === false || value === 'false') return false;
  return null;
}

export function evaluateP2PCompatibility(local, remote) {
  if (!remote || typeof remote !== 'object') {
    return { state: 'unknown', reason: 'legacy-peer-no-hello' };
  }

  const localProtocol = Number(local?.protocol);
  const remoteProtocol = Number(remote.protocol);
  if (
    !Number.isInteger(localProtocol) ||
    !Number.isInteger(remoteProtocol) ||
    remoteProtocol !== localProtocol
  ) {
    return { state: 'incompatible', reason: 'protocol-version' };
  }

  const localCipher = parseCipherEnabled(local?.cipherEnabled);
  const remoteCipher = parseCipherEnabled(remote.cipherEnabled);
  if (localCipher == null || remoteCipher == null || remoteCipher !== localCipher) {
    return { state: 'incompatible', reason: 'encryption-mode' };
  }

  // Do not exchange a password/key-derived fingerprint. The historical
  // `encryption-key` mismatch class is assigned only after the first
  // authenticated-decryption failure, then quarantined per peer. This avoids
  // exposing a stable offline password verifier in signaling.
  return { state: 'compatible', reason: '' };
}

export function isEncryptedEnvelope(value) {
  let parsed = value;
  if (typeof value === 'string') {
    try {
      parsed = JSON.parse(value);
    } catch (_) {
      return false;
    }
  }
  return Boolean(
    parsed &&
      typeof parsed === 'object' &&
      typeof parsed.nonce === 'string' &&
      typeof parsed.ciphertext === 'string' &&
      typeof parsed.tag === 'string',
  );
}

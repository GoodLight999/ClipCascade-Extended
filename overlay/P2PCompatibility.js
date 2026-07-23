export function evaluateP2PCompatibility(local, remote) {
  if (!remote || typeof remote !== 'object') {
    return { state: 'unknown', reason: 'legacy-peer-no-hello' };
  }
  if (Number(remote.protocol) !== Number(local.protocol)) {
    return { state: 'incompatible', reason: 'protocol-version' };
  }
  if (Boolean(remote.cipherEnabled) !== Boolean(local.cipherEnabled)) {
    return { state: 'incompatible', reason: 'encryption-mode' };
  }
  if (
    Boolean(local.cipherEnabled) &&
    String(remote.keyFingerprint || '') !== String(local.keyFingerprint || '')
  ) {
    return { state: 'incompatible', reason: 'encryption-key' };
  }
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

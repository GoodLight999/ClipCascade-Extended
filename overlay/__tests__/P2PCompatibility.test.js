import {
  evaluateP2PCompatibility,
  isEncryptedEnvelope,
} from '../P2PCompatibility';

describe('P2P compatibility', () => {
  const local = {
    protocol: 1,
    cipherEnabled: true,
    keyFingerprint: 'same-key',
  };

  test('accepts same protocol, encryption mode and key', () => {
    expect(evaluateP2PCompatibility(local, { ...local })).toEqual({
      state: 'compatible',
      reason: '',
    });
  });

  test('rejects protocol mismatch', () => {
    expect(
      evaluateP2PCompatibility(local, { ...local, protocol: 2 }),
    ).toEqual({ state: 'incompatible', reason: 'protocol-version' });
  });

  test('rejects encryption mode mismatch', () => {
    expect(
      evaluateP2PCompatibility(local, { ...local, cipherEnabled: false }),
    ).toEqual({ state: 'incompatible', reason: 'encryption-mode' });
  });

  test('rejects encryption key mismatch', () => {
    expect(
      evaluateP2PCompatibility(local, {
        ...local,
        keyFingerprint: 'different-key',
      }),
    ).toEqual({ state: 'incompatible', reason: 'encryption-key' });
  });

  test('keeps a legacy peer unknown until payload evidence exists', () => {
    expect(evaluateP2PCompatibility(local, null)).toEqual({
      state: 'unknown',
      reason: 'legacy-peer-no-hello',
    });
  });

  test('recognizes an encrypted envelope without misclassifying plain JSON', () => {
    expect(
      isEncryptedEnvelope(
        JSON.stringify({ nonce: 'n', ciphertext: 'c', tag: 't' }),
      ),
    ).toBe(true);
    expect(isEncryptedEnvelope(JSON.stringify({ hello: 'world' }))).toBe(false);
    expect(isEncryptedEnvelope('ordinary clipboard text')).toBe(false);
  });
});

import {
  evaluateP2PCompatibility,
  isEncryptedEnvelope,
} from '../P2PCompatibility';

describe('P2P compatibility', () => {
  const local = {
    protocol: 1,
    cipherEnabled: true,
  };

  test('accepts the same protocol and encryption mode', () => {
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

  test('accepts explicit string boolean values from older peers', () => {
    expect(
      evaluateP2PCompatibility(local, {
        protocol: '1',
        cipherEnabled: 'true',
      }),
    ).toEqual({ state: 'compatible', reason: '' });
  });

  test('rejects malformed encryption flags instead of Boolean coercion', () => {
    expect(
      evaluateP2PCompatibility(local, {
        protocol: 1,
        cipherEnabled: 'not-a-boolean',
      }),
    ).toEqual({ state: 'incompatible', reason: 'encryption-mode' });
  });

  test('does not use a password-derived key fingerprint in signaling policy', () => {
    expect(
      evaluateP2PCompatibility(local, {
        ...local,
        keyFingerprint: 'untrusted-and-ignored',
      }),
    ).toEqual({ state: 'compatible', reason: '' });
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

import {
  classifyInboundError,
  createInboundErrorCoalescer,
} from '../InboundErrorPolicy';

describe('inbound error policy', () => {
  test.each([
    'javax.crypto.AEADBadTagException: Bad auth tag',
    'Failed to decrypt: bad key',
    'Unable to decrypt P2S payload. Check the encryption setting',
  ])('classifies authenticated-decryption failure: %s', detail => {
    expect(classifyInboundError(detail)).toMatchObject({
      code: 'encryption-mismatch',
      fingerprint: 'encryption-mismatch',
    });
  });

  test('classifies malformed JSON separately', () => {
    expect(classifyInboundError('JSON parse failed: unexpected token')).toMatchObject({
      code: 'malformed-payload',
      fingerprint: 'malformed-payload',
    });
  });

  test('preserves unexpected details without exposing them as a dedupe wildcard', () => {
    expect(classifyInboundError(new Error('socket decoder failed'))).toMatchObject({
      code: 'inbound-error',
      message: 'socket decoder failed',
    });
  });

  test('reports the first incident and suppresses rapid duplicates', () => {
    let at = 1_000;
    const policy = createInboundErrorCoalescer({ now: () => at, windowMs: 30_000 });
    const first = policy.record('AEADBadTagException');
    at += 100;
    const second = policy.record('Bad auth tag');
    expect(first).toMatchObject({ shouldReport: true, count: 1 });
    expect(second).toMatchObject({ shouldReport: false, count: 2 });
    expect(policy.snapshot()).toMatchObject({ count: 2, firstAt: 1_000 });
  });

  test('reports again after the incident window', () => {
    let at = 1_000;
    const policy = createInboundErrorCoalescer({ now: () => at, windowMs: 30_000 });
    policy.record('AEADBadTagException');
    at += 30_001;
    expect(policy.record('AEADBadTagException')).toMatchObject({
      shouldReport: true,
      count: 1,
      firstAt: 31_001,
    });
  });

  test('clock rollback cannot accidentally suppress a new incident', () => {
    let at = 10_000;
    const policy = createInboundErrorCoalescer({ now: () => at });
    policy.record('AEADBadTagException');
    at = 9_000;
    expect(policy.record('AEADBadTagException').shouldReport).toBe(true);
  });

  test('a successful payload resets the incident', () => {
    const policy = createInboundErrorCoalescer({ now: () => 1_000 });
    policy.record('AEADBadTagException');
    expect(policy.reset()).toMatchObject({ count: 1 });
    expect(policy.snapshot()).toBeNull();
    expect(policy.record('AEADBadTagException').shouldReport).toBe(true);
  });
});

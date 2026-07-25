import {createOneShotContentGuard} from '../OneShotContentGuard';

describe('one-shot content guard', () => {
  test('local feedback guard clears token after unrelated user action', () => {
    const guard = createOneShotContentGuard({
      windowMs: 5000,
      clearOnMismatch: true,
    });
    guard.mark('image', 'hash-image', 1000);
    expect(guard.consume('text', 'hash-user', 1200)).toEqual({
      suppress: false,
      reason: 'mismatch-cleared',
      metadata: null,
    });
    expect(guard.consume('image', 'hash-image', 1300).suppress).toBe(false);
  });

  test('P2S echo guard survives unrelated inbound traffic until matching echo', () => {
    const guard = createOneShotContentGuard({
      windowMs: 30000,
      clearOnMismatch: false,
    });
    guard.mark('text', 'hash-own', 1000, {deliveryId: 'delivery-1'});
    expect(guard.consume('text', 'hash-other', 1500)).toEqual({
      suppress: false,
      reason: 'mismatch-kept',
      metadata: null,
    });
    expect(guard.consume('text', 'hash-own', 2000)).toEqual({
      suppress: true,
      reason: 'matched',
      metadata: {deliveryId: 'delivery-1'},
    });
  });

  test('type is part of identity and one match is consumed', () => {
    const guard = createOneShotContentGuard({
      windowMs: 5000,
      clearOnMismatch: false,
    });
    guard.mark('image', 'same-hash', 1000);
    expect(guard.consume('text', 'same-hash', 1100).suppress).toBe(false);
    expect(guard.consume('image', 'same-hash', 1200).suppress).toBe(true);
    expect(guard.consume('image', 'same-hash', 1300).suppress).toBe(false);
  });

  test('expiry and clock rollback invalidate tokens and metadata', () => {
    const guard = createOneShotContentGuard({
      windowMs: 100,
      clearOnMismatch: false,
    });
    guard.mark('text', 'hash', 1000, {deliveryId: 'delivery-1'});
    expect(guard.consume('text', 'hash', 1101)).toEqual({
      suppress: false,
      reason: 'expired',
      metadata: null,
    });
    guard.mark('text', 'hash', 1000, {deliveryId: 'delivery-2'});
    expect(guard.consume('text', 'hash', 999)).toEqual({
      suppress: false,
      reason: 'clock-rollback',
      metadata: null,
    });
  });
});

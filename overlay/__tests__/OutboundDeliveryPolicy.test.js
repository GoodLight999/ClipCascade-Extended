import {
  OUTBOUND_DELIVERY,
  classifyOutboundDeliveryResult,
  resolveAwaitingReceiptHead,
} from '../OutboundDeliveryPolicy';

describe('outbound delivery policy', () => {
  test('explicit success outcomes acknowledge queue items', () => {
    for (const result of [
      OUTBOUND_DELIVERY.SENT,
      OUTBOUND_DELIVERY.FEEDBACK_SUPPRESSED,
      OUTBOUND_DELIVERY.POLICY_DISCARDED,
    ]) {
      expect(classifyOutboundDeliveryResult(result)).toEqual({
        action: 'acknowledge',
        status: result,
      });
    }
  });

  test('P2S receipt state keeps head queued', () => {
    expect(
      classifyOutboundDeliveryResult(OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT),
    ).toEqual({
      action: 'await-receipt',
      status: OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT,
    });
  });

  test('unavailable transport waits and undefined cannot acknowledge', () => {
    for (const result of [OUTBOUND_DELIVERY.WAITING, false, null, undefined]) {
      expect(classifyOutboundDeliveryResult(result)).toEqual({
        action: 'wait',
        status: OUTBOUND_DELIVERY.WAITING,
      });
    }
  });

  test('unknown truthy values are rejected instead of acknowledging', () => {
    expect(() => classifyOutboundDeliveryResult(true)).toThrow(
      /Invalid outbound delivery result/,
    );
    expect(() => classifyOutboundDeliveryResult('ok')).toThrow(
      /Invalid outbound delivery result/,
    );
  });

  test('fast receipt lets the active flush continue to the next head', () => {
    expect(resolveAwaitingReceiptHead('delivery-1', 'delivery-2')).toEqual({
      action: 'continue',
      status: 'p2s-receipt-already-acknowledged',
    });
    expect(resolveAwaitingReceiptHead('delivery-1', null)).toEqual({
      action: 'continue',
      status: 'p2s-receipt-already-acknowledged',
    });
  });

  test('receipt wait stops while the same item remains head', () => {
    expect(resolveAwaitingReceiptHead('delivery-1', 'delivery-1')).toEqual({
      action: 'wait',
      status: OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT,
    });
    expect(() => resolveAwaitingReceiptHead('', 'delivery-1')).toThrow(
      /delivery ID/,
    );
  });
});

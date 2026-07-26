import {applyOutboundDeliveryResult} from '../OutboundDeliveryExecutor';
import {OUTBOUND_DELIVERY} from '../OutboundDeliveryPolicy';

function harness({headId = 'delivery-1'} = {}) {
  const calls = [];
  return {
    calls,
    peek: async () => (headId == null ? null : {id: headId}),
    acknowledge: async id => calls.push(['ack', id]),
    updateStatus: async status => calls.push(['status', status]),
  };
}

describe('outbound delivery executor', () => {
  test('explicit P2P success acknowledges the durable head', async () => {
    const queue = harness();
    const result = await applyOutboundDeliveryResult({
      deliveryId: 'delivery-1',
      transportResult: OUTBOUND_DELIVERY.SENT,
      ...queue,
    });
    expect(result).toEqual({action: 'continue', status: 'sent'});
    expect(queue.calls).toEqual([
      ['ack', 'delivery-1'],
      ['status', 'sent'],
    ]);
  });

  test('undefined P2P result cannot accidentally acknowledge queue', async () => {
    const queue = harness();
    const result = await applyOutboundDeliveryResult({
      deliveryId: 'delivery-1',
      transportResult: undefined,
      ...queue,
    });
    expect(result).toEqual({
      action: 'wait',
      status: OUTBOUND_DELIVERY.WAITING,
    });
    expect(queue.calls).toEqual([['status', OUTBOUND_DELIVERY.WAITING]]);
  });

  test('active P2S receipt wait preserves head', async () => {
    const queue = harness({headId: 'delivery-1'});
    const result = await applyOutboundDeliveryResult({
      deliveryId: 'delivery-1',
      transportResult: OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT,
      ...queue,
    });
    expect(result).toEqual({
      action: 'wait',
      status: OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT,
    });
    expect(queue.calls).toEqual([
      ['status', OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT],
    ]);
  });

  test('fast receipt acknowledgement continues in same flush', async () => {
    const queue = harness({headId: 'delivery-2'});
    const result = await applyOutboundDeliveryResult({
      deliveryId: 'delivery-1',
      transportResult: OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT,
      ...queue,
    });
    expect(result).toEqual({
      action: 'continue',
      status: 'p2s-receipt-already-acknowledged',
    });
    expect(queue.calls).toEqual([
      ['status', 'p2s-receipt-already-acknowledged'],
    ]);
  });

  test('policy discard and local feedback are terminal outcomes', async () => {
    for (const transportResult of [
      OUTBOUND_DELIVERY.POLICY_DISCARDED,
      OUTBOUND_DELIVERY.FEEDBACK_SUPPRESSED,
    ]) {
      const queue = harness();
      const result = await applyOutboundDeliveryResult({
        deliveryId: 'delivery-1',
        transportResult,
        ...queue,
      });
      expect(result.action).toBe('continue');
      expect(queue.calls).toEqual([
        ['ack', 'delivery-1'],
        ['status', transportResult],
      ]);
    }
  });
});

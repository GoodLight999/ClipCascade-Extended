import {
  P2S_RECEIPT_TIMEOUT_MS,
  createP2SReceiptTracker,
  shouldAcknowledgeP2SDelivery,
} from '../P2SReceiptTracker';

function fakeTimers() {
  const callbacks = new Map();
  let next = 1;
  return {
    setTimer(callback, delay) {
      const id = next++;
      callbacks.set(id, {callback, delay});
      return id;
    },
    clearTimer(id) {
      callbacks.delete(id);
    },
    fire(id) {
      callbacks.get(id)?.callback();
    },
    first() {
      return callbacks.entries().next().value;
    },
    size() {
      return callbacks.size;
    },
  };
}

describe('P2S receipt tracker', () => {
  test('matching receipt clears active timeout', () => {
    const timers = fakeTimers();
    const tracker = createP2SReceiptTracker({
      setTimer: timers.setTimer,
      clearTimer: timers.clearTimer,
    });
    tracker.begin('delivery-1', () => {});
    expect(tracker.active()).toEqual({id: 'delivery-1'});
    expect(tracker.acknowledge('other')).toBe(false);
    expect(tracker.acknowledge('delivery-1')).toBe(true);
    expect(tracker.active()).toBeNull();
    expect(timers.size()).toBe(0);
  });

  test('begin replaces previous wait without leaking timer', () => {
    const timers = fakeTimers();
    const tracker = createP2SReceiptTracker({
      setTimer: timers.setTimer,
      clearTimer: timers.clearTimer,
    });
    tracker.begin('delivery-1', () => {});
    tracker.begin('delivery-2', () => {});
    expect(tracker.active()).toEqual({id: 'delivery-2'});
    expect(timers.size()).toBe(1);
  });

  test('timeout clears state and reports delivery ID', async () => {
    const timers = fakeTimers();
    const timedOut = [];
    const tracker = createP2SReceiptTracker({
      setTimer: timers.setTimer,
      clearTimer: timers.clearTimer,
    });
    tracker.begin('delivery-1', id => timedOut.push(id));
    const [timerId, timer] = timers.first();
    expect(timer.delay).toBe(P2S_RECEIPT_TIMEOUT_MS);
    timers.fire(timerId);
    await Promise.resolve();
    expect(timedOut).toEqual(['delivery-1']);
    expect(tracker.active()).toBeNull();
    expect(tracker.acknowledge('delivery-1')).toBe(false);
  });

  test('timeout callback rejection is supervised', async () => {
    const timers = fakeTimers();
    const failures = [];
    const tracker = createP2SReceiptTracker({
      onCallbackError: error => failures.push(String(error)),
      setTimer: timers.setTimer,
      clearTimer: timers.clearTimer,
    });
    tracker.begin('delivery-1', async () => {
      throw new Error('timeout recorder failed');
    });
    timers.fire(timers.first()[0]);
    await Promise.resolve();
    await Promise.resolve();
    expect(failures).toHaveLength(1);
    expect(failures[0]).toMatch(/timeout recorder failed/);
  });

  test('cancel returns cancelled delivery ID', () => {
    const tracker = createP2SReceiptTracker();
    tracker.begin('delivery-1', () => {});
    expect(tracker.cancel()).toBe('delivery-1');
    expect(tracker.cancel()).toBeNull();
  });

  test('active receipt or matching late loopback acknowledges exact head', () => {
    expect(
      shouldAcknowledgeP2SDelivery({
        activeReceiptMatched: true,
        queuedHeadId: 'other',
        deliveryId: 'delivery-1',
      }),
    ).toBe(true);
    expect(
      shouldAcknowledgeP2SDelivery({
        activeReceiptMatched: false,
        queuedHeadId: 'delivery-1',
        deliveryId: 'delivery-1',
      }),
    ).toBe(true);
  });

  test('stale callback cannot remove a later queue item', () => {
    expect(
      shouldAcknowledgeP2SDelivery({
        activeReceiptMatched: false,
        queuedHeadId: 'delivery-2',
        deliveryId: 'delivery-1',
      }),
    ).toBe(false);
    expect(
      shouldAcknowledgeP2SDelivery({
        activeReceiptMatched: false,
        queuedHeadId: null,
        deliveryId: '',
      }),
    ).toBe(false);
  });
});

import { createP2SAckTracker } from '../P2SAckTracker';

describe('P2SAckTracker', () => {
  test('acknowledges only the active delivery ID', () => {
    const tracker = createP2SAckTracker({setTimer: () => 1, clearTimer: jest.fn()});
    tracker.begin('delivery-a', jest.fn());
    expect(tracker.acknowledge('delivery-b')).toBe(false);
    expect(tracker.current()).toBe('delivery-a');
    expect(tracker.acknowledge('delivery-a')).toBe(true);
    expect(tracker.current()).toBeNull();
  });

  test('invokes timeout once and clears active state', () => {
    let callback;
    const timedOut = jest.fn();
    const tracker = createP2SAckTracker({
      setTimer: fn => {
        callback = fn;
        return 7;
      },
      clearTimer: jest.fn(),
    });
    tracker.begin('delivery-a', timedOut);
    callback();
    expect(timedOut).toHaveBeenCalledWith('delivery-a');
    expect(tracker.current()).toBeNull();
  });

  test('replacing a flight cancels the old timer', () => {
    const clearTimer = jest.fn();
    let timerId = 0;
    const tracker = createP2SAckTracker({
      setTimer: () => {
        timerId += 1;
        return timerId;
      },
      clearTimer,
    });
    tracker.begin('first', jest.fn());
    tracker.begin('second', jest.fn());
    expect(clearTimer).toHaveBeenCalledWith(1);
    expect(tracker.current()).toBe('second');
  });

  test('cancel returns the previous ID', () => {
    const tracker = createP2SAckTracker({setTimer: () => 1, clearTimer: jest.fn()});
    tracker.begin('delivery-a', jest.fn());
    expect(tracker.cancel()).toBe('delivery-a');
    expect(tracker.current()).toBeNull();
  });
});

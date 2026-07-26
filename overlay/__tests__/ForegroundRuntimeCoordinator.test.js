import {
  FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS,
  createForegroundRuntimeCoordinator,
  shouldPreserveOutboundQueue,
} from '../ForegroundRuntimeCoordinator';

function deferred() {
  let resolve;
  const promise = new Promise(done => {
    resolve = done;
  });
  return {promise, resolve};
}

describe('foreground runtime coordinator', () => {
  test('owns one runtime and rejects a duplicate lease', () => {
    const coordinator = createForegroundRuntimeCoordinator();
    const first = coordinator.acquire('runtime-1', async () => {});
    expect(first).not.toBeNull();
    expect(first.isActive()).toBe(true);
    expect(coordinator.activeRuntimeId()).toBe('runtime-1');
    expect(coordinator.acquire('runtime-2', async () => {})).toBeNull();
    expect(first.finish()).toBe(true);
    expect(first.finish()).toBe(false);
    expect(coordinator.activeRuntimeId()).toBeNull();
  });

  test('restart succeeds only after the active lease finishes', async () => {
    const stopRequested = deferred();
    const coordinator = createForegroundRuntimeCoordinator();
    const lease = coordinator.acquire('runtime-1', async reason => {
      expect(reason).toBe('forced-share-recovery');
      stopRequested.resolve();
    });

    const restartPromise = coordinator.requestRestart('forced-share-recovery');
    await stopRequested.promise;
    expect(coordinator.activeRuntimeId()).toBe('runtime-1');
    expect(lease.finish()).toBe(true);
    await expect(restartPromise).resolves.toEqual({
      hadActiveRuntime: true,
      stopped: true,
      runtimeId: 'runtime-1',
      error: '',
    });
  });

  test('start transitions are serialized and rejection does not poison the chain', async () => {
    const coordinator = createForegroundRuntimeCoordinator();
    const firstGate = deferred();
    const order = [];
    const first = coordinator.runStartTransition(async () => {
      order.push('first-start');
      await firstGate.promise;
      order.push('first-end');
      throw new Error('first failed');
    });
    const second = coordinator.runStartTransition(async () => {
      order.push('second');
      return 2;
    });

    await Promise.resolve();
    expect(order).toEqual(['first-start']);
    firstGate.resolve();
    await expect(first).rejects.toThrow('first failed');
    await expect(second).resolves.toBe(2);
    expect(order).toEqual(['first-start', 'first-end', 'second']);
  });

  test('waitForActiveRuntime resolves only when callback acquires a lease', async () => {
    let timeoutCallback;
    const coordinator = createForegroundRuntimeCoordinator({
      setTimer: callback => {
        timeoutCallback = callback;
        return 9;
      },
      clearTimer: () => {
        timeoutCallback = null;
      },
    });
    const waiting = coordinator.waitForActiveRuntime();
    expect(timeoutCallback).toEqual(expect.any(Function));
    coordinator.acquire('runtime-1', async () => {});
    await expect(waiting).resolves.toBe('runtime-1');
    expect(timeoutCallback).toBeNull();
  });

  test('waitForActiveRuntime returns null on bounded startup timeout', async () => {
    let timeoutCallback;
    const coordinator = createForegroundRuntimeCoordinator({
      setTimer: callback => {
        timeoutCallback = callback;
        return 11;
      },
      clearTimer: () => {},
    });
    const waiting = coordinator.waitForActiveRuntime(8000);
    timeoutCallback();
    await expect(waiting).resolves.toBeNull();
  });

  test('bounded restart timeout never permits replacement while old lease remains', async () => {
    let timeoutCallback;
    const coordinator = createForegroundRuntimeCoordinator({
      setTimer: callback => {
        timeoutCallback = callback;
        return 7;
      },
      clearTimer: () => {},
    });
    coordinator.acquire('runtime-1', async () => {});
    const restartPromise = coordinator.requestRestart(
      'forced-share-recovery',
      FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS,
    );
    await Promise.resolve();
    timeoutCallback();
    await expect(restartPromise).resolves.toEqual({
      hadActiveRuntime: true,
      stopped: false,
      runtimeId: 'runtime-1',
      error: 'foreground-runtime-stop-timeout',
    });
    expect(coordinator.activeRuntimeId()).toBe('runtime-1');
  });

  test('only explicit manual stop discards durable outbound work', () => {
    expect(shouldPreserveOutboundQueue('manual')).toBe(false);
    expect(shouldPreserveOutboundQueue(null)).toBe(false);
    expect(shouldPreserveOutboundQueue('forced-share-recovery')).toBe(true);
    expect(shouldPreserveOutboundQueue('runtime-failure')).toBe(true);
  });
});

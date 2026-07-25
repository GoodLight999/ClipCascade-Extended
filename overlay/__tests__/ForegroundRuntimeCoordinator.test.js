import {
  FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS,
  createForegroundRuntimeCoordinator,
} from '../ForegroundRuntimeCoordinator';

function deferred() {
  let resolve;
  const promise = new Promise(done => {
    resolve = done;
  });
  return { promise, resolve };
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

  test('restart is immediately safe when no runtime is active', async () => {
    const coordinator = createForegroundRuntimeCoordinator();
    await expect(
      coordinator.requestRestart('forced-share-recovery'),
    ).resolves.toEqual({
      hadActiveRuntime: false,
      stopped: true,
      runtimeId: null,
      error: '',
    });
  });

  test('stop callback failure is reported and keeps the lease owned', async () => {
    const coordinator = createForegroundRuntimeCoordinator();
    coordinator.acquire('runtime-1', async () => {
      throw new Error('stop failed');
    });
    const result = await coordinator.requestRestart('forced-share-recovery');
    expect(result).toMatchObject({
      hadActiveRuntime: true,
      stopped: false,
      runtimeId: 'runtime-1',
    });
    expect(result.error).toContain('stop failed');
    expect(coordinator.activeRuntimeId()).toBe('runtime-1');
  });

  test('bounded timeout never permits a replacement while the old lease remains', async () => {
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
    expect(timeoutCallback).toEqual(expect.any(Function));
    timeoutCallback();
    await expect(restartPromise).resolves.toEqual({
      hadActiveRuntime: true,
      stopped: false,
      runtimeId: 'runtime-1',
      error: 'foreground-runtime-stop-timeout',
    });
    expect(coordinator.activeRuntimeId()).toBe('runtime-1');
  });
});

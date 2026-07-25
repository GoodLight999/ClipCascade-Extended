export const FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS = 10_000;
export const FOREGROUND_RUNTIME_START_TIMEOUT_MS = 8_000;
export const MANUAL_FOREGROUND_STOP_REASON = 'manual';

/** Explicit user stop may discard the queue; recovery and failure stops must not. */
export function shouldPreserveOutboundQueue(stopReason) {
  return String(stopReason || MANUAL_FOREGROUND_STOP_REASON) !== MANUAL_FOREGROUND_STOP_REASON;
}

/**
 * Own exactly one JavaScript clipboard/network runtime. Restart and startup
 * transitions are serialized so concurrent UI, Headless JS, and recovery calls
 * cannot stop or replace one another's newly-created foreground service.
 */
export function createForegroundRuntimeCoordinator({
  setTimer = (callback, delay) => setTimeout(callback, delay),
  clearTimer = handle => clearTimeout(handle),
} = {}) {
  let active = null;
  let startTransitionChain = Promise.resolve();
  const acquisitionWaiters = new Set();

  const notifyAcquired = runtimeId => {
    for (const waiter of Array.from(acquisitionWaiters)) {
      acquisitionWaiters.delete(waiter);
      if (waiter.timer != null) clearTimer(waiter.timer);
      waiter.resolve(runtimeId);
    }
  };

  const finish = runtimeId => {
    if (!active || active.runtimeId !== runtimeId) return false;
    const completed = active;
    active = null;
    completed.resolveCompletion();
    return true;
  };

  return {
    acquire(runtimeId, requestStop) {
      if (typeof runtimeId !== 'string' || runtimeId.length === 0) {
        throw new Error('Foreground runtime ID is required');
      }
      if (typeof requestStop !== 'function') {
        throw new TypeError('Foreground runtime stop callback is required');
      }
      if (active) return null;

      let resolveCompletion;
      const completion = new Promise(resolve => {
        resolveCompletion = resolve;
      });
      active = {
        runtimeId,
        requestStop,
        completion,
        resolveCompletion,
      };
      notifyAcquired(runtimeId);
      return {
        runtimeId,
        isActive: () => active?.runtimeId === runtimeId,
        finish: () => finish(runtimeId),
      };
    },

    runStartTransition(task) {
      if (typeof task !== 'function') {
        return Promise.reject(
          new TypeError('Foreground start transition must be a function'),
        );
      }
      const current = startTransitionChain.then(task, task);
      startTransitionChain = current.catch(() => undefined);
      return current;
    },

    waitForActiveRuntime(timeoutMs = FOREGROUND_RUNTIME_START_TIMEOUT_MS) {
      if (active) return Promise.resolve(active.runtimeId);
      return new Promise(resolve => {
        const waiter = {resolve, timer: null};
        waiter.timer = setTimer(() => {
          acquisitionWaiters.delete(waiter);
          resolve(null);
        }, Number(timeoutMs));
        acquisitionWaiters.add(waiter);
      });
    },

    async requestRestart(
      reason,
      timeoutMs = FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS,
    ) {
      const current = active;
      if (!current) {
        return {
          hadActiveRuntime: false,
          stopped: true,
          runtimeId: null,
          error: '',
        };
      }

      try {
        await current.requestStop(String(reason || 'restart'));
      } catch (error) {
        return {
          hadActiveRuntime: true,
          stopped: false,
          runtimeId: current.runtimeId,
          error: String(error?.stack || error),
        };
      }

      let timer = null;
      const timeout = new Promise(resolve => {
        timer = setTimer(() => resolve(false), Number(timeoutMs));
      });
      const completed = await Promise.race([
        current.completion.then(() => true),
        timeout,
      ]);
      if (timer != null) clearTimer(timer);

      return {
        hadActiveRuntime: true,
        stopped: completed && active?.runtimeId !== current.runtimeId,
        runtimeId: current.runtimeId,
        error: completed ? '' : 'foreground-runtime-stop-timeout',
      };
    },

    activeRuntimeId() {
      return active?.runtimeId || null;
    },
  };
}

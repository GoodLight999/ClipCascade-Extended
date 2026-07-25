export const FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS = 10_000;

/**
 * Own exactly one JavaScript clipboard/network runtime. A forced restart first
 * asks the current lease to stop and then waits for that exact lease to finish;
 * a replacement runtime must never be launched while the old one still owns
 * callbacks, listeners, or transports.
 */
export function createForegroundRuntimeCoordinator({
  setTimer = (callback, delay) => setTimeout(callback, delay),
  clearTimer = handle => clearTimeout(handle),
} = {}) {
  let active = null;

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
      return {
        runtimeId,
        isActive: () => active?.runtimeId === runtimeId,
        finish: () => finish(runtimeId),
      };
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

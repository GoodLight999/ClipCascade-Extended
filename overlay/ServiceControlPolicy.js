export const FOREGROUND_STOP_TIMEOUT_MS = 10_000;

export function nextRequestedServiceState(persistedValue) {
  return persistedValue === 'true' ? 'false' : 'true';
}

/**
 * UI presses toggle. Recovery paths request an explicit state. A stale-runtime
 * recovery may force the start branch even when the persisted request is still
 * true, because that flag is not proof that the Notifee handler is alive.
 */
export function resolveRequestedServiceState(
  persistedValue,
  desiredState = null,
  forceRestart = false,
) {
  const persistedState = persistedValue === 'true' ? 'true' : 'false';
  if (desiredState === 'true' || desiredState === 'false') {
    const forcedStart = desiredState === 'true' && forceRestart === true;
    return {
      nextState: desiredState,
      noOp: persistedState === desiredState && !forcedStart,
      persistedState,
      forcedStart,
    };
  }
  return {
    nextState: nextRequestedServiceState(persistedState),
    noOp: false,
    persistedState,
    forcedStart: false,
  };
}

export function hasForegroundStopTimedOut(
  startedAt,
  now,
  timeoutMs = FOREGROUND_STOP_TIMEOUT_MS,
) {
  const elapsed = Number(now) - Number(startedAt);
  return elapsed < 0 || elapsed >= Number(timeoutMs);
}

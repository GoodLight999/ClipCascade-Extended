export const FOREGROUND_STOP_TIMEOUT_MS = 10_000;

export function nextRequestedServiceState(persistedValue) {
  return persistedValue === 'true' ? 'false' : 'true';
}

/**
 * UI presses toggle. Recovery paths request an explicit state and become
 * idempotent even if another actor changes persisted state between polling and
 * execution.
 */
export function resolveRequestedServiceState(persistedValue, desiredState = null) {
  const persistedState = persistedValue === 'true' ? 'true' : 'false';
  if (desiredState === 'true' || desiredState === 'false') {
    return {
      nextState: desiredState,
      noOp: persistedState === desiredState,
      persistedState,
    };
  }
  return {
    nextState: nextRequestedServiceState(persistedState),
    noOp: false,
    persistedState,
  };
}

export function hasForegroundStopTimedOut(
  startedAt,
  now,
  timeoutMs = FOREGROUND_STOP_TIMEOUT_MS,
) {
  return Number(now) - Number(startedAt) >= Number(timeoutMs);
}

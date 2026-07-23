export const FOREGROUND_STOP_TIMEOUT_MS = 10_000;

export function nextRequestedServiceState(persistedValue) {
  return persistedValue === 'true' ? 'false' : 'true';
}

export function hasForegroundStopTimedOut(
  startedAt,
  now,
  timeoutMs = FOREGROUND_STOP_TIMEOUT_MS,
) {
  return Number(now) - Number(startedAt) >= Number(timeoutMs);
}

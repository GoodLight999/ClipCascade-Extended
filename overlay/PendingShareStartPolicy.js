export const PENDING_SHARE_START_RETRY_MS = 5_000;

/**
 * Decide whether the visible React UI should start the foreground runtime for
 * an Android Share payload that MainActivity has already persisted.
 *
 * The same decision covers restored sessions, immediately-after-login shares,
 * and shares delivered while the websocket screen is already open. A clock
 * rollback starts one fresh attempt instead of suppressing recovery forever.
 */
export function shouldStartPendingShare({
  sessionReady,
  payloadPending,
  serviceRequested,
  buttonEnabled,
  startInFlight,
  lastAttemptAt,
  now,
  retryMs = PENDING_SHARE_START_RETRY_MS,
}) {
  if (
    sessionReady !== true ||
    payloadPending !== true ||
    serviceRequested === true ||
    buttonEnabled !== true ||
    startInFlight === true
  ) {
    return false;
  }

  if (lastAttemptAt == null || !Number.isFinite(Number(lastAttemptAt))) {
    return true;
  }

  const elapsed = Number(now) - Number(lastAttemptAt);
  return elapsed < 0 || elapsed >= Number(retryMs);
}

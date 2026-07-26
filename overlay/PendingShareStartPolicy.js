export const PENDING_SHARE_START_RETRY_MS = 5_000;
export const FOREGROUND_HEARTBEAT_STALE_MS = 15_000;
export const FOREGROUND_START_GRACE_MS = 20_000;

const STARTING_STATES = new Set([
  'notification-starting',
  'notification-displayed',
  'handler-starting',
]);

function isFreshTimestamp(value, now, maxAgeMs) {
  const timestamp = Number(value);
  const current = Number(now);
  if (!Number.isFinite(timestamp) || !Number.isFinite(current)) return false;
  const elapsed = current - timestamp;
  // A wall-clock rollback must not make a dead runtime look fresh forever.
  return elapsed >= 0 && elapsed <= Number(maxAgeMs);
}

/**
 * A persisted wsIsRunning=true value is only a request, not liveness proof.
 * Heartbeat is authoritative once the handler is running; a short start grace
 * prevents duplicate restarts while Notifee is still creating the handler.
 */
export function isForegroundRuntimeFresh({
  serviceState,
  heartbeatAt,
  lastStartedAt,
  now,
  heartbeatStaleMs = FOREGROUND_HEARTBEAT_STALE_MS,
  startGraceMs = FOREGROUND_START_GRACE_MS,
}) {
  if (isFreshTimestamp(heartbeatAt, now, heartbeatStaleMs)) return true;
  return (
    STARTING_STATES.has(String(serviceState || '')) &&
    isFreshTimestamp(lastStartedAt, now, startGraceMs)
  );
}

/**
 * Decide whether the visible React UI should start or restart the foreground
 * runtime for an Android Share payload already persisted by MainActivity.
 *
 * The same decision covers restored sessions, immediately-after-login shares,
 * shares delivered while the websocket screen is already open, and a stale
 * service whose requested flag survived process/runtime death.
 */
export function planPendingShareStart({
  sessionReady,
  payloadPending,
  serviceRequested,
  serviceState,
  heartbeatAt,
  lastStartedAt,
  buttonEnabled,
  startInFlight,
  lastAttemptAt,
  now,
  retryMs = PENDING_SHARE_START_RETRY_MS,
}) {
  if (sessionReady !== true) {
    return { start: false, forceRestart: false, reason: 'session-not-ready' };
  }
  if (payloadPending !== true) {
    return { start: false, forceRestart: false, reason: 'no-payload' };
  }
  if (buttonEnabled !== true) {
    return { start: false, forceRestart: false, reason: 'control-busy' };
  }
  if (startInFlight === true) {
    return { start: false, forceRestart: false, reason: 'start-in-flight' };
  }

  const runtimeFresh = isForegroundRuntimeFresh({
    serviceState,
    heartbeatAt,
    lastStartedAt,
    now,
  });
  if (serviceRequested === true && runtimeFresh) {
    return { start: false, forceRestart: false, reason: 'runtime-active' };
  }

  if (lastAttemptAt != null && Number.isFinite(Number(lastAttemptAt))) {
    const elapsed = Number(now) - Number(lastAttemptAt);
    if (elapsed >= 0 && elapsed < Number(retryMs)) {
      return { start: false, forceRestart: false, reason: 'retry-throttled' };
    }
  }

  const forceRestart = serviceRequested === true;
  return {
    start: true,
    forceRestart,
    reason: forceRestart ? 'stale-runtime' : 'runtime-stopped',
  };
}

export function shouldStartPendingShare(input) {
  return planPendingShareStart(input).start;
}

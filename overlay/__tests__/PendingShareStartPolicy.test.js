import {
  FOREGROUND_HEARTBEAT_STALE_MS,
  FOREGROUND_START_GRACE_MS,
  PENDING_SHARE_START_RETRY_MS,
  isForegroundRuntimeFresh,
  planPendingShareStart,
  shouldStartPendingShare,
} from '../PendingShareStartPolicy';

const ready = {
  sessionReady: true,
  payloadPending: true,
  serviceRequested: false,
  serviceState: 'stopped',
  heartbeatAt: null,
  lastStartedAt: null,
  buttonEnabled: true,
  startInFlight: false,
  lastAttemptAt: null,
  now: 100_000,
};

describe('pending Android Share foreground start policy', () => {
  test('starts a persisted share when the session is ready and runtime is stopped', () => {
    expect(planPendingShareStart(ready)).toEqual({
      start: true,
      forceRestart: false,
      reason: 'runtime-stopped',
    });
    expect(shouldStartPendingShare(ready)).toBe(true);
  });

  test.each([
    ['session is not ready', { sessionReady: false }, 'session-not-ready'],
    ['no payload is pending', { payloadPending: false }, 'no-payload'],
    ['start/stop control is busy', { buttonEnabled: false }, 'control-busy'],
    ['another start is in flight', { startInFlight: true }, 'start-in-flight'],
  ])('does not start when %s', (_, patch, reason) => {
    expect(planPendingShareStart({ ...ready, ...patch })).toEqual({
      start: false,
      forceRestart: false,
      reason,
    });
  });

  test('fresh heartbeat proves that a requested runtime is active', () => {
    const input = {
      ...ready,
      serviceRequested: true,
      serviceState: 'running',
      heartbeatAt: ready.now - FOREGROUND_HEARTBEAT_STALE_MS,
    };
    expect(isForegroundRuntimeFresh(input)).toBe(true);
    expect(planPendingShareStart(input)).toEqual({
      start: false,
      forceRestart: false,
      reason: 'runtime-active',
    });
  });

  test('recent starting state gets a bounded grace period before heartbeat exists', () => {
    const input = {
      ...ready,
      serviceRequested: true,
      serviceState: 'handler-starting',
      lastStartedAt: ready.now - FOREGROUND_START_GRACE_MS,
    };
    expect(isForegroundRuntimeFresh(input)).toBe(true);
    expect(planPendingShareStart(input).start).toBe(false);
  });

  test('requested flag with stale heartbeat forces a restart', () => {
    const input = {
      ...ready,
      serviceRequested: true,
      serviceState: 'running',
      heartbeatAt: ready.now - FOREGROUND_HEARTBEAT_STALE_MS - 1,
      lastStartedAt: ready.now - FOREGROUND_START_GRACE_MS - 1,
    };
    expect(isForegroundRuntimeFresh(input)).toBe(false);
    expect(planPendingShareStart(input)).toEqual({
      start: true,
      forceRestart: true,
      reason: 'stale-runtime',
    });
  });

  test('clock rollback cannot make a dead runtime look fresh', () => {
    const input = {
      ...ready,
      serviceRequested: true,
      serviceState: 'running',
      heartbeatAt: ready.now + 1,
      lastStartedAt: ready.now + 1,
    };
    expect(isForegroundRuntimeFresh(input)).toBe(false);
    expect(planPendingShareStart(input).forceRestart).toBe(true);
  });

  test('suppresses rapid retries after a failed start', () => {
    expect(
      planPendingShareStart({
        ...ready,
        lastAttemptAt: ready.now - PENDING_SHARE_START_RETRY_MS + 1,
      }),
    ).toEqual({
      start: false,
      forceRestart: false,
      reason: 'retry-throttled',
    });
    expect(
      planPendingShareStart({
        ...ready,
        lastAttemptAt: ready.now - PENDING_SHARE_START_RETRY_MS,
      }).start,
    ).toBe(true);
  });

  test('clock rollback or invalid retry timestamp permits one fresh recovery', () => {
    expect(
      planPendingShareStart({
        ...ready,
        lastAttemptAt: ready.now + 1,
      }).start,
    ).toBe(true);
    expect(
      planPendingShareStart({
        ...ready,
        lastAttemptAt: 'not-a-number',
      }).start,
    ).toBe(true);
  });
});

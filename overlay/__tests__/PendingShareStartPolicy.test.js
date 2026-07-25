import {
  PENDING_SHARE_START_RETRY_MS,
  shouldStartPendingShare,
} from '../PendingShareStartPolicy';

const ready = {
  sessionReady: true,
  payloadPending: true,
  serviceRequested: false,
  buttonEnabled: true,
  startInFlight: false,
  lastAttemptAt: null,
  now: 10_000,
};

describe('pending Android Share foreground start policy', () => {
  test('starts a persisted share when the session is ready and runtime is stopped', () => {
    expect(shouldStartPendingShare(ready)).toBe(true);
  });

  test.each([
    ['session is not ready', { sessionReady: false }],
    ['no payload is pending', { payloadPending: false }],
    ['runtime is already requested', { serviceRequested: true }],
    ['start/stop button is locked', { buttonEnabled: false }],
    ['another start is in flight', { startInFlight: true }],
  ])('does not start when %s', (_, patch) => {
    expect(shouldStartPendingShare({ ...ready, ...patch })).toBe(false);
  });

  test('suppresses rapid retries after a failed start', () => {
    expect(
      shouldStartPendingShare({
        ...ready,
        lastAttemptAt: ready.now - PENDING_SHARE_START_RETRY_MS + 1,
      }),
    ).toBe(false);
    expect(
      shouldStartPendingShare({
        ...ready,
        lastAttemptAt: ready.now - PENDING_SHARE_START_RETRY_MS,
      }),
    ).toBe(true);
  });

  test('clock rollback cannot suppress recovery indefinitely', () => {
    expect(
      shouldStartPendingShare({
        ...ready,
        lastAttemptAt: ready.now + 1,
      }),
    ).toBe(true);
  });

  test('invalid prior attempt timestamps are treated as no prior attempt', () => {
    expect(
      shouldStartPendingShare({
        ...ready,
        lastAttemptAt: 'not-a-number',
      }),
    ).toBe(true);
  });
});

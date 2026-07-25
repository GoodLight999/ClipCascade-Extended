import {
  FOREGROUND_STOP_TIMEOUT_MS,
  hasForegroundStopTimedOut,
  nextRequestedServiceState,
  resolveRequestedServiceState,
} from '../ServiceControlPolicy';

describe('foreground service control policy', () => {
  test('uses persisted state rather than delayed React state', () => {
    expect(nextRequestedServiceState('true')).toBe('false');
    expect(nextRequestedServiceState('false')).toBe('true');
    expect(nextRequestedServiceState(null)).toBe('true');
  });

  test('UI mode toggles the persisted state', () => {
    expect(resolveRequestedServiceState('true')).toEqual({
      nextState: 'false',
      noOp: false,
      persistedState: 'true',
      forcedStart: false,
    });
    expect(resolveRequestedServiceState('false')).toEqual({
      nextState: 'true',
      noOp: false,
      persistedState: 'false',
      forcedStart: false,
    });
  });

  test('automatic start is idempotent when another path already started', () => {
    expect(resolveRequestedServiceState('true', 'true')).toEqual({
      nextState: 'true',
      noOp: true,
      persistedState: 'true',
      forcedStart: false,
    });
    expect(resolveRequestedServiceState('false', 'true')).toEqual({
      nextState: 'true',
      noOp: false,
      persistedState: 'false',
      forcedStart: false,
    });
  });

  test('stale-runtime recovery can force the start branch despite persisted true', () => {
    expect(resolveRequestedServiceState('true', 'true', true)).toEqual({
      nextState: 'true',
      noOp: false,
      persistedState: 'true',
      forcedStart: true,
    });
  });

  test('forceRestart preserves an explicit stop and executes it', () => {
    expect(resolveRequestedServiceState('true', 'false', true)).toEqual({
      nextState: 'false',
      noOp: false,
      persistedState: 'true',
      forcedStart: false,
    });
  });

  test('invalid desired states cannot bypass normal toggle semantics', () => {
    expect(resolveRequestedServiceState('true', 'start-now', true)).toEqual({
      nextState: 'false',
      noOp: false,
      persistedState: 'true',
      forcedStart: false,
    });
  });

  test('bounds stop waiting', () => {
    expect(
      hasForegroundStopTimedOut(
        1000,
        1000 + FOREGROUND_STOP_TIMEOUT_MS - 1,
      ),
    ).toBe(false);
    expect(
      hasForegroundStopTimedOut(1000, 1000 + FOREGROUND_STOP_TIMEOUT_MS),
    ).toBe(true);
  });

  test('clock rollback cannot make stop waiting unbounded', () => {
    expect(hasForegroundStopTimedOut(10_000, 9_999)).toBe(true);
  });
});

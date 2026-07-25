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
    });
    expect(resolveRequestedServiceState('false')).toEqual({
      nextState: 'true',
      noOp: false,
      persistedState: 'false',
    });
  });

  test('automatic start is idempotent when another path already started', () => {
    expect(resolveRequestedServiceState('true', 'true')).toEqual({
      nextState: 'true',
      noOp: true,
      persistedState: 'true',
    });
    expect(resolveRequestedServiceState('false', 'true')).toEqual({
      nextState: 'true',
      noOp: false,
      persistedState: 'false',
    });
  });

  test('invalid desired states cannot bypass normal toggle semantics', () => {
    expect(resolveRequestedServiceState('true', 'start-now')).toMatchObject({
      nextState: 'false',
      noOp: false,
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

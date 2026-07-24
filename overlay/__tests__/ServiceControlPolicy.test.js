import {
  FOREGROUND_STOP_TIMEOUT_MS,
  hasForegroundStopTimedOut,
  nextRequestedServiceState,
} from '../ServiceControlPolicy';

describe('foreground service control policy', () => {
  test('uses persisted state rather than delayed React state', () => {
    expect(nextRequestedServiceState('true')).toBe('false');
    expect(nextRequestedServiceState('false')).toBe('true');
    expect(nextRequestedServiceState(null)).toBe('true');
  });

  test('bounds stop waiting', () => {
    expect(hasForegroundStopTimedOut(1000, 1000 + FOREGROUND_STOP_TIMEOUT_MS - 1)).toBe(false);
    expect(hasForegroundStopTimedOut(1000, 1000 + FOREGROUND_STOP_TIMEOUT_MS)).toBe(true);
  });
});

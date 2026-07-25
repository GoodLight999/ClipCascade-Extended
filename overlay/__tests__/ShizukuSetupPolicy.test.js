import {
  isShizukuSetupVerified,
  planShizukuSetup,
} from '../ShizukuSetupPolicy';

describe('Shizuku one-time setup policy', () => {
  test('does not require Shizuku after Android retained both grants', () => {
    expect(
      planShizukuSetup({
        installed: true,
        running: false,
        permissionGranted: false,
        readLogs: true,
        overlay: true,
      }),
    ).toEqual({
      state: 'already-configured',
      requestPermission: false,
      applySetup: false,
    });
  });

  test('distinguishes missing installation from a Binder startup race', () => {
    expect(planShizukuSetup({ installed: false })).toEqual({
      state: 'not-installed',
      requestPermission: false,
      applySetup: false,
    });
    expect(
      planShizukuSetup({
        installed: true,
        running: false,
        permissionGranted: false,
      }),
    ).toEqual({
      state: 'binder-pending',
      requestPermission: true,
      applySetup: true,
    });
  });

  test('requests permission when the Binder is live and authorization is absent', () => {
    expect(
      planShizukuSetup({
        installed: true,
        running: true,
        permissionGranted: false,
      }),
    ).toEqual({
      state: 'permission-required',
      requestPermission: true,
      applySetup: true,
    });
  });

  test('applies directly when Shizuku is already authorized', () => {
    expect(
      planShizukuSetup({
        installed: true,
        running: true,
        permissionGranted: true,
        readLogs: false,
        overlay: false,
      }),
    ).toEqual({
      state: 'ready-to-apply',
      requestPermission: false,
      applySetup: true,
    });
  });

  test('accepts a JSON status and verifies retained grants', () => {
    const status = JSON.stringify({ readLogs: true, overlay: true });
    expect(isShizukuSetupVerified(status)).toBe(true);
    expect(planShizukuSetup(status).state).toBe('already-configured');
  });

  test('treats malformed status as uninstalled instead of guessing', () => {
    expect(planShizukuSetup('not-json').state).toBe('not-installed');
    expect(isShizukuSetupVerified('not-json')).toBe(false);
  });
});

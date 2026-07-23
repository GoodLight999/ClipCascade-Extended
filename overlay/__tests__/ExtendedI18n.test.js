import {
  STRINGS,
  getExtendedStrings,
  localizeRuntimeMessage,
} from '../ExtendedI18n';

describe('Extended product localization', () => {
  const required = [
    'username',
    'password',
    'serverUrl',
    'login',
    'start',
    'stop',
    'logout',
    'accessibility',
    'overlay',
    'shizukuOpen',
    'shizukuSetup',
    'adb',
    'selfTest',
    'autoDebug',
    'copy',
    'close',
    'checkingService',
    'verifyingSession',
    'requestTimedOut',
    'loginSuccess',
    'loginFailed',
    'logoutSuccess',
    'logoutFailed',
    'diagnosticsOverall',
    'diagnosticRecovery',
  ];

  test.each(['ja', 'zh', 'en'])('%s contains all product labels', locale => {
    const strings = getExtendedStrings(locale);
    for (const key of required) {
      expect(typeof strings[key]).toBe('string');
      expect(strings[key].length).toBeGreaterThan(0);
    }
  });

  test('Japanese and Chinese are not accidental English fallbacks', () => {
    expect(STRINGS.ja.login).not.toBe(STRINGS.en.login);
    expect(STRINGS.zh.login).not.toBe(STRINGS.en.login);
    expect(STRINGS.ja.autoDebug).not.toBe(STRINGS.en.autoDebug);
    expect(STRINGS.zh.autoDebug).not.toBe(STRINGS.en.autoDebug);
    expect(STRINGS.ja.checkingService).not.toBe(STRINGS.en.checkingService);
    expect(STRINGS.zh.verifyingSession).not.toBe(STRINGS.en.verifyingSession);
  });

  test('localizes inherited Japanese runtime messages without hiding details', () => {
    const strings = getExtendedStrings('ja');
    expect(localizeRuntimeMessage('Checking foreground service...', strings)).toBe(
      strings.checkingService,
    );
    expect(localizeRuntimeMessage('Verifying Session...', strings)).toBe(
      strings.verifyingSession,
    );
    expect(localizeRuntimeMessage('Login successful: 200', strings)).toBe(
      `${strings.loginSuccess}: 200`,
    );
    expect(localizeRuntimeMessage('Error: Request timed out', strings)).toBe(
      `${strings.genericError}: ${strings.requestTimedOut}`,
    );
    expect(
      localizeRuntimeMessage(
        '❌ Foreground service: ForegroundServiceStartNotAllowedException',
        strings,
      ),
    ).toContain('ForegroundServiceStartNotAllowedException');
  });
});

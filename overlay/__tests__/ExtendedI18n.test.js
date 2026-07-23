import { STRINGS, getExtendedStrings } from '../ExtendedI18n';

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
  });
});

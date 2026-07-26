import { Buffer } from 'buffer';
import { fragmentUtf8String } from '../Utf8Fragmenter';

describe('fragmentUtf8String', () => {
  test.each([
    'plain ASCII clipboard text',
    '日本語の長文を壊さずに分割する必要があります。'.repeat(2000),
    '絵文字😀🧪🚀と漢字とASCII-mixed-content-'.repeat(1200),
    'e\u0301 combining mark remains byte-exact '.repeat(1500),
  ])('round-trips UTF-8 content exactly', input => {
    const fragments = fragmentUtf8String(input, 127);
    expect(fragments.join('')).toBe(input);
    for (const fragment of fragments) {
      expect(Buffer.byteLength(fragment, 'utf8')).toBeLessThanOrEqual(127);
    }
  });

  test('keeps one code point intact when budget is smaller than it', () => {
    const fragments = fragmentUtf8String('😀A', 1);
    expect(fragments).toEqual(['😀', 'A']);
  });

  test('validates arguments', () => {
    expect(() => fragmentUtf8String(null, 10)).toThrow(TypeError);
    expect(() => fragmentUtf8String('x', 0)).toThrow(RangeError);
  });
});

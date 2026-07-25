import fs from 'fs';
import path from 'path';

function channel(value) {
  const normalized = value / 255;
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4;
}

function luminance(hex) {
  const value = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map(index =>
    channel(Number.parseInt(value.slice(index, index + 2), 16)),
  );
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(left, right) {
  const brighter = Math.max(luminance(left), luminance(right));
  const darker = Math.min(luminance(left), luminance(right));
  return (brighter + 0.05) / (darker + 0.05);
}

describe('diagnostic report contrast', () => {
  const source = fs.readFileSync(
    path.join(__dirname, '..', 'ExtendedControlPanel.js'),
    'utf8',
  );
  const palettes = Array.from(
    source.matchAll(/surface: '(#[0-9a-f]{6})',[\s\S]*?text: '(#[0-9a-f]{6})'/gi),
    match => ({ surface: match[1], text: match[2] }),
  );

  test('defines explicit light and dark palettes', () => {
    expect(palettes).toHaveLength(2);
    expect(palettes).toContainEqual({ surface: '#1b1b1f', text: '#f5f5f7' });
    expect(palettes).toContainEqual({ surface: '#ffffff', text: '#15171a' });
  });

  test.each(['dark', 'light'])('%s palette exceeds normal-text AA contrast', mode => {
    const palette = mode === 'dark' ? palettes[0] : palettes[1];
    expect(contrast(palette.surface, palette.text)).toBeGreaterThanOrEqual(7);
  });

  test('does not delegate diagnostic colors to OEM theme attributes', () => {
    expect(source).not.toContain('PlatformColor(');
  });
});

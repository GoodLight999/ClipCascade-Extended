/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import App from '../App';

jest.useFakeTimers();

test('renders and unmounts without losing bootstrap work', async () => {
  let renderer: ReactTestRenderer.ReactTestRenderer | undefined;

  await ReactTestRenderer.act(async () => {
    renderer = ReactTestRenderer.create(<App />);
    await Promise.resolve();
  });

  expect(renderer).toBeDefined();

  await ReactTestRenderer.act(async () => {
    renderer?.unmount();
    jest.runOnlyPendingTimers();
    await Promise.resolve();
  });
});

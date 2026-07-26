import { createDetachedTaskSupervisor } from '../DetachedTaskSupervisor';

describe('DetachedTaskSupervisor', () => {
  test('runs successful tasks without recording a failure', async () => {
    const recordFailure = jest.fn();
    const task = jest.fn().mockResolvedValue('ok');
    const runDetached = createDetachedTaskSupervisor(recordFailure);

    await expect(runDetached('success', task)).resolves.toBe('ok');
    expect(task).toHaveBeenCalledTimes(1);
    expect(recordFailure).not.toHaveBeenCalled();
  });

  test('records rejected tasks and resolves the host callback boundary', async () => {
    const failure = new Error('network failed');
    const recordFailure = jest.fn().mockResolvedValue(undefined);
    const runDetached = createDetachedTaskSupervisor(recordFailure);

    await expect(
      runDetached('signaling-message', () => Promise.reject(failure)),
    ).resolves.toBeUndefined();
    expect(recordFailure).toHaveBeenCalledWith('signaling-message', failure);
  });

  test('does not create a second rejection when failure recording fails', async () => {
    const recordFailure = jest.fn().mockRejectedValue(new Error('storage failed'));
    const runDetached = createDetachedTaskSupervisor(recordFailure);

    await expect(
      runDetached('outbound-retry', () => Promise.reject(new Error('send failed'))),
    ).resolves.toBeUndefined();
    expect(recordFailure).toHaveBeenCalledTimes(1);
  });

  test('reports a non-function task through the same safe boundary', async () => {
    const recordFailure = jest.fn().mockResolvedValue(undefined);
    const runDetached = createDetachedTaskSupervisor(recordFailure);

    await expect(runDetached('invalid-task', null)).resolves.toBeUndefined();
    expect(recordFailure).toHaveBeenCalledWith(
      'invalid-task',
      expect.any(TypeError),
    );
  });

  test('rejects an invalid recorder at construction time', () => {
    expect(() => createDetachedTaskSupervisor(null)).toThrow(TypeError);
  });
});

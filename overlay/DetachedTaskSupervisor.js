export function createDetachedTaskSupervisor(recordFailure) {
  if (typeof recordFailure !== 'function') {
    throw new TypeError('Detached task failure recorder must be a function');
  }

  return function runDetached(scope, task) {
    if (typeof task !== 'function') {
      return Promise.resolve()
        .then(() =>
          recordFailure(
            String(scope || 'unknown'),
            new TypeError('Detached task must be a function'),
          ),
        )
        .catch(() => undefined);
    }

    return Promise.resolve()
      .then(task)
      .catch(error =>
        Promise.resolve()
          .then(() => recordFailure(String(scope || 'unknown'), error))
          .catch(() => undefined),
      );
  };
}

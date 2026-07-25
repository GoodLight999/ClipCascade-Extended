function normalizeStatus(input) {
  if (input && typeof input === 'object') return input;
  if (typeof input !== 'string' || input.trim() === '') return {};
  try {
    return JSON.parse(input);
  } catch (_) {
    return {};
  }
}

/**
 * Pure, unit-testable setup planner. Shizuku is only a one-time privilege
 * bootstrapper; once READ_LOGS and overlay app-ops are retained, runtime must
 * remain independent from the Shizuku process.
 *
 * An installed-but-not-yet-observed Binder is deliberately allowed to enter
 * requestPermission. The native layer has a bounded sticky-Binder wait and can
 * distinguish a startup race from a genuinely stopped Shizuku service.
 */
export function planShizukuSetup(statusInput) {
  const status = normalizeStatus(statusInput);
  const readLogs = status.readLogs === true;
  const overlay = status.overlay === true;

  if (readLogs && overlay) {
    return {
      state: 'already-configured',
      requestPermission: false,
      applySetup: false,
    };
  }
  if (status.installed !== true) {
    return {
      state: 'not-installed',
      requestPermission: false,
      applySetup: false,
    };
  }
  if (status.running !== true) {
    return {
      state: 'binder-pending',
      requestPermission: true,
      applySetup: true,
    };
  }
  if (status.permissionGranted !== true) {
    return {
      state: 'permission-required',
      requestPermission: true,
      applySetup: true,
    };
  }
  return {
    state: 'ready-to-apply',
    requestPermission: false,
    applySetup: true,
  };
}

export function isShizukuSetupVerified(statusInput) {
  const status = normalizeStatus(statusInput);
  return status.readLogs === true && status.overlay === true;
}

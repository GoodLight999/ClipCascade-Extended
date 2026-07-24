// Historical regression label kept searchable by CI: event-listener-order.
function parseObject(value) {
  if (value && typeof value === 'object') return value;
  if (typeof value !== 'string' || value.trim() === '') return {};
  try {
    return JSON.parse(value);
  } catch (_) {
    return { raw: value };
  }
}

function check(id, level, detail) {
  return { id, level, detail: String(detail ?? '') };
}

export function analyzeDiagnostics(
  statusInput,
  nativeProbeInput = {},
  now = Date.now(),
) {
  const status = parseObject(statusInput);
  const probe = parseObject(nativeProbeInput);
  const clipboardProbe = parseObject(probe.clipboard);
  const eventBridge = parseObject(probe.eventBridge);
  const queue = parseObject(status.outboundQueueStatus);
  const checks = [];

  const listenerStateReady =
    status.nativeDeliveryReady &&
    String(status.jsListenerStatus || '').includes('ready-after-registration');
  checks.push(
    check(
      'native-react-event-bridge',
      listenerStateReady && eventBridge.received === true ? 'PASS' : 'FAIL',
      `nativeReady=${status.nativeDeliveryReady}; js=${
        status.jsListenerStatus || 'missing'
      }; activeProbe=${JSON.stringify(eventBridge)}`,
    ),
  );
  checks.push(
    check(
      'accessibility',
      status.accessibilityEnabled ? 'PASS' : 'WARN',
      `${status.accessibilityEnabled}; ${
        status.accessibilityServiceStatus || 'idle'
      }`,
    ),
  );
  checks.push(
    check('overlay', status.overlay ? 'PASS' : 'FAIL', String(status.overlay)),
  );
  checks.push(
    check(
      'capture-coordinator',
      String(status.captureCoordinator || '').includes('abandoned-after')
        ? 'FAIL'
        : 'PASS',
      status.captureCoordinator || 'missing',
    ),
  );
  checks.push(
    check(
      'native-events',
      Number(status.pendingEvents || 0) === 0 ? 'PASS' : 'WARN',
      status.pendingEvents || 0,
    ),
  );
  checks.push(
    check(
      'outbound-queue',
      ['send-error', 'dropped-permanent-error'].includes(queue.state)
        ? 'FAIL'
        : Number(queue.count || 0) > 0
          ? 'WARN'
          : 'PASS',
      JSON.stringify(queue),
    ),
  );

  const heartbeatAt = Number(status.foregroundServiceHeartbeatAt || 0);
  const heartbeatAge = heartbeatAt > 0 ? Math.max(0, now - heartbeatAt) : null;
  let foregroundLevel = 'WARN';
  let foregroundDetail = 'synchronization is not requested';
  if (status.foregroundServiceError) {
    foregroundLevel = 'FAIL';
    foregroundDetail = status.foregroundServiceError;
  } else if (status.serviceRequested) {
    if (heartbeatAge != null && heartbeatAge <= 15_000) {
      foregroundLevel = 'PASS';
      foregroundDetail = `heartbeatAgeMs=${heartbeatAge}; state=${
        status.foregroundServiceState || 'unknown'
      }; instance=${status.foregroundServiceInstanceId || 'missing'}`;
    } else {
      foregroundLevel = 'FAIL';
      foregroundDetail = `requested but heartbeat is ${
        heartbeatAge == null ? 'missing' : `${heartbeatAge} ms old`
      }; state=${status.foregroundServiceState || 'unknown'}`;
    }
  }
  checks.push(check('foreground-service', foregroundLevel, foregroundDetail));

  const duplicateSuppressedAt = Number(
    status.foregroundServiceDuplicateSuppressedAt || 0,
  );
  const duplicateAge =
    duplicateSuppressedAt > 0 ? Math.max(0, now - duplicateSuppressedAt) : null;
  checks.push(
    check(
      'foreground-runtime-singleton',
      duplicateAge != null && duplicateAge <= 10 * 60_000 ? 'WARN' : 'PASS',
      duplicateAge == null
        ? `instance=${status.foregroundServiceInstanceId || 'none'}; no duplicate observed`
        : `duplicate runtime suppressed ${duplicateAge} ms ago; instance=${
            status.foregroundServiceInstanceId || 'none'
          }`,
    ),
  );

  const recoveryStatus = String(status.foregroundServiceRecoveryStatus || '');
  const recoveryFailed = /(?:recovery-failed|headless-error)/i.test(recoveryStatus);
  checks.push(
    check(
      'foreground-recovery',
      recoveryFailed ? 'FAIL' : 'PASS',
      recoveryStatus || 'no recovery attempt recorded',
    ),
  );

  checks.push(
    check(
      'shared-payload',
      String(status.sharedPayloadStatus || '').includes('error') ? 'FAIL' : 'PASS',
      status.sharedPayloadStatus || 'idle',
    ),
  );

  const peerSetupError = String(status.p2pLastPeerSetupError || '');
  const peerOperationError = String(status.p2pLastPeerOperationError || '');
  const signalingError = String(status.p2pLastSignalingError || '');
  const incompatiblePeers = Number(status.p2pIncompatiblePeers || 0);
  const p2pLevel =
    peerSetupError || peerOperationError || signalingError
      ? 'FAIL'
      : incompatiblePeers > 0
        ? 'WARN'
        : 'PASS';
  checks.push(
    check(
      'p2p-compatibility',
      p2pLevel,
      `compatible=${status.p2pCompatiblePeers || 0}; incompatible=${
        status.p2pIncompatiblePeers || 0
      }; candidates=${status.p2pCandidatePeers || 0}; signalingError=${
        signalingError || 'none'
      }; setupError=${peerSetupError || 'none'}; operationError=${
        peerOperationError || 'none'
      }`,
    ),
  );

  checks.push(
    check(
      'foreground-clipboard-probe',
      clipboardProbe.clipboardRead === true
        ? 'PASS'
        : clipboardProbe.clipboardRead === false
          ? 'FAIL'
          : 'WARN',
      JSON.stringify(clipboardProbe),
    ),
  );

  const overall = checks.some(item => item.level === 'FAIL')
    ? 'FAIL'
    : checks.some(item => item.level === 'WARN')
      ? 'WARN'
      : 'PASS';
  return {
    overall,
    checks,
    status,
    probe,
    generatedAt: new Date(now).toISOString(),
  };
}

const DEFAULT_REPORT_TEXT = {
  reportTitle: 'ClipCascade Extended diagnostics',
  diagnosticsOverall: 'Overall',
  diagnosticsGenerated: 'Generated',
  diagnosticsRawStatus: 'Raw status',
  diagnosticsNativeProbe: 'Native probe',
  pass: 'PASS',
  warn: 'CHECK',
  fail: 'FAIL',
  diagnosticNativeReact: 'Native → React event bridge',
  diagnosticAccessibility: 'Accessibility copy detection',
  diagnosticOverlay: 'Overlay permission',
  diagnosticCapture: 'Clipboard capture coordinator',
  diagnosticNativeEvents: 'Pending native events',
  diagnosticOutboundQueue: 'Durable outbound queue',
  diagnosticForeground: 'Foreground Service heartbeat',
  diagnosticSingleton: 'Foreground runtime singleton',
  diagnosticRecovery: 'Visible-capture runtime recovery',
  diagnosticSharedPayload: 'Android Share / staged payload',
  diagnosticP2P: 'P2P compatibility',
  diagnosticClipboardProbe: 'Foreground clipboard probe',
};

const CHECK_LABEL_KEYS = {
  'native-react-event-bridge': 'diagnosticNativeReact',
  accessibility: 'diagnosticAccessibility',
  overlay: 'diagnosticOverlay',
  'capture-coordinator': 'diagnosticCapture',
  'native-events': 'diagnosticNativeEvents',
  'outbound-queue': 'diagnosticOutboundQueue',
  'foreground-service': 'diagnosticForeground',
  'foreground-runtime-singleton': 'diagnosticSingleton',
  'foreground-recovery': 'diagnosticRecovery',
  'shared-payload': 'diagnosticSharedPayload',
  'p2p-compatibility': 'diagnosticP2P',
  'foreground-clipboard-probe': 'diagnosticClipboardProbe',
};

export function formatDiagnosticsReport(report, textInput = DEFAULT_REPORT_TEXT) {
  const supplied =
    typeof textInput === 'string' ? { reportTitle: textInput } : textInput || {};
  const text = { ...DEFAULT_REPORT_TEXT, ...supplied };
  const levels = { PASS: text.pass, WARN: text.warn, FAIL: text.fail };
  const lines = [
    text.reportTitle,
    `${text.diagnosticsOverall}: ${levels[report.overall] || report.overall}`,
    `${text.diagnosticsGenerated}: ${report.generatedAt}`,
    '',
  ];
  for (const item of report.checks) {
    const key = CHECK_LABEL_KEYS[item.id];
    const label = (key && text[key]) || item.id;
    lines.push(`[${levels[item.level] || item.level}] ${label}`);
    lines.push(`  ${item.detail}`);
  }
  lines.push(
    '',
    `${text.diagnosticsRawStatus}:`,
    JSON.stringify(report.status, null, 2),
  );
  lines.push(
    '',
    `${text.diagnosticsNativeProbe}:`,
    JSON.stringify(report.probe, null, 2),
  );
  return lines.join('\n');
}

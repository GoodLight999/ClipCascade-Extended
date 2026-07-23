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

export function analyzeDiagnostics(statusInput, nativeProbeInput = {}) {
  const status = parseObject(statusInput);
  const probe = parseObject(nativeProbeInput);
  const queue = parseObject(status.outboundQueueStatus);
  const checks = [];

  checks.push(
    check(
      'event-listener-order',
      status.nativeDeliveryReady &&
        String(status.jsListenerStatus || '').includes('ready-after-registration')
        ? 'PASS'
        : 'FAIL',
      `nativeReady=${status.nativeDeliveryReady}; js=${status.jsListenerStatus || 'missing'}`,
    ),
  );
  checks.push(
    check(
      'accessibility',
      status.accessibilityEnabled ? 'PASS' : 'WARN',
      `${status.accessibilityEnabled}; ${status.accessibilityServiceStatus || 'idle'}`,
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
  checks.push(
    check(
      'foreground-service',
      status.foregroundServiceError ? 'FAIL' : status.serviceRequested ? 'PASS' : 'WARN',
      status.foregroundServiceError || status.connectionStatus || 'not requested',
    ),
  );
  checks.push(
    check(
      'shared-payload',
      String(status.sharedPayloadStatus || '').includes('error') ? 'FAIL' : 'PASS',
      status.sharedPayloadStatus || 'idle',
    ),
  );
  checks.push(
    check(
      'p2p-compatibility',
      Number(status.p2pIncompatiblePeers || 0) > 0 ? 'WARN' : 'PASS',
      `compatible=${status.p2pCompatiblePeers || 0}; incompatible=${status.p2pIncompatiblePeers || 0}; candidates=${status.p2pCandidatePeers || 0}`,
    ),
  );
  checks.push(
    check(
      'foreground-clipboard-probe',
      probe.clipboardRead === true ? 'PASS' : probe.clipboardRead === false ? 'FAIL' : 'WARN',
      JSON.stringify(probe),
    ),
  );

  const overall = checks.some(item => item.level === 'FAIL')
    ? 'FAIL'
    : checks.some(item => item.level === 'WARN')
      ? 'WARN'
      : 'PASS';
  return { overall, checks, status, probe, generatedAt: new Date().toISOString() };
}

export function formatDiagnosticsReport(report, title = 'ClipCascade Extended diagnostics') {
  const lines = [title, `Overall: ${report.overall}`, `Generated: ${report.generatedAt}`, ''];
  for (const item of report.checks) {
    lines.push(`[${item.level}] ${item.id}`);
    lines.push(`  ${item.detail}`);
  }
  lines.push('', 'Raw status:', JSON.stringify(report.status, null, 2));
  lines.push('', 'Native probe:', JSON.stringify(report.probe, null, 2));
  return lines.join('\n');
}

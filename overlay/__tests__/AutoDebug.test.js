import { analyzeDiagnostics, formatDiagnosticsReport } from '../AutoDebug';

describe('automatic diagnostics', () => {
  const now = 1_000_000;
  const healthyStatus = {
    nativeDeliveryReady: true,
    jsListenerStatus: 'ready-after-registration',
    accessibilityEnabled: true,
    accessibilityServiceStatus: 'enabled',
    overlay: true,
    captureCoordinator: 'idle;inFlight=false',
    pendingEvents: 0,
    outboundQueueStatus: JSON.stringify({ count: 0, state: 'idle' }),
    foregroundServiceError: '',
    foregroundServiceState: 'running',
    foregroundServiceHeartbeatAt: String(now - 1_000),
    serviceRequested: true,
    connectionStatus: 'connected',
    sharedPayloadStatus: 'idle',
    p2pIncompatiblePeers: 0,
    p2pCompatiblePeers: 1,
    p2pCandidatePeers: 1,
  };
  const healthyProbe = {
    eventBridge: { received: true, token: 'test' },
    clipboard: { clipboardRead: true, payloadPresent: true },
  };

  test('returns PASS for a healthy active snapshot', () => {
    const result = analyzeDiagnostics(healthyStatus, healthyProbe, now);
    expect(result.overall).toBe('PASS');
    expect(result.checks.every(item => item.level === 'PASS')).toBe(true);
  });

  test('detects the historical listener-drain ordering failure', () => {
    const result = analyzeDiagnostics(
      { ...healthyStatus, jsListenerStatus: '', nativeDeliveryReady: true },
      healthyProbe,
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(
      result.checks.find(item => item.id === 'native-react-event-bridge'),
    ).toMatchObject({ level: 'FAIL' });
  });

  test('detects an active native event that never reaches React', () => {
    const result = analyzeDiagnostics(
      healthyStatus,
      {
        ...healthyProbe,
        eventBridge: { received: false, error: 'timeout' },
      },
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(
      result.checks.find(item => item.id === 'native-react-event-bridge'),
    ).toMatchObject({ level: 'FAIL' });
  });

  test('detects a requested service with a stale heartbeat', () => {
    const result = analyzeDiagnostics(
      {
        ...healthyStatus,
        foregroundServiceHeartbeatAt: String(now - 20_000),
      },
      healthyProbe,
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(result.checks.find(item => item.id === 'foreground-service')).toMatchObject({
      level: 'FAIL',
    });
  });

  test('reports foreground-service failure and queued outbound data', () => {
    const result = analyzeDiagnostics(
      {
        ...healthyStatus,
        foregroundServiceError: 'ForegroundServiceStartNotAllowedException',
        outboundQueueStatus: JSON.stringify({ count: 2, state: 'send-error' }),
      },
      {
        eventBridge: { received: true },
        clipboard: { clipboardRead: false, error: 'denied' },
      },
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(formatDiagnosticsReport(result)).toContain(
      'ForegroundServiceStartNotAllowedException',
    );
  });
});

import { analyzeDiagnostics, formatDiagnosticsReport } from '../AutoDebug';

describe('automatic diagnostics', () => {
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
    serviceRequested: true,
    connectionStatus: 'connected',
    sharedPayloadStatus: 'idle',
    p2pIncompatiblePeers: 0,
    p2pCompatiblePeers: 1,
    p2pCandidatePeers: 1,
  };

  test('returns PASS for a healthy snapshot', () => {
    const result = analyzeDiagnostics(healthyStatus, {
      clipboard: { clipboardRead: true, payloadPresent: true },
    });
    expect(result.overall).toBe('PASS');
    expect(result.checks.every(item => item.level === 'PASS')).toBe(true);
  });

  test('detects the historical listener-drain ordering failure', () => {
    const result = analyzeDiagnostics(
      { ...healthyStatus, jsListenerStatus: '', nativeDeliveryReady: true },
      { clipboard: { clipboardRead: true } },
    );
    expect(result.overall).toBe('FAIL');
    expect(result.checks.find(item => item.id === 'event-listener-order')).toMatchObject({
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
      { clipboard: { clipboardRead: false, error: 'denied' } },
    );
    expect(result.overall).toBe('FAIL');
    expect(formatDiagnosticsReport(result)).toContain('ForegroundServiceStartNotAllowedException');
  });
});

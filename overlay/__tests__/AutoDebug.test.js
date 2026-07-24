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
    foregroundServiceDetachedError: '',
    foregroundServiceDetachedErrorAt: '',
    foregroundServiceState: 'running',
    foregroundServiceHeartbeatAt: String(now - 1_000),
    foregroundServiceRecoveryStatus: 'heartbeat-healthy:test',
    serviceRequested: true,
    connectionStatus: 'connected',
    sharedPayloadStatus: 'idle',
    p2pIncompatiblePeers: 0,
    p2pCompatiblePeers: 1,
    p2pCandidatePeers: 1,
    p2pLastPeerSetupError: '',
    p2pLastPeerOperationError: '',
    p2pLastSignalingError: '',
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
    expect(
      result.checks.find(item => item.id === 'foreground-service'),
    ).toMatchObject({ level: 'FAIL' });
  });

  test('detects detached timer or WebRTC callback failures', () => {
    const result = analyzeDiagnostics(
      {
        ...healthyStatus,
        foregroundServiceDetachedError:
          'datachannel-message:peer-a:malformed fragment metadata',
        foregroundServiceDetachedErrorAt: String(now - 25),
      },
      healthyProbe,
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(
      result.checks.find(item => item.id === 'foreground-service'),
    ).toMatchObject({
      level: 'FAIL',
      detail: expect.stringContaining('datachannel-message:peer-a'),
    });
  });

  test('detects visible-capture recovery failures', () => {
    const result = analyzeDiagnostics(
      {
        ...healthyStatus,
        foregroundServiceRecoveryStatus:
          'recovery-failed:ForegroundServiceStartNotAllowedException',
      },
      healthyProbe,
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(
      result.checks.find(item => item.id === 'foreground-recovery'),
    ).toMatchObject({ level: 'FAIL' });
  });

  test('detects current P2P signaling failures', () => {
    const result = analyzeDiagnostics(
      {
        ...healthyStatus,
        p2pLastSignalingError: 'reconnect:network unavailable',
      },
      healthyProbe,
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(
      result.checks.find(item => item.id === 'p2p-compatibility'),
    ).toMatchObject({ level: 'FAIL' });
  });

  test('detects current P2P peer setup failures', () => {
    const result = analyzeDiagnostics(
      {
        ...healthyStatus,
        p2pLastPeerSetupError: 'peer-a:createOffer failed',
      },
      healthyProbe,
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(
      result.checks.find(item => item.id === 'p2p-compatibility'),
    ).toMatchObject({ level: 'FAIL' });
  });

  test('detects current serialized peer-operation failures', () => {
    const result = analyzeDiagnostics(
      {
        ...healthyStatus,
        p2pLastPeerOperationError: 'peer-b:setRemoteDescription failed',
      },
      healthyProbe,
      now,
    );
    expect(result.overall).toBe('FAIL');
    expect(
      result.checks.find(item => item.id === 'p2p-compatibility'),
    ).toMatchObject({ level: 'FAIL' });
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

  test('localizes report headings, levels and check names', () => {
    const result = analyzeDiagnostics(healthyStatus, healthyProbe, now);
    const report = formatDiagnosticsReport(result, {
      reportTitle: '自動診断レポート',
      diagnosticsOverall: '総合判定',
      diagnosticsGenerated: '生成日時',
      diagnosticsRawStatus: '生の状態情報',
      diagnosticsNativeProbe: 'ネイティブ実経路検査',
      pass: '合格',
      warn: '要確認',
      fail: '失敗',
      diagnosticNativeReact: 'ネイティブ→Reactイベント経路',
    });
    expect(report).toContain('総合判定: 合格');
    expect(report).toContain('[合格] ネイティブ→Reactイベント経路');
    expect(report).toContain('生の状態情報:');
    expect(report).toContain('ネイティブ実経路検査:');
  });
});

import React, { useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  NativeEventEmitter,
  ScrollView,
  Text,
  TouchableOpacity,
  useColorScheme,
  View,
} from 'react-native';
import Clipboard from '@react-native-clipboard/clipboard';

import { analyzeDiagnostics, formatDiagnosticsReport } from './AutoDebug';
import {
  getExtendedStrings,
  localizeRuntimeMessage,
} from './ExtendedI18n';
import {
  isShizukuSetupVerified,
  planShizukuSetup,
} from './ShizukuSetupPolicy';

const ADB_COMMANDS = [
  'adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS',
  'adb shell appops set com.clipcascade.extended android:system_alert_window allow',
].join('\n');

function pretty(value) {
  if (value == null || value === '') return '—';
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  try {
    return JSON.stringify(JSON.parse(String(value)), null, 2);
  } catch (_) {
    return String(value);
  }
}

function parseJson(value) {
  if (value && typeof value === 'object') return value;
  try {
    return JSON.parse(String(value || '{}'));
  } catch (_) {
    return {};
  }
}

function setupError(code, detail = '') {
  const error = new Error(code);
  error.code = code;
  error.detail = String(detail || '');
  return error;
}

function formatSetupError(error, text) {
  const code = String(error?.code || 'SETUP_FAILED');
  const detail = String(error?.detail || '');
  return `${text.setupFailed}\n\n${code}${detail ? `\n${detail}` : ''}`;
}

export default function ExtendedControlPanel({ NativeBridgeModule, notifee }) {
  const text = getExtendedStrings();
  const styles = createStyles(useColorScheme() === 'dark');
  const [busy, setBusy] = useState(false);
  const [dialog, setDialog] = useState({
    visible: false,
    title: '',
    body: '',
    copy: '',
  });

  const show = (title, body, copy = body) => {
    setDialog({
      visible: true,
      title,
      body: String(body),
      copy: String(copy),
    });
  };

  const run = async action => {
    if (busy) return;
    setBusy(true);
    try {
      await action();
    } catch (error) {
      show(text.setupFailed, formatSetupError(error, text));
    } finally {
      setBusy(false);
    }
  };

  const runEventBridgeProbe = async () =>
    new Promise(resolve => {
      const token = `cc-probe-${Date.now()}-${Math.random()}`;
      const emitter = new NativeEventEmitter(NativeBridgeModule);
      let finished = false;
      let subscription;
      let timeout;
      const finish = (received, error = '') => {
        if (finished) return;
        finished = true;
        if (timeout) clearTimeout(timeout);
        subscription?.remove();
        resolve({ received, token, error });
      };
      subscription = emitter.addListener(
        'onExtendedDiagnosticProbe',
        receivedToken => {
          if (receivedToken === token) finish(true);
        },
      );
      timeout = setTimeout(
        () => finish(false, 'native event was not observed within 2000 ms'),
        2000,
      );
      Promise.resolve(NativeBridgeModule.runEventBridgeProbe(token)).catch(
        error => finish(false, String(error)),
      );
    });

  const showStatus = async () => {
    const status = parseJson(await NativeBridgeModule.getReliabilityStatus());
    const lines = [
      `${text.packageLabel}: ${status.packageName}`,
      `${text.requestedLabel}: ${status.serviceRequested}`,
      `${text.connectionStatus}: ${localizeRuntimeMessage(
        status.connectionStatus,
        text,
      )}`,
      `${text.accessibilityLabel}: ${status.accessibilityEnabled}`,
      `${text.accessibilityStateLabel}: ${
        status.accessibilityServiceStatus || '—'
      }`,
      `${text.captureLabel}: ${status.accessibilityCaptureStatus || '—'}`,
      `${text.coordinatorLabel}: ${status.captureCoordinator || '—'}`,
      `${text.listenerLabel}: ${status.jsListenerStatus || '—'}`,
      `${text.nativeDeliveryLabel}: ${status.nativeDeliveryReady}`,
      `${text.pendingEventsLabel}: ${status.pendingEvents}`,
      `${text.sharedPayloadLabel}: ${status.sharedPayloadStatus || '—'}`,
      `${text.outboundQueueLabel}:\n${pretty(status.outboundQueueStatus)}`,
      `${text.foregroundStateLabel}: ${status.foregroundServiceState || '—'}`,
      `${text.foregroundHeartbeatLabel}: ${
        status.foregroundServiceHeartbeatAt || '—'
      }`,
      `${text.foregroundErrorLabel}: ${status.foregroundServiceError || '—'}`,
      `${text.foregroundRecoveryLabel}: ${
        status.foregroundServiceRecoveryStatus || '—'
      }`,
      `${text.p2pCompatibilityLabel}: ${status.p2pCandidatePeers || 0}/${
        status.p2pCompatiblePeers || 0
      }/${status.p2pIncompatiblePeers || 0}`,
      `${text.p2pLastErrorLabel}: P2P=${
        status.p2pLastCompatibilityError || '—'
      }; P2S=${status.p2sLastInboundErrorCode || '—'}/${
        status.p2sLastInboundErrorCount || 0
      }`,
      `${text.readLogsLabel}: ${status.readLogs}`,
      `${text.overlayLabel}: ${status.overlay}`,
      `${text.shizukuLabel}:\n${pretty(status.shizuku)}`,
      `${text.restartLabel}: ${status.restartReceiverStatus || '—'}`,
    ];
    show(text.selfTest, lines.join('\n'));
  };

  const runAutoDebug = async () => {
    const eventBridge = await runEventBridgeProbe();
    const status = parseJson(await NativeBridgeModule.getReliabilityStatus());
    const probe = NativeBridgeModule.runNativeAutoDebug
      ? parseJson(await NativeBridgeModule.runNativeAutoDebug())
      : { clipboard: { clipboardRead: null }, reason: 'native probe unavailable' };
    probe.eventBridge = eventBridge;
    const report = analyzeDiagnostics(status, probe);
    const body = formatDiagnosticsReport(report, text);
    show(text.autoDebug, body);
  };

  const getShizukuStatus = async () =>
    parseJson(await NativeBridgeModule.getShizukuStatus());

  const runShizuku = async () => {
    let status = await getShizukuStatus();
    const plan = planShizukuSetup(status);

    if (plan.state === 'already-configured') {
      show(
        'Shizuku',
        `${text.setupComplete}\n\nREAD_LOGS: ${status.readLogs}\nOverlay: ${status.overlay}`,
      );
      return;
    }
    if (plan.state === 'not-installed') {
      await NativeBridgeModule.openOrGetShizuku();
      show('Shizuku', `${text.shizukuOpen}\n\n${text.shizukuGuide}`);
      return;
    }
    if (plan.state === 'not-running') {
      show('Shizuku', text.shizukuGuide);
      return;
    }

    if (plan.requestPermission) {
      await NativeBridgeModule.requestShizukuPermission();
      status = await getShizukuStatus();
      if (status.permissionGranted !== true) {
        throw setupError('SHIZUKU_PERMISSION_NOT_RETAINED');
      }
    }
    if (plan.applySetup) {
      await NativeBridgeModule.applyShizukuOneTimeSetup();
    }

    status = await getShizukuStatus();
    if (!isShizukuSetupVerified(status)) {
      throw setupError('SHIZUKU_GRANTS_NOT_RETAINED', pretty(status));
    }
    show(
      'Shizuku',
      `${text.setupComplete}\n\nREAD_LOGS: ${status.readLogs}\nOverlay: ${
        status.overlay
      }\nBinder: ${status.binderEvent || '—'}`,
    );
  };

  const button = (label, action, backgroundColor = '#2457a6') => (
    <TouchableOpacity
      accessibilityRole="button"
      style={[styles.button, { backgroundColor }]}
      disabled={busy}
      onPress={() => run(action)}
    >
      <Text style={styles.buttonText}>{label}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.card}>
      <Text style={styles.heading}>{text.setupTitle}</Text>
      {busy && <ActivityIndicator style={styles.busy} />}
      {button(
        text.accessibility,
        () => NativeBridgeModule.openAccessibilitySettings(),
        '#176b3a',
      )}
      {button(
        text.overlay,
        () => NativeBridgeModule.openOverlaySettings(),
        '#176b3a',
      )}
      {button(
        text.shizukuOpen,
        async () => {
          await NativeBridgeModule.openOrGetShizuku();
          show('Shizuku', text.shizukuGuide);
        },
        '#5b2785',
      )}
      {button(text.shizukuSetup, runShizuku, '#5b2785')}
      {button(
        text.adb,
        () => show('ADB', `${text.adbGuide}\n\n${ADB_COMMANDS}`, ADB_COMMANDS),
        '#48515a',
      )}
      {button(
        text.battery,
        () => notifee.openBatteryOptimizationSettings(),
        '#48515a',
      )}
      {button(
        text.power,
        () => notifee.openPowerManagerSettings(),
        '#48515a',
      )}
      {button(text.selfTest, showStatus, '#263238')}
      {button(text.autoDebug, runAutoDebug, '#8a3b12')}

      <Modal
        animationType="fade"
        transparent
        visible={dialog.visible}
        onRequestClose={() =>
          setDialog(previous => ({ ...previous, visible: false }))
        }
      >
        <View style={styles.backdrop}>
          <View style={styles.dialog}>
            <Text style={styles.dialogTitle}>{dialog.title}</Text>
            <ScrollView
              style={styles.dialogScroll}
              contentContainerStyle={styles.dialogBodyContainer}
            >
              <Text selectable style={styles.dialogBody}>
                {dialog.body}
              </Text>
            </ScrollView>
            <View style={styles.dialogActions}>
              <TouchableOpacity
                accessibilityRole="button"
                style={[styles.actionButton, styles.copyButton]}
                onPress={() => {
                  Clipboard.setString(dialog.copy);
                  setDialog(previous => ({
                    ...previous,
                    title: text.copied,
                  }));
                }}
              >
                <Text style={styles.buttonText}>{text.copy}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                accessibilityRole="button"
                style={[
                  styles.actionButton,
                  styles.closeButton,
                  styles.rightActionButton,
                ]}
                onPress={() =>
                  setDialog(previous => ({ ...previous, visible: false }))
                }
              >
                <Text style={styles.buttonText}>{text.close}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

function createStyles(isDark) {
  const palette = isDark
    ? {
        surface: '#1b1b1f',
        border: '#7a7a84',
        text: '#f5f5f7',
        scrim: 'rgba(0,0,0,0.78)',
      }
    : {
        surface: '#ffffff',
        border: '#6d7077',
        text: '#15171a',
        scrim: 'rgba(0,0,0,0.58)',
      };
  return {
    card: {
      marginTop: 18,
      padding: 14,
      borderRadius: 12,
      backgroundColor: palette.surface,
      borderWidth: 1,
      borderColor: palette.border,
    },
    heading: {
      color: palette.text,
      fontSize: 18,
      fontWeight: '700',
      marginBottom: 8,
      textAlign: 'center',
    },
    busy: { marginVertical: 8 },
    button: {
      paddingVertical: 12,
      paddingHorizontal: 10,
      borderRadius: 8,
      alignItems: 'center',
      marginVertical: 5,
    },
    buttonText: {
      color: '#ffffff',
      fontSize: 15,
      fontWeight: '600',
      textAlign: 'center',
    },
    backdrop: {
      flex: 1,
      backgroundColor: palette.scrim,
      justifyContent: 'center',
      padding: 16,
    },
    dialog: {
      maxHeight: '88%',
      borderRadius: 14,
      padding: 16,
      backgroundColor: palette.surface,
      borderWidth: 1,
      borderColor: palette.border,
    },
    dialogTitle: {
      color: palette.text,
      fontSize: 19,
      fontWeight: '700',
      marginBottom: 10,
    },
    dialogScroll: { minHeight: 120 },
    dialogBodyContainer: { paddingBottom: 8 },
    dialogBody: {
      color: palette.text,
      fontFamily: 'monospace',
      fontSize: 13,
      lineHeight: 20,
    },
    dialogActions: { flexDirection: 'row', marginTop: 12 },
    actionButton: {
      flex: 1,
      paddingVertical: 12,
      borderRadius: 8,
      alignItems: 'center',
    },
    rightActionButton: { marginLeft: 10 },
    copyButton: { backgroundColor: '#2457a6' },
    closeButton: { backgroundColor: '#5b6168' },
  };
}

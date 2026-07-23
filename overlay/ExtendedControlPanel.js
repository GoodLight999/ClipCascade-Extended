import React, { useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  PlatformColor,
  ScrollView,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Clipboard from '@react-native-clipboard/clipboard';

import { analyzeDiagnostics, formatDiagnosticsReport } from './AutoDebug';
import { getExtendedStrings } from './ExtendedI18n';

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

export default function ExtendedControlPanel({ NativeBridgeModule, notifee }) {
  const text = getExtendedStrings();
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
      show(text.setupFailed, String(error));
    } finally {
      setBusy(false);
    }
  };

  const showStatus = async () => {
    const status = JSON.parse(
      await NativeBridgeModule.getReliabilityStatus(),
    );
    const lines = [
      `Package: ${status.packageName}`,
      `Service requested: ${status.serviceRequested}`,
      `Connection: ${status.connectionStatus || '—'}`,
      `Accessibility: ${status.accessibilityEnabled}`,
      `Accessibility state: ${status.accessibilityServiceStatus || '—'}`,
      `Capture: ${status.accessibilityCaptureStatus || '—'}`,
      `Coordinator: ${status.captureCoordinator || '—'}`,
      `JS listener: ${status.jsListenerStatus || '—'}`,
      `Native delivery ready: ${status.nativeDeliveryReady}`,
      `Pending native events: ${status.pendingEvents}`,
      `Shared payload: ${status.sharedPayloadStatus || 'idle'}`,
      `Outbound queue:\n${pretty(status.outboundQueueStatus)}`,
      `Foreground service state: ${status.foregroundServiceState || '—'}`,
      `Foreground service error: ${status.foregroundServiceError || 'none'}`,
      `P2P candidates/compatible/incompatible: ${
        status.p2pCandidatePeers || 0
      }/${status.p2pCompatiblePeers || 0}/${
        status.p2pIncompatiblePeers || 0
      }`,
      `P2P last compatibility error: ${
        status.p2pLastCompatibilityError || 'none'
      }`,
      `READ_LOGS: ${status.readLogs}`,
      `Overlay: ${status.overlay}`,
      `Shizuku:\n${pretty(status.shizuku)}`,
      `Restart receiver: ${status.restartReceiverStatus || 'not observed'}`,
    ];
    show(text.selfTest, lines.join('\n'));
  };

  const runAutoDebug = async () => {
    const status = JSON.parse(
      await NativeBridgeModule.getReliabilityStatus(),
    );
    const probe = NativeBridgeModule.runNativeAutoDebug
      ? JSON.parse(await NativeBridgeModule.runNativeAutoDebug())
      : { clipboard: { clipboardRead: null }, reason: 'native probe unavailable' };
    const report = analyzeDiagnostics(status, probe);
    const body = formatDiagnosticsReport(report, text.reportTitle);
    show(text.autoDebug, body);
  };

  const runShizuku = async () => {
    try {
      await NativeBridgeModule.requestShizukuPermission();
      await NativeBridgeModule.applyShizukuOneTimeSetup();
      const status = JSON.parse(
        await NativeBridgeModule.getShizukuStatus(),
      );
      show(
        'Shizuku',
        `${text.setupComplete}\n\nREAD_LOGS: ${status.readLogs}\nOverlay: ${
          status.overlay
        }\nBinder: ${status.binderEvent || '—'}`,
      );
    } catch (error) {
      show(text.setupFailed, `${String(error)}\n\n${text.shizukuGuide}`);
    }
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

const styles = {
  card: {
    marginTop: 18,
    padding: 14,
    borderRadius: 12,
    backgroundColor: PlatformColor('?android:attr/colorBackgroundFloating'),
    borderWidth: 1,
    borderColor: PlatformColor('?android:attr/textColorSecondary'),
  },
  heading: {
    color: PlatformColor('?android:attr/textColorPrimary'),
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
    backgroundColor: 'rgba(0,0,0,0.72)',
    justifyContent: 'center',
    padding: 16,
  },
  dialog: {
    maxHeight: '88%',
    borderRadius: 14,
    padding: 16,
    backgroundColor: PlatformColor('?android:attr/colorBackgroundFloating'),
    borderWidth: 1,
    borderColor: PlatformColor('?android:attr/textColorSecondary'),
  },
  dialogTitle: {
    color: PlatformColor('?android:attr/textColorPrimary'),
    fontSize: 19,
    fontWeight: '700',
    marginBottom: 10,
  },
  dialogScroll: { minHeight: 120 },
  dialogBodyContainer: { paddingBottom: 8 },
  dialogBody: {
    color: PlatformColor('?android:attr/textColorPrimary'),
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

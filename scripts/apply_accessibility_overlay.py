#!/usr/bin/env python3
"""Apply the Accessibility + one-shot Shizuku reliability phase."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one marker, found {count}")
    return text.replace(old, new, 1)


def matching_brace(text: str, marker: str, label: str) -> tuple[int, int]:
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"{label}: marker not found")
    opening = text.find("{", start, start + len(marker) + 8)
    if opening < 0:
        raise RuntimeError(f"{label}: opening brace not found")
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return opening, index
    raise RuntimeError(f"{label}: unmatched brace")


def insert_before_block_close(text: str, marker: str, insertion: str, label: str) -> str:
    _, closing = matching_brace(text, marker, label)
    return text[:closing] + insertion + text[closing:]


def patch_gradle(root: Path) -> None:
    path = root / "android/app/build.gradle"
    text = path.read_text(encoding="utf-8")
    text = insert_before_block_close(
        text,
        "android {",
        """
    buildFeatures {
        aidl true
    }
""",
        "android build features",
    )
    text = insert_before_block_close(
        text,
        "dependencies {",
        """
    // Shizuku is used only for one-time permission setup/repair.
    implementation "dev.rikka.shizuku:api:13.1.5"
    implementation "dev.rikka.shizuku:provider:13.1.5"
""",
        "Shizuku dependencies",
    )
    path.write_text(text, encoding="utf-8")


def patch_manifest(root: Path) -> None:
    path = root / "android/app/src/main/AndroidManifest.xml"
    text = path.read_text(encoding="utf-8")
    queries = """
    <queries>
      <package android:name="moe.shizuku.privileged.api" />
    </queries>

"""
    text = replace_once(text, "    <application\n", queries + "    <application\n", "Shizuku query")
    accessibility_service = """

      <service
        android:name=".ClipCascadeAccessibilityService"
        android:enabled="true"
        android:exported="false"
        android:label="@string/clipcascade_accessibility_label"
        android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">
        <intent-filter>
          <action android:name="android.accessibilityservice.AccessibilityService" />
        </intent-filter>
        <meta-data
          android:name="android.accessibilityservice"
          android:resource="@xml/clipcascade_accessibility_service" />
      </service>
"""
    text = replace_once(
        text,
        "\n      <service\n        android:name=\".NotificationCaptureService\"",
        accessibility_service + "\n      <service\n        android:name=\".NotificationCaptureService\"",
        "Accessibility service manifest",
    )
    path.write_text(text, encoding="utf-8")


def patch_native_bridge(root: Path) -> None:
    path = root / "android/app/src/main/java/com/clipcascade/NativeBridgeModule.kt"
    text = path.read_text(encoding="utf-8")
    methods = r'''
    @ReactMethod
    fun openAccessibilitySettings(promise: Promise) {
        try {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            reactApplicationContext.startActivity(intent)
            promise.resolve(true)
        } catch (error: Exception) {
            promise.reject("SETTINGS_ERROR", "Unable to open Accessibility settings", error)
        }
    }

    @ReactMethod
    fun openOverlaySettings(promise: Promise) {
        try {
            val intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:${reactApplicationContext.packageName}")
            ).apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }
            reactApplicationContext.startActivity(intent)
            promise.resolve(true)
        } catch (error: Exception) {
            promise.reject("SETTINGS_ERROR", "Unable to open overlay settings", error)
        }
    }

    @ReactMethod
    fun getShizukuStatus(promise: Promise) {
        try {
            promise.resolve(ShizukuSetup.status(reactApplicationContext))
        } catch (error: Exception) {
            promise.reject("SHIZUKU_STATUS_ERROR", "Unable to inspect Shizuku", error)
        }
    }

    @ReactMethod
    fun requestShizukuPermission(promise: Promise) {
        ShizukuSetup.requestPermission(promise)
    }

    @ReactMethod
    fun applyShizukuOneTimeSetup(promise: Promise) {
        ShizukuSetup.apply(reactApplicationContext, promise)
    }

'''
    text = replace_once(
        text,
        "    @ReactMethod\n    fun getReliabilityStatus(promise: Promise) {",
        methods + "    @ReactMethod\n    fun getReliabilityStatus(promise: Promise) {",
        "native setup methods",
    )
    old_access = '''            val readLogs = ContextCompat.checkSelfPermission(
                reactApplicationContext,
                android.Manifest.permission.READ_LOGS
            ) == android.content.pm.PackageManager.PERMISSION_GRANTED
'''
    new_access = '''            val accessibilityComponent = ComponentName(
                reactApplicationContext,
                ClipCascadeAccessibilityService::class.java
            ).flattenToString()
            val enabledAccessibilityServices = Settings.Secure.getString(
                reactApplicationContext.contentResolver,
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            ).orEmpty()
            val accessibilityEnabled = enabledAccessibilityServices
                .split(':')
                .any { it.equals(accessibilityComponent, ignoreCase = true) }
            val readLogs = ContextCompat.checkSelfPermission(
                reactApplicationContext,
                android.Manifest.permission.READ_LOGS
            ) == android.content.pm.PackageManager.PERMISSION_GRANTED
'''
    text = replace_once(text, old_access, new_access, "accessibility status calculation")
    old_result = '''                put("notificationAccess", notificationAccess)
                put("readLogs", readLogs)
                put("overlay", overlay)
'''
    new_result = '''                put("notificationAccess", notificationAccess)
                put("accessibilityEnabled", accessibilityEnabled)
                put("accessibilityServiceStatus", bridge.getValue("accessibility_service_status").orEmpty())
                put("accessibilityCaptureStatus", bridge.getValue("accessibility_capture_status").orEmpty())
                put("captureCoordinator", ClipboardCaptureCoordinator.status(reactApplicationContext))
                put("readLogs", readLogs)
                put("overlay", overlay)
                put("shizuku", JSONObject(ShizukuSetup.status(reactApplicationContext)))
'''
    text = replace_once(text, old_result, new_result, "reliability status fields")
    path.write_text(text, encoding="utf-8")


def patch_app_js(root: Path) -> None:
    path = root / "App.js"
    text = path.read_text(encoding="utf-8")
    locale_block = r'''

const EXTENDED_SETUP_TEXT = (() => {
  const locale = Intl.DateTimeFormat().resolvedOptions().locale.toLowerCase();
  if (locale.startsWith('ja')) {
    return {
      accessibility: '1. ユーザー補助を有効化',
      overlay: '2. 他のアプリの上に表示を許可',
      shizuku: '3. Shizukuで一回だけ権限設定',
      adb: 'PCのADBで設定（次善策）',
      selfTest: '信頼性セルフテスト',
      shizukuStopped: 'Shizukuを一度だけ起動してから、このボタンを押してください。設定後はShizukuを停止して構いません。',
      setupComplete: '権限設定が完了しました。Shizukuの常時起動は不要です。',
      setupFailed: '設定に失敗しました',
      adbGuide: 'PCで次の2コマンドを一度だけ実行してください。\n\nadb shell pm grant com.clipcascade.extended android.permission.READ_LOGS\nadb shell appops set com.clipcascade.extended android:system_alert_window allow',
    };
  }
  if (locale.startsWith('zh')) {
    return {
      accessibility: '1. 启用无障碍服务',
      overlay: '2. 允许显示在其他应用上层',
      shizuku: '3. 使用 Shizuku 一次性授权',
      adb: '使用电脑 ADB 设置（备用）',
      selfTest: '可靠性自检',
      shizukuStopped: '请仅启动一次 Shizuku，然后返回并再次点击。设置完成后无需保持 Shizuku 运行。',
      setupComplete: '权限设置完成。无需让 Shizuku 常驻运行。',
      setupFailed: '设置失败',
      adbGuide: '请在电脑上仅执行一次以下命令：\n\nadb shell pm grant com.clipcascade.extended android.permission.READ_LOGS\nadb shell appops set com.clipcascade.extended android:system_alert_window allow',
    };
  }
  return {
    accessibility: '1. Enable Accessibility Service',
    overlay: '2. Allow display over other apps',
    shizuku: '3. One-time Shizuku permission setup',
    adb: 'PC ADB setup (second choice)',
    selfTest: 'Reliability Self-Test',
    shizukuStopped: 'Start Shizuku once, return here, and tap again. Shizuku does not need to stay running after setup.',
    setupComplete: 'Permission setup completed. Shizuku does not need to stay running.',
    setupFailed: 'Setup failed',
    adbGuide: 'Run these commands once from a PC:\n\nadb shell pm grant com.clipcascade.extended android.permission.READ_LOGS\nadb shell appops set com.clipcascade.extended android:system_alert_window allow',
  };
})();
'''
    text = replace_once(
        text,
        "const APP_VERSION = '3.2.0-extended.1';",
        "const APP_VERSION = '3.2.0-extended.1';" + locale_block,
        "setup localization",
    )
    old_buttons = '''              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: 'black' }]}
                onPress={async () => {
                  try {
                    await NativeBridgeModule.openNotificationListenerSettings();
                  } catch (error) {
                    Alert.alert('Error', String(error));
                  }
                }}
              >
                <Text style={styles.loginButtonText}>
                  Notification Access (OTP Sync)
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: '#263238' }]}
                onPress={async () => {
                  try {
                    const status = JSON.parse(
                      await NativeBridgeModule.getReliabilityStatus(),
                    );
                    Alert.alert(
                      'Reliability Self-Test',
                      [
                        `Package: ${status.packageName}`,
                        `Service requested: ${status.serviceRequested}`,
                        `Connection: ${status.connectionStatus || 'not connected'}`,
                        `Notification access: ${status.notificationAccess}`,
                        `READ_LOGS fallback: ${status.readLogs}`,
                        `Overlay fallback: ${status.overlay}`,
                        `Pending native events: ${status.pendingEvents}`,
                        `Clipboard fallback: ${status.clipboardFallbackStatus || 'idle'}`,
                        `OTP capture: ${status.notificationCaptureStatus || 'idle'}`,
                      ].join('\\n'),
                    );
                  } catch (error) {
                    Alert.alert('Self-test failed', String(error));
                  }
                }}
              >
                <Text style={styles.loginButtonText}>
                  Reliability Self-Test
                </Text>
              </TouchableOpacity>
'''
    new_buttons = '''              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: '#1b5e20' }]}
                onPress={async () =>
                  await NativeBridgeModule.openAccessibilitySettings()
                }
              >
                <Text style={styles.loginButtonText}>
                  {EXTENDED_SETUP_TEXT.accessibility}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: '#1b5e20' }]}
                onPress={async () => await NativeBridgeModule.openOverlaySettings()}
              >
                <Text style={styles.loginButtonText}>
                  {EXTENDED_SETUP_TEXT.overlay}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: '#4a148c' }]}
                onPress={async () => {
                  try {
                    let status = JSON.parse(
                      await NativeBridgeModule.getShizukuStatus(),
                    );
                    if (!status.running) {
                      Alert.alert('Shizuku', EXTENDED_SETUP_TEXT.shizukuStopped);
                      return;
                    }
                    if (!status.permissionGranted) {
                      await NativeBridgeModule.requestShizukuPermission();
                    }
                    await NativeBridgeModule.applyShizukuOneTimeSetup();
                    status = JSON.parse(
                      await NativeBridgeModule.getShizukuStatus(),
                    );
                    Alert.alert(
                      'Shizuku',
                      `${EXTENDED_SETUP_TEXT.setupComplete}\nREAD_LOGS: ${status.readLogs}\nOverlay: ${status.overlay}`,
                    );
                  } catch (error) {
                    Alert.alert(
                      EXTENDED_SETUP_TEXT.setupFailed,
                      String(error),
                    );
                  }
                }}
              >
                <Text style={styles.loginButtonText}>
                  {EXTENDED_SETUP_TEXT.shizuku}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: '#37474f' }]}
                onPress={() => Alert.alert('ADB', EXTENDED_SETUP_TEXT.adbGuide)}
              >
                <Text style={styles.loginButtonText}>
                  {EXTENDED_SETUP_TEXT.adb}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: '#263238' }]}
                onPress={async () => {
                  try {
                    const status = JSON.parse(
                      await NativeBridgeModule.getReliabilityStatus(),
                    );
                    Alert.alert(
                      EXTENDED_SETUP_TEXT.selfTest,
                      [
                        `Package: ${status.packageName}`,
                        `Service requested: ${status.serviceRequested}`,
                        `Connection: ${status.connectionStatus || 'not connected'}`,
                        `Accessibility: ${status.accessibilityEnabled}`,
                        `Accessibility state: ${status.accessibilityServiceStatus || 'idle'}`,
                        `Capture: ${status.accessibilityCaptureStatus || 'idle'}`,
                        `Coordinator: ${status.captureCoordinator}`,
                        `READ_LOGS: ${status.readLogs}`,
                        `Overlay: ${status.overlay}`,
                        `Shizuku running (not required after setup): ${status.shizuku.running}`,
                        `Pending native events: ${status.pendingEvents}`,
                        `Clipboard fallback: ${status.clipboardFallbackStatus || 'idle'}`,
                      ].join('\\n'),
                    );
                  } catch (error) {
                    Alert.alert('Self-test failed', String(error));
                  }
                }}
              >
                <Text style={styles.loginButtonText}>
                  {EXTENDED_SETUP_TEXT.selfTest}
                </Text>
              </TouchableOpacity>
'''
    text = replace_once(text, old_buttons, new_buttons, "replace deferred OTP setup UI")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    root = args.destination.resolve()
    patch_gradle(root)
    patch_manifest(root)
    patch_native_bridge(root)
    patch_app_js(root)


if __name__ == "__main__":
    main()

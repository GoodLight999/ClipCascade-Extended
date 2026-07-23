#!/usr/bin/env python3
"""Remove the deferred OTP experiment from the core generated Android app."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def remove_method(path: Path, marker: str, next_marker: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"{label}: method marker not found")
    end = text.find(next_marker, start + len(marker))
    if end < 0:
        raise RuntimeError(f"{label}: following marker not found")
    path.write_text(text[:start] + text[end:], encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()

    manifest = root / "android/app/src/main/AndroidManifest.xml"
    otp_service = '''
      <service
        android:name=".NotificationCaptureService"
        android:exported="true"
        android:label="ClipCascade OTP capture"
        android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">
        <intent-filter>
          <action android:name="android.service.notification.NotificationListenerService" />
        </intent-filter>
      </service>
'''
    replace_once(manifest, otp_service, "", "deferred OTP manifest service")

    native_bridge = root / "android/app/src/main/java/com/clipcascade/NativeBridgeModule.kt"
    remove_method(
        native_bridge,
        '''    @ReactMethod
    fun openNotificationListenerSettings(promise: Promise) {''',
        '''    @ReactMethod
    fun getReliabilityStatus(promise: Promise) {''',
        "deferred OTP settings method",
    )
    notification_status = '''            val component = ComponentName(
                reactApplicationContext,
                NotificationCaptureService::class.java
            ).flattenToString()
            val enabledListeners = Settings.Secure.getString(
                reactApplicationContext.contentResolver,
                "enabled_notification_listeners"
            ).orEmpty()
            val notificationAccess = enabledListeners
                .split(':')
                .any { it.equals(component, ignoreCase = true) }
'''
    replace_once(
        native_bridge,
        notification_status,
        "",
        "deferred OTP notification-access calculation",
    )
    replace_once(
        native_bridge,
        '''                put("notificationAccess", notificationAccess)
''',
        "",
        "deferred OTP self-test field",
    )
    replace_once(
        native_bridge,
        '''                put("notificationCaptureStatus", bridge.getValue("notification_capture_status").orEmpty())
''',
        "",
        "deferred OTP capture status field",
    )

    for relative in (
        "android/app/src/main/java/com/clipcascade/NotificationCaptureService.kt",
        "android/app/src/main/java/com/clipcascade/OtpExtractor.kt",
        "android/app/src/test/java/com/clipcascade/OtpExtractorTest.kt",
    ):
        path = root / relative
        if not path.is_file():
            raise RuntimeError(f"Deferred OTP source missing before removal: {path}")
        path.unlink()

    app_js = root / "App.js"
    app_text = app_js.read_text(encoding="utf-8")
    for forbidden in (
        "Notification Access (OTP Sync)",
        "notificationAccess",
        "notificationCaptureStatus",
        "OTP capture",
    ):
        if forbidden in app_text:
            raise RuntimeError(f"Deferred OTP UI remained after Accessibility phase: {forbidden}")

    print("Removed deferred OTP experiment from core generated app")


if __name__ == "__main__":
    main()

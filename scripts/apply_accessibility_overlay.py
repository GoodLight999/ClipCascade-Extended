#!/usr/bin/env python3
"""Apply the Accessibility and one-time Shizuku reliability layer.

This phase adds only final runtime capabilities. It does not create temporary UI
or deferred OTP components for later removal.
"""
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
    text = replace_once(
        text,
        "    <application\n",
        queries + "    <application\n",
        "Shizuku package query",
    )
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
        "    </application>",
        accessibility_service + "    </application>",
        "Accessibility service manifest",
    )
    path.write_text(text, encoding="utf-8")


def patch_native_bridge(root: Path) -> None:
    path = root / "android/app/src/main/java/com/clipcascade/NativeBridgeModule.kt"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import android.content.Intent\n",
        "import android.content.ComponentName\nimport android.content.Intent\nimport android.net.Uri\n",
        "Accessibility native imports",
    )

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

    old_result = '''                put("readLogs", readLogs)
                put("overlay", overlay)
'''
    new_result = '''                put("accessibilityEnabled", accessibilityEnabled)
                put("accessibilityServiceStatus", bridge.getValue("accessibility_service_status").orEmpty())
                put("accessibilityCaptureStatus", bridge.getValue("accessibility_capture_status").orEmpty())
                put("captureCoordinator", ClipboardCaptureCoordinator.status(reactApplicationContext))
                put("readLogs", readLogs)
                put("overlay", overlay)
                put("shizuku", JSONObject(ShizukuSetup.status(reactApplicationContext)))
'''
    text = replace_once(text, old_result, new_result, "reliability status fields")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    patch_gradle(root)
    patch_manifest(root)
    patch_native_bridge(root)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Apply the deterministic ClipCascade Extended base overlay.

The input must be a fresh copy of the pinned upstream mobile source. This phase
only establishes the final package/version/signing identity, copies canonical
Extended source files, and adds the minimal native reliability-status bridge.
It must never introduce deferred features that a later phase has to delete.
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "overlay"
VERSION_CODE = "320004"
VERSION_NAME = "3.2.0-extended.4"
APPLICATION_ID = "com.clipcascade.extended"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one marker, found {count}")
    return text.replace(old, new, 1)


def matching_brace(text: str, marker: str, label: str) -> tuple[int, int]:
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"{label}: block marker not found: {marker!r}")
    opening = text.find("{", start, start + len(marker) + 4)
    if opening < 0:
        raise RuntimeError(f"{label}: opening brace not found")
    depth = 0
    for index in range(opening, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return opening, index
    raise RuntimeError(f"{label}: unmatched brace")


def insert_before_block_close(text: str, marker: str, insertion: str, label: str) -> str:
    _, closing = matching_brace(text, marker, label)
    return text[:closing] + insertion + text[closing:]


def copy_overlay(destination: Path) -> None:
    if not OVERLAY.is_dir():
        raise RuntimeError(f"Overlay directory is missing: {OVERLAY}")
    for source in sorted(OVERLAY.rglob("*")):
        if source.is_dir():
            continue
        relative = source.relative_to(OVERLAY)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def patch_app_gradle(destination: Path) -> None:
    path = destination / "android/app/build.gradle"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'applicationId "com.clipcascade"',
        f'applicationId "{APPLICATION_ID}"',
        "application id",
    )
    text = replace_once(text, "versionCode 1", f"versionCode {VERSION_CODE}", "version code")
    text = replace_once(
        text,
        'versionName "1.0"',
        f'versionName "{VERSION_NAME}"',
        "version name",
    )

    signing = """
        // Repository-pinned sideload key. It exists solely to keep update
        // signatures stable across CI builds; it is not a trust secret.
        extended {
            storeFile file("clipcascade-extended.keystore")
            storePassword "clipcascade-extended"
            keyAlias "clipcascade-extended"
            keyPassword "clipcascade-extended"
        }
"""
    text = insert_before_block_close(text, "    signingConfigs {", signing, "signing configs")

    build_type = """
        extended {
            initWith release
            matchingFallbacks = ["release"]
            signingConfig signingConfigs.extended
            debuggable false
            minifyEnabled false
        }
"""
    text = insert_before_block_close(text, "    buildTypes {", build_type, "build types")
    text = insert_before_block_close(
        text,
        "dependencies {",
        '\n    testImplementation "junit:junit:4.13.2"\n',
        "test dependency",
    )
    path.write_text(text, encoding="utf-8")


def patch_manifest(destination: Path) -> None:
    path = destination / "android/app/src/main/AndroidManifest.xml"
    text = path.read_text(encoding="utf-8")
    old_activity = """      <activity
        android:name=".ClipboardFloatingActivity"
        android:theme="@style/Theme.TransparentActivity" />"""
    new_activity = """      <activity
        android:name=".ClipboardFloatingActivity"
        android:excludeFromRecents="true"
        android:exported="false"
        android:noHistory="true"
        android:theme="@style/Theme.TransparentActivity" />"""
    path.write_text(
        replace_once(text, old_activity, new_activity, "floating activity manifest"),
        encoding="utf-8",
    )


def patch_native_bridge(destination: Path) -> None:
    path = destination / "android/app/src/main/java/com/clipcascade/NativeBridgeModule.kt"
    text = path.read_text(encoding="utf-8")
    imports = """import android.content.Intent
import android.provider.Settings
import androidx.core.content.ContextCompat
import org.json.JSONObject
"""
    text = replace_once(
        text,
        "import android.content.Context\n",
        "import android.content.Context\n" + imports,
        "native bridge imports",
    )

    methods = r'''
    @ReactMethod
    fun getReliabilityStatus(promise: Promise) {
        try {
            val readLogs = ContextCompat.checkSelfPermission(
                reactApplicationContext,
                android.Manifest.permission.READ_LOGS
            ) == android.content.pm.PackageManager.PERMISSION_GRANTED
            val overlay = Settings.canDrawOverlays(reactApplicationContext)
            val bridge = AsyncStorageBridge(reactApplicationContext)
            val result = JSONObject().apply {
                put("packageName", reactApplicationContext.packageName)
                put("readLogs", readLogs)
                put("overlay", overlay)
                put("serviceRequested", bridge.getValue("wsIsRunning") == "true")
                put("connectionStatus", bridge.getValue("wsStatusMessage").orEmpty())
                put("clipboardFallbackStatus", bridge.getValue("clipboard_fallback_status").orEmpty())
                put("pendingEvents", PendingReactEventStore.pendingCount(reactApplicationContext))
            }
            promise.resolve(result.toString())
        } catch (error: Exception) {
            promise.reject("STATUS_ERROR", "Unable to inspect reliability status", error)
        }
    }

'''
    marker = "    /**\n     * JS calls this synchronously"
    text = replace_once(text, marker, methods + marker, "native diagnostics insertion")
    path.write_text(text, encoding="utf-8")


def patch_app_js(destination: Path) -> None:
    path = destination / "App.js"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "const APP_VERSION = '3.2.0';",
        f"const APP_VERSION = '{VERSION_NAME}';",
        "app version",
    )
    text = replace_once(
        text,
        "const APP_NAME = 'ClipCascade';",
        "const APP_NAME = 'ClipCascade Extended';",
        "app name",
    )
    text = text.replace("com.clipcascade", APPLICATION_ID)
    path.write_text(text, encoding="utf-8")


def patch_strings(destination: Path) -> None:
    path = destination / "android/app/src/main/res/values/strings.xml"
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'(<string\s+name="app_name"\s*>)(.*?)(</string>)',
        r"\1ClipCascade Extended\3",
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError("app name resource: expected exactly one app_name string")
    path.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    destination = parser.parse_args().destination.resolve()
    if not (destination / "android/app/build.gradle").is_file():
        raise RuntimeError(f"Not an upstream mobile source tree: {destination}")

    copy_overlay(destination)
    patch_app_gradle(destination)
    patch_manifest(destination)
    patch_native_bridge(destination)
    patch_app_js(destination)
    patch_strings(destination)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Add the native Shizuku open/install action.

The user-facing setup UI is canonical in overlay/ExtendedControlPanel.js; this
phase only adds the upstream NativeBridge method required by that UI.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()

    native = root / "android/app/src/main/java/com/clipcascade/NativeBridgeModule.kt"
    replace_once(
        native,
        '''    @ReactMethod
    fun getShizukuStatus(promise: Promise) {''',
        '''    @ReactMethod
    fun openOrGetShizuku(promise: Promise) {
        try {
            val packageName = "moe.shizuku.privileged.api"
            val launchIntent = reactApplicationContext.packageManager
                .getLaunchIntentForPackage(packageName)
            val intent = launchIntent ?: Intent(
                Intent.ACTION_VIEW,
                Uri.parse("https://github.com/thedjchi/Shizuku/releases")
            )
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            reactApplicationContext.startActivity(intent)
            promise.resolve(launchIntent != null)
        } catch (error: Exception) {
            promise.reject("SHIZUKU_OPEN_ERROR", "Unable to open or locate Shizuku", error)
        }
    }

    @ReactMethod
    fun getShizukuStatus(promise: Promise) {''',
        "Shizuku open/install native method",
    )


if __name__ == "__main__":
    main()

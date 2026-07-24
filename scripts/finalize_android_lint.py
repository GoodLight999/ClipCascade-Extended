#!/usr/bin/env python3
"""Resolve verified Android lint findings with narrow guarded edits."""
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
    manifest = root / "android/app/src/main/AndroidManifest.xml"
    strings = root / "android/app/src/main/res/values/strings.xml"

    # Notifee documents this exact service class. React Native autolinking supplies
    # it at package time, but Android Lint cannot resolve it in this generated tree.
    replace_once(
        manifest,
        '''        tools:replace="android:foregroundServiceType"/>''',
        '''        tools:replace="android:foregroundServiceType"
        tools:ignore="MissingClass"/>''',
        "Notifee autolink lint suppression",
    )
    replace_once(
        strings,
        '''<string name="app_name">ClipCascade Extended</string>''',
        '''<string name="app_name" translatable="false">ClipCascade Extended</string>''',
        "non-translatable product name",
    )
    replace_once(
        manifest,
        '''    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />''',
        '''    <uses-permission
      android:name="android.permission.READ_EXTERNAL_STORAGE"
      android:maxSdkVersion="32" />''',
        "legacy read storage API bound",
    )
    replace_once(
        manifest,
        '''    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />''',
        '''    <uses-permission
      android:name="android.permission.WRITE_EXTERNAL_STORAGE"
      android:maxSdkVersion="28" />''',
        "legacy write storage API bound",
    )


if __name__ == "__main__":
    main()

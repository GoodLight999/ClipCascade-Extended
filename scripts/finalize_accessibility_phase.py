#!/usr/bin/env python3
"""Finalize phase-specific versioning after guarded overlays are applied."""
from pathlib import Path
import argparse


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"{path}: expected one {old!r}, found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    replace_once(root / "android/app/build.gradle", "versionCode 320001", "versionCode 320004")
    replace_once(
        root / "android/app/build.gradle",
        'versionName "3.2.0-extended.1"',
        'versionName "3.2.0-extended.4"',
    )
    replace_once(
        root / "App.js",
        "const APP_VERSION = '3.2.0-extended.1';",
        "const APP_VERSION = '3.2.0-extended.4';",
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Reject regressions in text/image/file Android Share handling."""
from __future__ import annotations

import argparse
from pathlib import Path


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f"missing {label}: {needle!r}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise RuntimeError(f"forbidden {label}: {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root.resolve()
    android = root / "android/app/src/main"
    activity = (android / "java/com/clipcascade/MainActivity.kt").read_text(encoding="utf-8")

    require(activity, "getCharSequenceExtra(Intent.EXTRA_TEXT)", "CharSequence text share")
    require(activity, "getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)", "PROCESS_TEXT share")
    require(activity, "Intent.ACTION_SEND_MULTIPLE", "multiple-file share")
    require(activity, "intent.type?.startsWith(\"image/\")", "image share classification")
    require(activity, 'stageAndDispatch(listOf(stream), "SHARED_IMAGE", "image")', "image staging")
    require(activity, 'stageAndDispatch(uris, "SHARED_FILES", "files")', "multi-file staging")
    require(activity, 'setValue("shared_payload_pending", "false")', "pending-state cleanup")
    require(activity, '"unsupported-share:', "unsupported-share evidence")
    require(activity, "R.string.clipcascade_share_prepare_failed", "localized share failure")
    require(
        activity,
        "(applicationContext as MainApplication).reactNativeHost.reactInstanceManager",
        "Application-owned React host",
    )
    require(
        activity,
        "applicationReactInstanceManager()?.currentReactContext",
        "nullable React Context dispatch",
    )
    require(
        activity,
        "PendingReactEventStore.emitOrQueue",
        "durable share event fallback",
    )
    forbid(activity, 'intent.type == "text/plain"', "text/plain-only share restriction")
    forbid(activity, "getStringExtra(Intent.EXTRA_TEXT)", "String-only text share")
    forbid(activity, "reactInstanceManager.currentReactContext", "Activity delegate React host race")
    forbid(activity, '"ClipCascade Extended could not prepare the shared file."', "hard-coded English Toast")

    for directory in ("values", "values-ja", "values-zh-rCN"):
        strings = (android / f"res/{directory}/clipcascade_extended_strings.xml").read_text(
            encoding="utf-8"
        )
        require(
            strings,
            'name="clipcascade_share_prepare_failed"',
            f"localized share failure in {directory}",
        )

    print("Android Share intent coverage and localization: OK")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate final generated scope after all reliability finalizers."""
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
    android_main = root / "android/app/src/main"
    java_root = android_main / "java/com/clipcascade"
    test_root = root / "android/app/src/test/java/com/clipcascade"

    manifest = (android_main / "AndroidManifest.xml").read_text(encoding="utf-8")
    native_bridge = (java_root / "NativeBridgeModule.kt").read_text(encoding="utf-8")
    foreground = (root / "StartForegroundService.js").read_text(encoding="utf-8")
    app = (root / "App.js").read_text(encoding="utf-8")
    sync_cache = (java_root / "SyncRequestCache.kt").read_text(encoding="utf-8")
    shizuku = (java_root / "ShizukuSetup.kt").read_text(encoding="utf-8")

    for path in (
        java_root / "NotificationCaptureService.kt",
        java_root / "OtpExtractor.kt",
        test_root / "OtpExtractorTest.kt",
    ):
        if path.exists():
            raise RuntimeError(f"Deferred OTP file remained in generated app: {path}")

    for text, label in ((manifest, "manifest"), (native_bridge, "NativeBridge"), (app, "App")):
        forbid(text, "NotificationCaptureService", f"deferred OTP in {label}")
        forbid(text, "notificationAccess", f"deferred OTP access in {label}")
        forbid(text, "notificationCaptureStatus", f"deferred OTP status in {label}")
    forbid(manifest, "BIND_NOTIFICATION_LISTENER_SERVICE", "notification-listener binding")
    forbid(app, "OTP capture", "OTP self-test UI")

    require(sync_cache, "previous == null || now < previous", "first/rollback cache refresh")
    require(sync_cache, "lastCheckAt = null", "cache invalidation")
    require(shizuku, "activeConnection !== connection", "stale Shizuku connection guard")
    require(shizuku, "waitForVerification(app, connection)", "cancel-aware Shizuku verification")
    require(native_bridge, "fun openOrGetShizuku", "Shizuku open/install action")
    require(native_bridge, "thedjchi/Shizuku/releases", "recommended Shizuku fork fallback")
    require(app, "shizukuOpen", "localized Shizuku open button")
    require(app, "shizukuGuide", "localized Shizuku guidance")
    require(foreground, "p2s-late-echo-acknowledged", "late P2S ACK recovery")
    require(foreground, "queuedForAck?.id === echoedDeliveryId", "late P2S queue identity guard")

    print("final generated scope and deferred-feature boundaries: OK")


if __name__ == "__main__":
    main()

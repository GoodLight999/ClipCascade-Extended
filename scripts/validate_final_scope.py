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


def require_before(text: str, first: str, second: str, label: str) -> None:
    left = text.find(first)
    right = text.find(second)
    if left < 0 or right < 0 or left >= right:
        raise RuntimeError(f"invalid ordering for {label}")


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
    control_panel = (root / "ExtendedControlPanel.js").read_text(encoding="utf-8")
    i18n = (root / "ExtendedI18n.js").read_text(encoding="utf-8")
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
    require(shizuku, "addBinderReceivedListenerSticky", "sticky Shizuku Binder listener")
    require(shizuku, "awaitBinder(BINDER_TIMEOUT_MS)", "bounded Shizuku Binder wait")
    require(native_bridge, "fun openOrGetShizuku", "Shizuku open/install action")
    require(native_bridge, "thedjchi/Shizuku/releases", "recommended Shizuku fork fallback")
    require(native_bridge, "fun runNativeAutoDebug", "native one-tap diagnostics")
    require(control_panel, "text.shizukuOpen", "localized Shizuku open button")
    require(control_panel, "text.shizukuGuide", "localized Shizuku guidance")
    require(control_panel, "Clipboard.setString(dialog.copy)", "copyable reports and ADB commands")
    require(i18n, "ja:", "Japanese product dictionary")
    require(i18n, "zh:", "Chinese product dictionary")
    require(i18n, "en:", "English product dictionary")
    # The detailed listener-ownership invariants live in
    # validate_service_and_p2p_controls.py. This final-scope check preserves only
    # the cross-phase ordering contract using the same canonical marker.
    require_before(
        foreground,
        "const clipboardOnChange = trackClipboardSubscription(clipboardListener.addListener(",
        "await ClipboardListener.startListening();",
        "owned native drain after JS callback registration",
    )
    require(foreground, "p2s-late-echo-acknowledged", "late P2S ACK recovery")
    require(foreground, "queuedForAck?.id === echoedDeliveryId", "late P2S queue identity guard")
    require(foreground, "quarantinedPeers", "P2P incompatible peer isolation")
    require(foreground, "foreground_service_error", "foreground-service error persistence")
    require(foreground, "shared_payload_pending", "share auto-start state")

    for inherited in (
        "New version available!",
        "GITHUB",
        "DONATE",
        "HOMEPAGE",
        "adb -d shell am force-stop",
    ):
        forbid(app, inherited, f"inherited upstream UI {inherited}")

    print("final generated scope and deferred-feature boundaries: OK")


if __name__ == "__main__":
    main()

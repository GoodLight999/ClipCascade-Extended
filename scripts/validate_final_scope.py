#!/usr/bin/env python3
"""Validate final generated scope after all reliability phases."""
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
    shizuku_policy = (root / "ShizukuSetupPolicy.js").read_text(encoding="utf-8")
    pending_share_policy = (root / "PendingShareStartPolicy.js").read_text(encoding="utf-8")
    service_policy = (root / "ServiceControlPolicy.js").read_text(encoding="utf-8")
    inbound_policy = (root / "InboundErrorPolicy.js").read_text(encoding="utf-8")
    receipt_policy = (root / "P2SReceiptTracker.js").read_text(encoding="utf-8")
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
    require(shizuku, "addBinderReceivedListenerSticky", "sticky Shizuku listener")
    require(shizuku, "awaitBinder(BINDER_TIMEOUT_MS)", "bounded Shizuku wait")
    require(native_bridge, "fun openOrGetShizuku", "Shizuku open/install action")
    require(native_bridge, "thedjchi/Shizuku/releases", "recommended fork fallback")
    require(native_bridge, "fun runNativeAutoDebug", "native one-tap diagnostics")
    require(control_panel, "text.shizukuOpen", "localized Shizuku open button")
    require(control_panel, "text.shizukuGuide", "localized Shizuku guidance")
    require(control_panel, "Clipboard.setString(dialog.copy)", "copyable reports and commands")
    require(control_panel, "createStyles(useColorScheme() === 'dark')", "readable theme")
    require(shizuku_policy, "state: 'already-configured'", "retained-grant state")
    require(shizuku_policy, "state: 'binder-pending'", "bounded startup state")
    require(shizuku_policy, "state: 'permission-required'", "permission state")
    for locale in ("ja:", "zh:", "en:"):
        require(i18n, locale, f"product dictionary {locale}")

    require(app, "import { planPendingShareStart }", "pending-share policy import")
    require(app, "sessionReadyRef.current = enableWSPage;", "session-derived readiness")
    require_before(
        app,
        "const [enableWSPage, setEnableWSPage] = useState(false);",
        "sessionReadyRef.current = enableWSPage;",
        "state declaration before synchronization",
    )
    for marker, label in (
        ("shared_payload_pending", "pending-share polling"),
        ("foreground_service_heartbeat_at", "heartbeat polling"),
        ("pendingShareStartInFlightRef", "share-start concurrency guard"),
        ("pendingShareLastAttemptAtRef", "share-start throttle"),
        ("service-start-requested:", "share-triggered start evidence"),
        ("pendingSharePlan.forceRestart", "stale restart propagation"),
        ("work-manager-recovery", "explicit WorkManager recovery"),
    ):
        require(app, marker, label)
    for marker, label in (
        ("FOREGROUND_HEARTBEAT_STALE_MS = 15_000", "heartbeat freshness"),
        ("elapsed >= 0 && elapsed <= Number(maxAgeMs)", "rollback-safe freshness"),
        ("forceRestart ? 'stale-runtime' : 'runtime-stopped'", "stale classification"),
    ):
        require(pending_share_policy, marker, label)
    require(service_policy, "forceRestart = false", "forced restart input")
    require(service_policy, "forcedStart", "forced restart result")

    require_before(
        foreground,
        "const clipboardOnChange = trackClipboardSubscription(clipboardListener.addListener(",
        "await ClipboardListener.startListening();",
        "owned callback registration before native drain",
    )

    # Final P2S contract: standard receipt plus identity-checked loopback fallback.
    for marker, label in (
        ("createP2SReceiptTracker", "receipt tracker integration"),
        ("headers: {receipt: receiptId}", "standard STOMP receipt"),
        ("stompClient.watchForReceipt(receiptId", "receipt callback"),
        ("p2sEchoGuard.consume(type_, hcb", "loopback fallback"),
        ("shouldAcknowledgeP2SDelivery", "late callback identity guard"),
        ("p2s-late-${source}-acknowledged", "late receipt/echo evidence"),
        ("queued?.id || null", "queue-head identity input"),
        ("p2s-receipt-timeout", "non-destructive timeout evidence"),
        ("p2sReceiptTracker.cancel();\n                p2sEchoGuard.clear();\n                return OUTBOUND_DELIVERY.WAITING;", "publish-time stop guard"),
        ("createInboundErrorCoalescer", "inbound error coalescing"),
        ("p2s_last_inbound_error_count", "P2S incident counter"),
    ):
        require(foreground, marker, label)
    require(receipt_policy, "String(queuedHeadId || '') === id", "late ACK queue-head guard")
    require(inbound_policy, "code: 'encryption-mismatch'", "decrypt classification")
    require(inbound_policy, "shouldReport: false", "duplicate inbound suppression")

    for marker, label in (
        ("quarantinedPeers", "P2P incompatible peer isolation"),
        ("foreground_service_error", "foreground error persistence"),
        ("shared_payload_pending", "share completion state"),
        ("foregroundRuntimeCoordinator.runStartTransition", "serialized service starts"),
        ("foregroundRuntimeCoordinator.waitForActiveRuntime", "live runtime confirmation"),
        ("handler-confirmed:", "runtime confirmation evidence"),
    ):
        require(foreground, marker, label)

    for forbidden, label in (
        ("Encryption must be enabled on all devices if enabled", "room-wide encryption wording"),
        ("extendedDeliveryId", "proprietary P2S payload metadata"),
        ("previous_clipboard_content_hash", "global feedback suppression"),
        ("block_image_once", "untyped feedback flag"),
    ):
        forbid(foreground, forbidden, label)

    for inherited in (
        "New version available!",
        "GITHUB",
        "DONATE",
        "HOMEPAGE",
        "adb -d shell am force-stop",
    ):
        forbid(app, inherited, f"inherited upstream UI {inherited}")

    print("final generated scope, receipt identity and deferred-feature boundaries: OK")


if __name__ == "__main__":
    main()

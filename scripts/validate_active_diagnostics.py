#!/usr/bin/env python3
"""Require active, localized, non-secret automatic diagnostics."""
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
    android = root / "android/app/src/main/java/com/clipcascade"
    native_bridge = (android / "NativeBridgeModule.kt").read_text(encoding="utf-8")
    native_debug = (android / "ReliabilityAutoDebug.kt").read_text(encoding="utf-8")
    recovery = (android / "ForegroundRuntimeRecovery.kt").read_text(encoding="utf-8")
    floating_activity = (android / "ClipboardFloatingActivity.kt").read_text(encoding="utf-8")
    foreground = (root / "StartForegroundService.js").read_text(encoding="utf-8")
    coordinator = (root / "ForegroundRuntimeCoordinator.js").read_text(encoding="utf-8")
    headless = (root / "HeadlessTask.js").read_text(encoding="utf-8")
    panel = (root / "ExtendedControlPanel.js").read_text(encoding="utf-8")
    analyzer = (root / "AutoDebug.js").read_text(encoding="utf-8")
    i18n = (root / "ExtendedI18n.js").read_text(encoding="utf-8")

    for marker, label in (
        ("fun runEventBridgeProbe", "native event bridge probe"),
        ("onExtendedDiagnosticProbe", "diagnostic event name"),
        ("DeviceEventManagerModule.RCTDeviceEventEmitter", "React event emitter"),
    ):
        require(native_bridge, marker, label)
    for marker, label in (
        ("runEventBridgeProbe", "one-tap active event test"),
        ("new NativeEventEmitter(NativeBridgeModule)", "active event listener"),
        ("probe.eventBridge = eventBridge", "active event result"),
        ("formatDiagnosticsReport(report, text)", "localized report dictionary"),
        ("foregroundServiceRecoveryStatus", "recovery state"),
        ("p2sLastInboundErrorCode", "P2S incident"),
        ("Clipboard.setString(dialog.copy)", "one-tap report copy"),
    ):
        require(panel, marker, label)
    for marker, label in (
        ("native-react-event-bridge", "event verdict"),
        ("heartbeatAgeMs", "heartbeat verdict"),
        ("foregroundServiceDetachedError", "detached callback verdict"),
        ("foreground-runtime-singleton", "runtime singleton verdict"),
        ("foreground-recovery", "recovery verdict"),
        ("p2sInboundCount", "P2S incident verdict"),
        ("CHECK_LABEL_KEYS", "localized check mapping"),
        ("diagnosticsRawStatus", "raw status heading"),
        ("diagnosticsNativeProbe", "native probe heading"),
    ):
        require(analyzer, marker, label)
    for key in (
        "diagnosticsOverall",
        "diagnosticsGenerated",
        "diagnosticsRawStatus",
        "diagnosticsNativeProbe",
        "diagnosticNativeReact",
        "diagnosticForeground",
        "diagnosticRecovery",
        "diagnosticSharedPayload",
        "diagnosticP2P",
    ):
        require(i18n, f"{key}:", f"localized diagnostic key {key}")

    for marker, label in (
        ("foreground_service_heartbeat_at", "foreground heartbeat"),
        ("foreground_service_detached_error", "detached failure evidence"),
        ("foregroundRuntimeCoordinator.acquire", "coordinated lease"),
        ("foregroundRuntimeCoordinator.runStartTransition", "serialized start"),
        ("foregroundRuntimeCoordinator.requestRestart", "restart wait"),
        ("foregroundRuntimeCoordinator.waitForActiveRuntime", "live callback confirmation"),
        ("`restart-waiting:${restartReason}`", "restart waiting evidence"),
        ("restart-stop-requested:", "old runtime stop evidence"),
        ("restart-old-runtime-stopped:", "old runtime completion evidence"),
        ("handler-confirmed:", "new runtime confirmation evidence"),
        ("duplicate-runtime-suppressed", "duplicate suppression"),
        ("finishForegroundRuntime", "lease release"),
        ("p2s_last_inbound_error_count", "P2S incident count"),
    ):
        require(foreground, marker, label)
    for marker, label in (
        ("FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS", "restart bound"),
        ("FOREGROUND_RUNTIME_START_TIMEOUT_MS", "start bound"),
        ("foreground-runtime-stop-timeout", "restart timeout"),
        ("runStartTransition(task)", "serialized transition API"),
        ("waitForActiveRuntime(", "runtime acquisition API"),
        ("activeRuntimeId()", "runtime introspection"),
    ):
        require(coordinator, marker, label)

    for marker in (
        "foregroundServiceHeartbeatAt",
        "foregroundServiceDetachedError",
        "foregroundServiceDetachedErrorAt",
        "foregroundServiceInstanceId",
        "foregroundServiceDuplicateSuppressedAt",
        "foregroundServiceRecoveryStatus",
        "p2sLastInboundErrorCode",
    ):
        require(native_bridge, marker, f"status bridge {marker}")
    for marker in (
        '"foreground_service_heartbeat_at"',
        '"foreground_service_instance_id"',
        '"foreground_service_recovery_status"',
        '"p2s_last_inbound_error_code"',
        'put("uriCount", uriCount)',
        'put("packageName", app.packageName)',
        'put("versionName", BuildConfig.VERSION_NAME)',
    ):
        require(native_debug, marker, f"raw diagnostic marker {marker}")

    for secret in (
        '"password"',
        '"hashed_password"',
        '"server_url"',
        '"websocket_url"',
        '"username"',
        '"salt"',
    ):
        forbid(native_debug, secret, f"diagnostic secret key {secret}")

    for marker, label in (
        ('EVENT = "com.clipcascade.CAPTURE_RECOVERY"', "capture recovery event"),
        ('bridge.getValue("wsIsRunning") != "true"', "requested runtime guard"),
        ("HEARTBEAT_STALE_MS = 15_000L", "stale heartbeat guard"),
        ("MIN_RETRY_INTERVAL_MS = 10_000L", "recovery throttle"),
        ("HeadlessJsTaskService.acquireWakeLockNow", "recovery WakeLock"),
    ):
        require(recovery, marker, label)
    require(floating_activity, "ForegroundRuntimeRecovery.startIfRequested", "visible recovery")
    require(headless, "restartFromVisibleCapture", "Headless capture recovery")
    require(headless, "foreground-start-requested", "Headless recovery evidence")

    print("active localized non-secret diagnostics and serialized recovery: OK")


if __name__ == "__main__":
    main()

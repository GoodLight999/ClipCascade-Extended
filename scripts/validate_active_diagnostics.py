#!/usr/bin/env python3
"""Require active event, heartbeat, detached-error and recovery diagnostics."""
from __future__ import annotations

import argparse
from pathlib import Path


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f"missing {label}: {needle!r}")


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
    headless = (root / "HeadlessTask.js").read_text(encoding="utf-8")
    panel = (root / "ExtendedControlPanel.js").read_text(encoding="utf-8")
    analyzer = (root / "AutoDebug.js").read_text(encoding="utf-8")
    i18n = (root / "ExtendedI18n.js").read_text(encoding="utf-8")

    require(native_bridge, "fun runEventBridgeProbe", "native event bridge probe")
    require(native_bridge, "onExtendedDiagnosticProbe", "diagnostic event name")
    require(native_bridge, "DeviceEventManagerModule.RCTDeviceEventEmitter", "React event emitter")
    require(panel, "runEventBridgeProbe", "one-tap active event test")
    require(panel, "new NativeEventEmitter(NativeBridgeModule)", "active event listener")
    require(panel, "probe.eventBridge = eventBridge", "active event result in report")
    require(panel, "formatDiagnosticsReport(report, text)", "localized report dictionary")
    require(panel, "foregroundServiceRecoveryStatus", "recovery state in self-test")
    require(analyzer, "native-react-event-bridge", "active event verdict")
    require(analyzer, "heartbeatAgeMs", "heartbeat freshness verdict")
    require(analyzer, "foregroundServiceDetachedError", "detached callback verdict")
    require(analyzer, "foreground-runtime-singleton", "foreground runtime singleton verdict")
    require(analyzer, "foreground-recovery", "visible recovery verdict")
    require(analyzer, "CHECK_LABEL_KEYS", "localized diagnostic check mapping")
    require(analyzer, "diagnosticsRawStatus", "localized raw-status heading")
    require(analyzer, "diagnosticsNativeProbe", "localized native-probe heading")
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

    require(foreground, "foreground_service_heartbeat_at", "foreground loop heartbeat")
    require(foreground, "foreground_service_detached_error", "detached callback failure evidence")
    require(foreground, "activeForegroundRuntimeId", "single foreground runtime lease")
    require(foreground, "duplicate-runtime-suppressed", "duplicate runtime suppression")
    require(foreground, "finishForegroundRuntime", "runtime lease release")
    require(native_bridge, "foregroundServiceHeartbeatAt", "heartbeat status bridge")
    require(native_bridge, "foregroundServiceDetachedError", "detached error status bridge")
    require(native_bridge, "foregroundServiceDetachedErrorAt", "detached error time bridge")
    require(native_bridge, "foregroundServiceInstanceId", "runtime instance status bridge")
    require(native_bridge, "foregroundServiceDuplicateSuppressedAt", "duplicate status bridge")
    require(native_bridge, "foregroundServiceRecoveryStatus", "recovery status bridge")
    require(native_debug, '"foreground_service_heartbeat_at"', "heartbeat raw snapshot")
    require(native_debug, '"foreground_service_instance_id"', "runtime lease raw snapshot")
    require(native_debug, '"foreground_service_recovery_status"', "recovery raw snapshot")
    require(native_debug, 'put("uriCount", uriCount)', "clipboard URI visibility")
    require(panel, "Clipboard.setString(dialog.copy)", "one-tap full report copy")

    require(recovery, 'EVENT = "com.clipcascade.CAPTURE_RECOVERY"', "capture recovery event")
    require(recovery, 'bridge.getValue("wsIsRunning") != "true"', "requested-runtime guard")
    require(recovery, "HEARTBEAT_STALE_MS = 15_000L", "stale heartbeat guard")
    require(recovery, "MIN_RETRY_INTERVAL_MS = 10_000L", "recovery throttle")
    require(recovery, "HeadlessJsTaskService.acquireWakeLockNow", "recovery WakeLock")
    require(floating_activity, "ForegroundRuntimeRecovery.startIfRequested", "visible Activity recovery")
    require(headless, "restartFromVisibleCapture", "Headless capture recovery")
    require(headless, "foreground-start-requested", "Headless recovery evidence")

    print("active localized automatic diagnostics, detached failures and visible recovery: OK")


if __name__ == "__main__":
    main()

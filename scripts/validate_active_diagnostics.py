#!/usr/bin/env python3
"""Require active event, heartbeat, runtime lease, clipboard URI and report-copy diagnostics."""
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
    foreground = (root / "StartForegroundService.js").read_text(encoding="utf-8")
    panel = (root / "ExtendedControlPanel.js").read_text(encoding="utf-8")
    analyzer = (root / "AutoDebug.js").read_text(encoding="utf-8")

    require(native_bridge, "fun runEventBridgeProbe", "native event bridge probe")
    require(native_bridge, "onExtendedDiagnosticProbe", "diagnostic event name")
    require(native_bridge, "DeviceEventManagerModule.RCTDeviceEventEmitter", "React event emitter")
    require(panel, "runEventBridgeProbe", "one-tap active event test")
    require(panel, "new NativeEventEmitter(NativeBridgeModule)", "active event listener")
    require(panel, "probe.eventBridge = eventBridge", "active event result in report")
    require(analyzer, "native-react-event-bridge", "active event verdict")
    require(analyzer, "heartbeatAgeMs", "heartbeat freshness verdict")
    require(analyzer, "foreground-runtime-singleton", "foreground runtime singleton verdict")
    require(foreground, "foreground_service_heartbeat_at", "foreground loop heartbeat")
    require(foreground, "activeForegroundRuntimeId", "single foreground runtime lease")
    require(foreground, "duplicate-runtime-suppressed", "duplicate runtime suppression")
    require(foreground, "finishForegroundRuntime", "runtime lease release")
    require(native_bridge, "foregroundServiceHeartbeatAt", "heartbeat status bridge")
    require(native_bridge, "foregroundServiceInstanceId", "runtime instance status bridge")
    require(native_bridge, "foregroundServiceDuplicateSuppressedAt", "duplicate status bridge")
    require(native_debug, '"foreground_service_heartbeat_at"', "heartbeat raw snapshot")
    require(native_debug, '"foreground_service_instance_id"', "runtime lease raw snapshot")
    require(native_debug, 'put("uriCount", uriCount)', "clipboard URI visibility")
    require(panel, "Clipboard.setString(dialog.copy)", "one-tap full report copy")

    print("active automatic diagnostics: OK")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Expose active automatic diagnostics and the runtime fields they evaluate."""
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
        "import com.facebook.react.bridge.ReactMethod\n",
        """import com.facebook.react.bridge.ReactMethod
import com.facebook.react.modules.core.DeviceEventManagerModule
""",
        "diagnostic event emitter import",
    )

    replace_once(
        native,
        '''    @ReactMethod
    fun getReliabilityStatus(promise: Promise) {''',
        '''    @ReactMethod
    fun addListener(eventName: String?) = Unit

    @ReactMethod
    fun removeListeners(count: Int?) = Unit

    @ReactMethod
    fun runEventBridgeProbe(token: String, promise: Promise) {
        try {
            reactApplicationContext.runOnUiQueueThread {
                try {
                    reactApplicationContext
                        .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
                        .emit("onExtendedDiagnosticProbe", token)
                    promise.resolve(true)
                } catch (error: Throwable) {
                    promise.reject(
                        "EVENT_BRIDGE_PROBE_ERROR",
                        "Native diagnostic event could not reach React",
                        error
                    )
                }
            }
        } catch (error: Throwable) {
            promise.reject(
                "EVENT_BRIDGE_PROBE_ERROR",
                "Unable to schedule native diagnostic event",
                error
            )
        }
    }

    @ReactMethod
    fun runNativeAutoDebug(promise: Promise) {
        try {
            promise.resolve(ReliabilityAutoDebug.run(reactApplicationContext))
        } catch (error: Throwable) {
            promise.reject("AUTO_DEBUG_ERROR", "Unable to run automatic diagnostics", error)
        }
    }

    @ReactMethod
    fun getReliabilityStatus(promise: Promise) {''',
        "active native automatic diagnostic methods",
    )

    replace_once(
        native,
        '''                put("restartReceiverStatus", bridge.getValue("restart_receiver_status").orEmpty())
                put("readLogs", readLogs)''',
        '''                put("restartReceiverStatus", bridge.getValue("restart_receiver_status").orEmpty())
                put("jsListenerStatus", bridge.getValue("js_listener_status").orEmpty())
                put("foregroundServiceError", bridge.getValue("foreground_service_error").orEmpty())
                put("foregroundServiceState", bridge.getValue("foreground_service_state").orEmpty())
                put("foregroundServiceHeartbeatAt", bridge.getValue("foreground_service_heartbeat_at").orEmpty())
                put("foregroundServiceLastStartedAt", bridge.getValue("foreground_service_last_started_at").orEmpty())
                put("foregroundServiceLastStoppedAt", bridge.getValue("foreground_service_last_stopped_at").orEmpty())
                put("p2pCandidatePeers", bridge.getValue("p2p_candidate_peers")?.toIntOrNull() ?: 0)
                put("p2pCompatiblePeers", bridge.getValue("p2p_compatible_peers")?.toIntOrNull() ?: 0)
                put("p2pIncompatiblePeers", bridge.getValue("p2p_incompatible_peers")?.toIntOrNull() ?: 0)
                put("p2pLastCompatibilityError", bridge.getValue("p2p_last_compatibility_error").orEmpty())
                put("readLogs", readLogs)''',
        "automatic diagnostic status fields",
    )


if __name__ == "__main__":
    main()

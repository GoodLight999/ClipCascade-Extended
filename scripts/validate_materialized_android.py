#!/usr/bin/env python3
"""Fail CI when the generated Android tree violates reliability invariants."""
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
    manifest = (android / "AndroidManifest.xml").read_text(encoding="utf-8")
    accessibility_xml = (
        android / "res/xml/clipcascade_accessibility_service.xml"
    ).read_text(encoding="utf-8")
    build_gradle = (root / "android/app/build.gradle").read_text(encoding="utf-8")
    app_js = (root / "App.js").read_text(encoding="utf-8")
    foreground_js = (root / "StartForegroundService.js").read_text(encoding="utf-8")
    headless_js = (root / "HeadlessTask.js").read_text(encoding="utf-8")
    queue_js = (root / "DurableOutboundQueue.js").read_text(encoding="utf-8")
    fragmenter_js = (root / "Utf8Fragmenter.js").read_text(encoding="utf-8")
    accumulator_js = (root / "P2PFragmentAccumulator.js").read_text(encoding="utf-8")
    channel_sender_js = (root / "P2PChannelSender.js").read_text(encoding="utf-8")

    require(manifest, ".ClipCascadeAccessibilityService", "Accessibility service")
    require(manifest, "android.permission.BIND_ACCESSIBILITY_SERVICE", "Accessibility binding")
    require(manifest, "android.intent.action.MY_PACKAGE_REPLACED", "package update restart")
    require(accessibility_xml, 'android:canRetrieveWindowContent="false"', "privacy setting")
    require(build_gradle, 'applicationId "com.clipcascade.extended"', "permanent package")
    require(build_gradle, "versionCode 320003", "monotonic versionCode")
    require(build_gradle, 'versionName "3.2.0-extended.3"', "versionName")
    require(app_js, "const APP_VERSION = '3.2.0-extended.3';", "UI version")
    require(app_js, "JS event listener ready", "listener readiness self-test")
    require(app_js, "Shared payload staging", "shared payload self-test")
    require(app_js, "Outbound queue", "outbound queue self-test")
    require(headless_js, "android.intent.action.MY_PACKAGE_REPLACED", "update headless restart")

    kotlin_files = list((android / "java/com/clipcascade").glob("*.kt"))
    all_native = "\n".join(path.read_text(encoding="utf-8") for path in kotlin_files)
    forbid(all_native, "FLAG_ACTIVITY_CLEAR_TASK", "task-destructive launch flag")
    require(all_native, "selection-without-copy", "selection false-positive guard")
    require(all_native, "activateAndDrain", "React listener readiness gate")
    require(all_native, "capture-timeout", "capture watchdog")
    require(all_native, "one-time-setup-only", "one-time Shizuku contract")
    require(all_native, "ClipCascade-ShareStager", "shared URI staging")
    require(all_native, "acquireWakeLockNow", "Headless JS wake lock")

    require(foreground_js, "⏳ Connecting...", "fresh connection status")
    require(
        foreground_js,
        "✅ Signaling connected; waiting for peer",
        "truthful P2P signaling status",
    )
    require(foreground_js, "✅ P2P peer connected", "truthful P2P peer status")
    require(foreground_js, "createDurableOutboundQueue", "durable outbound integration")
    require(foreground_js, "waiting-for-transport", "offline queue state")
    require(foreground_js, "enqueueOutboundClipboard", "early durable event enqueue")
    require(foreground_js, "p2pTransportReady", "cross-scope P2P readiness")
    require(foreground_js, "scheduleOutboundRetry", "bounded retry scheduling")
    require(foreground_js, "createP2PFragmentAccumulator", "concurrent fragment integration")
    require(
        foreground_js,
        "onDataChannelMessage(e.data, remotePeerId)",
        "peer-scoped fragment identity",
    )
    require(foreground_js, "fragmentAccumulator.clearPeer", "peer fragment cleanup")
    require(foreground_js, "deliveryId || (await generateUuid())", "idempotent P2P retry ID")
    require(foreground_js, "sendP2PFragment(openChannels, messageJson)", "P2P backpressure send")
    forbid(foreground_js, "receivingFragments =", "single global fragment buffer")
    forbid(foreground_js, "await sendClipBoard(", "pre-initialization event dispatch")
    forbid(foreground_js, "textEncoder.encode(clipContent)", "unsafe P2P byte sizing")
    require(queue_js, "MAX_FAILURES = 8", "finite permanent failure policy")
    require(queue_js, "raw.scope === scope", "server-scoped outbound queue")
    require(fragmenter_js, "bytes[end] & 0xc0", "UTF-8 code-point boundary guard")
    require(accumulator_js, "Too many concurrent fragmented", "fragment concurrency bound")
    require(accumulator_js, "Conflicting duplicate fragment", "fragment conflict guard")
    require(accumulator_js, "duplicate-complete", "completed fragment replay guard")
    require(channel_sender_js, "bufferedAmount", "DataChannel buffered amount guard")
    require(channel_sender_js, "backpressure timeout", "DataChannel timeout guard")

    runtime_files = [
        android / "java/com/clipcascade/ClipCascadeAccessibilityService.kt",
        android / "java/com/clipcascade/ClipboardCaptureCoordinator.kt",
        android / "java/com/clipcascade/ClipboardFloatingActivity.kt",
        android / "java/com/clipcascade/ClipboardListenerModule.kt",
        android / "java/com/clipcascade/SharedPayloadStager.kt",
        root / "StartForegroundService.js",
        root / "DurableOutboundQueue.js",
        root / "P2PFragmentAccumulator.js",
        root / "P2PChannelSender.js",
    ]
    for path in runtime_files:
        text = path.read_text(encoding="utf-8")
        forbid(text, "rikka.shizuku", f"runtime Shizuku dependency in {path.name}")
        forbid(text, "Shizuku.", f"runtime Shizuku call in {path.name}")

    print("materialized Android reliability invariants: OK")


if __name__ == "__main__":
    main()

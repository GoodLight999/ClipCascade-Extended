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


def require_before(text: str, first: str, second: str, label: str) -> None:
    first_index = text.find(first)
    second_index = text.find(second)
    if first_index < 0 or second_index < 0 or first_index >= second_index:
        raise RuntimeError(f"invalid ordering for {label}: {first!r} before {second!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root.resolve()

    android = root / "android/app/src/main"
    manifest = (android / "AndroidManifest.xml").read_text(encoding="utf-8")
    accessibility_xml = (
        android / "res/xml/clipcascade_accessibility_service.xml"
    ).read_text(encoding="utf-8")
    accessibility_service = (
        android / "java/com/clipcascade/ClipCascadeAccessibilityService.kt"
    ).read_text(encoding="utf-8")
    shizuku_setup = (
        android / "java/com/clipcascade/ShizukuSetup.kt"
    ).read_text(encoding="utf-8")
    native_debug = (
        android / "java/com/clipcascade/ReliabilityAutoDebug.kt"
    ).read_text(encoding="utf-8")
    build_gradle = (root / "android/app/build.gradle").read_text(encoding="utf-8")
    app_js = (root / "App.js").read_text(encoding="utf-8")
    foreground_js = (root / "StartForegroundService.js").read_text(encoding="utf-8")
    headless_js = (root / "HeadlessTask.js").read_text(encoding="utf-8")
    queue_js = (root / "DurableOutboundQueue.js").read_text(encoding="utf-8")
    fragmenter_js = (root / "Utf8Fragmenter.js").read_text(encoding="utf-8")
    accumulator_js = (root / "P2PFragmentAccumulator.js").read_text(encoding="utf-8")
    channel_sender_js = (root / "P2PChannelSender.js").read_text(encoding="utf-8")
    p2s_ack_js = (root / "P2SAckTracker.js").read_text(encoding="utf-8")
    file_uris_js = (root / "OutboundFileUris.js").read_text(encoding="utf-8")
    i18n_js = (root / "ExtendedI18n.js").read_text(encoding="utf-8")
    control_panel_js = (root / "ExtendedControlPanel.js").read_text(encoding="utf-8")
    auto_debug_js = (root / "AutoDebug.js").read_text(encoding="utf-8")
    p2p_compat_js = (root / "P2PCompatibility.js").read_text(encoding="utf-8")

    require(manifest, ".ClipCascadeAccessibilityService", "Accessibility service")
    require(manifest, "android.permission.BIND_ACCESSIBILITY_SERVICE", "Accessibility binding")
    require(manifest, "android.intent.action.MY_PACKAGE_REPLACED", "package update restart")
    require(accessibility_xml, 'android:canRetrieveWindowContent="false"', "privacy setting")
    forbid(
        accessibility_xml,
        "typeViewTextSelectionChanged",
        "selection-only Accessibility subscription",
    )
    require(accessibility_service, "SYNC_CHECK_CACHE_MS = 250L", "bounded sync-state lookup")
    require_before(
        accessibility_service,
        "if (!decision.capture) return",
        "if (!isSyncRequested())",
        "copy classification before AsyncStorage lookup",
    )

    require(build_gradle, 'applicationId "com.clipcascade.extended"', "permanent package")
    require(build_gradle, "versionCode 320004", "monotonic versionCode")
    require(build_gradle, 'versionName "3.2.0-extended.4"', "versionName")
    require(app_js, "const APP_VERSION = '3.2.0-extended.4';", "UI version")
    require(app_js, "ExtendedControlPanel", "Extended-only control panel")
    require(app_js, "getExtendedStrings", "complete product localization")
    require(app_js, "PlatformColor('?android:attr/textColorPrimary')", "adaptive text color")
    require(app_js, "EXTENDED_TEXT.username", "localized login form")
    require(app_js, "EXTENDED_TEXT.start", "localized synchronization controls")
    require(app_js, "APP_VERSION}</Text>", "visible product version")
    for inherited in (
        "New version available!",
        "GITHUB",
        "DONATE",
        "HOMEPAGE",
        "Automatic Clipboard Monitoring Setup",
        "raw.githubusercontent.com/Sathvik-Rao/ClipCascade/main/version.json",
        "raw.githubusercontent.com/Sathvik-Rao/ClipCascade/main/metadata.json",
        "adb -d shell am force-stop",
        "EXTENDED_SETUP_TEXT",
    ):
        forbid(app_js, inherited, f"inherited upstream UI residue {inherited}")

    for locale in ("ja:", "zh:", "en:"):
        require(i18n_js, locale, f"locale dictionary {locale}")
    for key in ("username", "login", "start", "shizukuSetup", "autoDebug", "copy"):
        require(i18n_js, f"{key}:", f"localized key {key}")
    require(control_panel_js, "selectable", "selectable diagnostic text")
    require(control_panel_js, "Clipboard.setString(dialog.copy)", "one-tap report/ADB copy")
    require(control_panel_js, "runNativeAutoDebug", "automatic diagnostic button")
    require(auto_debug_js, "event-listener-order", "listener-order verdict")
    require(auto_debug_js, "foreground-service", "foreground-service verdict")
    require(native_debug, "clipboardRead", "native foreground clipboard probe")
    require(native_debug, "sharedCacheBytes", "shared-cache diagnostics")

    require(headless_js, "android.intent.action.MY_PACKAGE_REPLACED", "update headless restart")

    kotlin_files = list((android / "java/com/clipcascade").glob("*.kt"))
    all_native = "\n".join(path.read_text(encoding="utf-8") for path in kotlin_files)
    forbid(all_native, "FLAG_ACTIVITY_CLEAR_TASK", "task-destructive launch flag")
    require(all_native, "selection-without-copy", "selection false-positive guard")
    require(all_native, "activateAndDrain", "React listener readiness gate")
    require(all_native, "capture-timeout", "capture watchdog")
    require(all_native, "one-time-setup-only", "one-time Shizuku contract")
    require(all_native, "ClipCascade-ShareStager", "shared URI staging")
    require(all_native, "MAX_CACHE_BYTES", "shared cache total bound")
    require(all_native, "MAX_BATCH_BYTES", "shared batch bound")
    require(all_native, "JSONArray(staged.map(Uri::toString))", "JSON-safe staged file URIs")
    require(all_native, "shared_payload_pending", "pending Android Share startup")
    require(
        all_native,
        "nontext-clipboard-use-android-share",
        "stable non-text outbound boundary",
    )
    require(all_native, "acquireWakeLockNow", "Headless JS wake lock")
    require(shizuku_setup, "addBinderReceivedListenerSticky", "asynchronous Shizuku Binder delivery")
    require(shizuku_setup, "awaitBinder(BINDER_TIMEOUT_MS)", "bounded Shizuku Binder wait")
    require(shizuku_setup, "addBinderDeadListener", "Shizuku Binder death tracking")

    require_before(
        foreground_js,
        "const clipboardOnChange = clipboardListener.addListener(",
        "await ClipboardListener.startListening();",
        "JS listener registration before native durable-event drain",
    )
    require(foreground_js, "ready-after-registration", "listener-order evidence")
    require(foreground_js, "foregroundServiceHandlerRegistered", "single foreground handler")
    require(foreground_js, "foreground_service_error", "persistent foreground-service error")
    require(foreground_js, "service-started-for-share", "automatic share service start")
    require(foreground_js, "share-image-enqueued", "image share enqueue evidence")
    require(foreground_js, "share-files-enqueued", "file share enqueue evidence")
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
    require(foreground_js, "evaluateP2PCompatibility", "tested P2P compatibility policy")
    require(foreground_js, "quarantinedPeers", "incompatible peer quarantine")
    require(foreground_js, "p2p_incompatible_peers", "P2P compatibility diagnostics")
    forbid(
        foreground_js,
        "Encryption must be enabled on all devices if enabled",
        "room-wide repeated P2P decrypt error",
    )
    require(p2p_compat_js, "legacy-peer-no-hello", "legacy peer compatibility state")
    require(p2p_compat_js, "encryption-key", "encryption key mismatch policy")
    require(foreground_js, "createP2SAckTracker", "P2S server-echo acknowledgement")
    require(foreground_js, "extendedDeliveryId", "P2S delivery metadata")
    require(foreground_js, "awaiting-p2s-ack", "P2S durable acknowledgement state")
    require(
        foreground_js,
        "p2s-echo-acknowledged",
        "P2S queue release only after server echo",
    )
    require(foreground_js, "P2S server echo acknowledgement timed out", "P2S ACK timeout")
    require(foreground_js, "parseOutboundFileUris", "JSON-safe outbound file URI parsing")
    forbid(
        foreground_js,
        "const file_paths = clipContent\n                      .split(',')",
        "comma-split file URI parsing",
    )
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
    require(p2s_ack_js, "P2S acknowledgement ID is required", "P2S ACK input guard")
    require(p2s_ack_js, "active?.id !== id", "P2S ACK identity guard")
    require(file_uris_js, "JSON.parse(value)", "JSON file URI decoding")
    require(file_uris_js, "Backward compatibility", "legacy file URI compatibility")

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
        root / "P2SAckTracker.js",
        root / "OutboundFileUris.js",
    ]
    for runtime_path in runtime_files:
        runtime_text = runtime_path.read_text(encoding="utf-8")
        forbid(runtime_text, "rikka.shizuku", f"runtime Shizuku dependency in {runtime_path.name}")
        forbid(runtime_text, "Shizuku.", f"runtime Shizuku call in {runtime_path.name}")

    print("materialized Android reliability invariants: OK")


if __name__ == "__main__":
    main()

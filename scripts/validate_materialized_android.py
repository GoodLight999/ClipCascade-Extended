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


def read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def require_all(text: str, markers: tuple[str, ...], scope: str) -> None:
    for marker in markers:
        require(text, marker, f"{scope}: {marker}")


def forbid_all(text: str, markers: tuple[str, ...], scope: str) -> None:
    for marker in markers:
        forbid(text, marker, f"{scope}: {marker}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root.resolve()
    android = root / "android/app/src/main"

    manifest = read(android, "AndroidManifest.xml")
    accessibility_xml = read(android, "res/xml/clipcascade_accessibility_service.xml")
    accessibility_service = read(
        android, "java/com/clipcascade/ClipCascadeAccessibilityService.kt"
    )
    shizuku_setup = read(android, "java/com/clipcascade/ShizukuSetup.kt")
    native_debug = read(android, "java/com/clipcascade/ReliabilityAutoDebug.kt")
    build_gradle = read(root, "android/app/build.gradle")
    app_js = read(root, "App.js")
    foreground_js = read(root, "StartForegroundService.js")
    headless_js = read(root, "HeadlessTask.js")
    queue_js = read(root, "DurableOutboundQueue.js")
    fragmenter_js = read(root, "Utf8Fragmenter.js")
    accumulator_js = read(root, "P2PFragmentAccumulator.js")
    channel_sender_js = read(root, "P2PChannelSender.js")
    receipt_js = read(root, "P2SReceiptTracker.js")
    feedback_guard_js = read(root, "OneShotContentGuard.js")
    delivery_policy_js = read(root, "OutboundDeliveryPolicy.js")
    delivery_executor_js = read(root, "OutboundDeliveryExecutor.js")
    file_uris_js = read(root, "OutboundFileUris.js")
    i18n_js = read(root, "ExtendedI18n.js")
    control_panel_js = read(root, "ExtendedControlPanel.js")
    auto_debug_js = read(root, "AutoDebug.js")
    p2p_compat_js = read(root, "P2PCompatibility.js")
    pending_share_policy_js = read(root, "PendingShareStartPolicy.js")
    service_policy_js = read(root, "ServiceControlPolicy.js")
    coordinator_js = read(root, "ForegroundRuntimeCoordinator.js")

    # Product identity, package continuity and privacy boundary.
    require_all(
        manifest,
        (
            ".ClipCascadeAccessibilityService",
            "android.permission.BIND_ACCESSIBILITY_SERVICE",
            "android.intent.action.MY_PACKAGE_REPLACED",
        ),
        "manifest",
    )
    require(accessibility_xml, 'android:canRetrieveWindowContent="false"', "privacy setting")
    forbid(accessibility_xml, "typeViewTextSelectionChanged", "selection-only subscription")
    require(accessibility_service, "SYNC_CHECK_CACHE_MS = 250L", "bounded sync lookup")
    require_before(
        accessibility_service,
        "if (!decision.capture) return",
        "if (!isSyncRequested())",
        "classification before storage lookup",
    )
    require_all(
        build_gradle,
        (
            'applicationId "com.clipcascade.extended"',
            "versionCode 320005",
            'versionName "3.2.0-extended.5"',
            "debuggable false",
        ),
        "build identity",
    )

    # Extended-owned UI, complete localization and explicit service control.
    require_all(
        app_js,
        (
            "const APP_VERSION = '3.2.0-extended.5';",
            "ExtendedControlPanel",
            "getExtendedStrings",
            "EXTENDED_TEXT.username",
            "EXTENDED_TEXT.start",
            "APP_VERSION}</Text>",
            "planPendingShareStart",
            "pendingSharePlan.forceRestart",
            "foreground_service_heartbeat_at",
            "foreground_service_last_started_at",
            "let controlLockAcquired = false;",
            "resolveRequestedServiceState(",
            "restartReason",
            "work-manager-recovery",
            "pollUIFlags().catch",
            "if (controlLockAcquired) {",
        ),
        "App service/UI contract",
    )
    require_before(
        app_js,
        "const [enableWSPage, setEnableWSPage] = useState(false);",
        "sessionReadyRef.current = enableWSPage;",
        "session state before synchronization effect",
    )
    forbid_all(
        app_js,
        (
            "New version available!",
            "GITHUB",
            "DONATE",
            "HOMEPAGE",
            "Automatic Clipboard Monitoring Setup",
            "raw.githubusercontent.com/Sathvik-Rao/ClipCascade/main/version.json",
            "raw.githubusercontent.com/Sathvik-Rao/ClipCascade/main/metadata.json",
            "adb -d shell am force-stop",
            "EXTENDED_SETUP_TEXT",
        ),
        "inherited UI/network residue",
    )
    require_all(
        pending_share_policy_js,
        (
            "FOREGROUND_HEARTBEAT_STALE_MS = 15_000",
            "reason: forceRestart ? 'stale-runtime' : 'runtime-stopped'",
            "elapsed >= 0 && elapsed <= Number(maxAgeMs)",
        ),
        "pending share policy",
    )
    require_all(
        service_policy_js,
        (
            "FOREGROUND_STOP_TIMEOUT_MS = 10_000",
            "forceRestart = false",
            "forcedStart",
            "elapsed < 0 || elapsed >= Number(timeoutMs)",
        ),
        "service control policy",
    )

    for locale in ("ja:", "zh:", "en:"):
        require(i18n_js, locale, f"locale dictionary {locale}")
    for key in ("username", "login", "start", "shizukuSetup", "autoDebug", "copy"):
        require(i18n_js, f"{key}:", f"localized key {key}")
    require_all(
        control_panel_js,
        ("selectable", "Clipboard.setString(dialog.copy)", "runNativeAutoDebug"),
        "diagnostics UI",
    )
    require_all(auto_debug_js, ("event-listener-order", "foreground-service"), "auto debug")
    require_all(native_debug, ("clipboardRead", "uriCount", "sharedCacheBytes"), "native debug")

    # Native capture ordering, Share staging and one-time Shizuku setup.
    require_all(
        headless_js,
        ("android.intent.action.MY_PACKAGE_REPLACED", "forceRestart: true"),
        "Headless recovery",
    )
    kotlin_files = list((android / "java/com/clipcascade").glob("*.kt"))
    all_native = "\n".join(path.read_text(encoding="utf-8") for path in kotlin_files)
    require_all(
        all_native,
        (
            "selection-without-copy",
            "activateAndDrain",
            "drainInOrder",
            "admissionPlan",
            "QUEUE_AND_DRAIN",
            "retry-scheduled",
            "capture-timeout",
            "URI_STAGING_TIMEOUT_MS = 120_000L",
            "extendForUriStaging",
            "one-time-setup-only",
            "ClipCascade-ShareStager",
            "MAX_CACHE_BYTES",
            "MAX_BATCH_BYTES",
            "JSONArray(staged.map(Uri::toString))",
            "shared_payload_pending",
            "fun readOrStage",
            "clipboard-uri-staging",
            "clipboard-uri-duplicate-suppressed",
            "capture-delivered:$type",
            "acquireWakeLockNow",
        ),
        "native reliability",
    )
    forbid_all(
        all_native,
        ("FLAG_ACTIVITY_CLEAR_TASK", "nontext-clipboard-use-android-share"),
        "native regressions",
    )
    require_all(
        shizuku_setup,
        (
            "addBinderReceivedListenerSticky",
            "awaitBinder(BINDER_TIMEOUT_MS)",
            "addBinderDeadListener",
        ),
        "Shizuku lifecycle",
    )

    # One runtime lease, serialized start, live callback confirmation and stop-safe queue.
    require_before(
        foreground_js,
        "const clipboardOnChange = trackClipboardSubscription(clipboardListener.addListener(",
        "await ClipboardListener.startListening();",
        "listener registration before native drain",
    )
    require_all(
        coordinator_js,
        (
            "FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS = 10_000",
            "FOREGROUND_RUNTIME_START_TIMEOUT_MS = 8_000",
            "startTransitionChain = Promise.resolve()",
            "runStartTransition(task)",
            "waitForActiveRuntime(",
            "requestRestart(",
            "foreground-runtime-stop-timeout",
        ),
        "runtime coordinator",
    )
    require_all(
        foreground_js,
        (
            "foregroundServiceHandlerRegistered",
            "foregroundRuntimeCoordinator.runStartTransition",
            "foregroundRuntimeCoordinator.waitForActiveRuntime",
            "foreground runtime did not acquire a lease",
            "runtimeLease.finish()",
            "duplicate-runtime-suppressed",
            "ready-after-registration",
            "foreground_service_error",
            "foreground_service_last_started_at",
            "share-image-enqueued",
            "share-files-enqueued",
            "createDurableOutboundQueue",
            "enqueueOutboundClipboard",
            "p2pTransportReady",
            "scheduleOutboundRetry",
            "if (shouldPreserveRuntimeQueue())",
            "preserved-for-${runtimeStopReason}",
        ),
        "foreground runtime",
    )
    forbid_all(
        foreground_js,
        ("removeAllListeners(", "let activeForegroundRuntimeId", "new Promise(async"),
        "runtime ownership regressions",
    )

    # P2P truthfulness, bounded fragmentation and peer isolation.
    require_all(
        foreground_js,
        (
            "⏳ Connecting...",
            "✅ Signaling connected; waiting for peer",
            "✅ P2P peer connected",
            "createP2PFragmentAccumulator",
            "onDataChannelMessage(e.data, remotePeerId)",
            "fragmentAccumulator.clearPeer",
            "deliveryId || (await generateUuid())",
            "sendP2PFragment(openChannels, messageJson)",
            "evaluateP2PCompatibility",
            "quarantinedPeers",
            "p2p_incompatible_peers",
            "OUTBOUND_DELIVERY.SENT",
        ),
        "P2P reliability",
    )
    forbid(foreground_js, "Encryption must be enabled on all devices if enabled", "room-wide decrypt error")
    require_all(p2p_compat_js, ("legacy-peer-no-hello", "encryption-key"), "P2P compatibility")
    require_all(
        fragmenter_js,
        ("bytes[end] & 0xc0",),
        "UTF-8 fragmentation",
    )
    require_all(
        accumulator_js,
        ("Too many concurrent fragmented", "Conflicting duplicate fragment", "duplicate-complete"),
        "fragment accumulator",
    )
    require_all(channel_sender_js, ("bufferedAmount", "backpressure timeout"), "DataChannel sender")

    # P2S remains upstream-payload-compatible while using standard receipt and self-echo ACKs.
    require_all(
        foreground_js,
        (
            "createP2SReceiptTracker",
            "watchForReceipt(receiptId",
            "headers: {receipt: receiptId}",
            "p2s-self-echo-suppressed",
            "p2s-receipt-timeout",
            "OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT",
            "applyOutboundDeliveryResult",
            "createOneShotContentGuard",
            "feedback-suppressed",
            "OUTBOUND_DELIVERY.WAITING",
        ),
        "P2S delivery",
    )
    forbid_all(
        foreground_js,
        (
            "createP2SAckTracker",
            "extendedDeliveryId",
            "awaiting-p2s-ack",
            "p2s-echo-acknowledged",
            "P2S server echo acknowledgement timed out",
            "previous_clipboard_content_hash",
            "block_image_once",
            "newCB(",
            "result !== false",
        ),
        "legacy transport semantics",
    )
    require_all(
        receipt_js,
        (
            "P2S receipt delivery ID is required",
            "active.id !== id",
            "queuedHeadId",
            "Promise.resolve(onTimeout(id)).catch",
        ),
        "receipt tracker",
    )
    require_all(
        feedback_guard_js,
        (
            "LOCAL_FEEDBACK_WINDOW_MS = 5_000",
            "P2S_ECHO_WINDOW_MS = 30_000",
            "clearOnMismatch",
            "clock-rollback",
        ),
        "typed feedback guard",
    )
    require_all(
        delivery_policy_js,
        (
            "WAITING: 'waiting-for-transport'",
            "AWAITING_P2S_RECEIPT",
            "Invalid outbound delivery result",
            "p2s-receipt-already-acknowledged",
        ),
        "delivery policy",
    )
    require_all(
        delivery_executor_js,
        ("const currentHead = await peek();", "resolveAwaitingReceiptHead"),
        "delivery executor",
    )

    # Queue, file URI and runtime-dependency boundaries.
    require_all(queue_js, ("MAX_FAILURES = 8", "raw.scope === scope"), "durable queue")
    require_all(file_uris_js, ("JSON.parse(value)", "Backward compatibility"), "file URI parser")
    require(foreground_js, "parseOutboundFileUris", "JSON-safe outbound file URIs")
    forbid_all(
        foreground_js,
        (
            "const file_paths = clipContent\n                      .split(',')",
            "receivingFragments =",
            "await sendClipBoard(",
            "textEncoder.encode(clipContent)",
        ),
        "generated transport regressions",
    )

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
        root / "P2SReceiptTracker.js",
        root / "OneShotContentGuard.js",
        root / "OutboundDeliveryPolicy.js",
        root / "OutboundDeliveryExecutor.js",
        root / "OutboundFileUris.js",
    ]
    for runtime_path in runtime_files:
        runtime_text = runtime_path.read_text(encoding="utf-8")
        forbid(runtime_text, "rikka.shizuku", f"runtime Shizuku dependency in {runtime_path.name}")
        forbid(runtime_text, "Shizuku.", f"runtime Shizuku call in {runtime_path.name}")

    print("materialized Android reliability invariants: OK")


if __name__ == "__main__":
    main()

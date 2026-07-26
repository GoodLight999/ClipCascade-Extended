#!/usr/bin/env python3
"""Prevent stale service toggles, unsafe replacement and private P2P controls."""
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
    app = (root / "App.js").read_text(encoding="utf-8")
    service = (root / "StartForegroundService.js").read_text(encoding="utf-8")
    policy = (root / "ServiceControlPolicy.js").read_text(encoding="utf-8")
    pending = (root / "PendingShareStartPolicy.js").read_text(encoding="utf-8")
    coordinator = (root / "ForegroundRuntimeCoordinator.js").read_text(encoding="utf-8")
    detached = (root / "DetachedTaskSupervisor.js").read_text(encoding="utf-8")

    for marker, label in (
        ("resolveRequestedServiceState(", "persistent explicit service intent"),
        ("desiredState = null", "desired-state API"),
        ("forceRestart = false", "forced restart API"),
        ("restartReason = null", "restart reason API"),
        ("foregroundService('true', pendingSharePlan.forceRestart", "heartbeat-aware auto start"),
        ("work-manager-recovery", "explicit WorkManager recovery"),
        ("onPress={() => foregroundService()}", "UI-only toggle"),
        ("StartForegroundService({", "coordinator start input"),
        ("forceRestart,", "force restart forwarding"),
        ("restartReason,", "restart reason forwarding"),
        ("requested.noOp", "already-satisfied intent guard"),
        ("hasForegroundStopTimedOut", "bounded stop policy"),
        ("stop-timeout", "truthful stop timeout state"),
        ("pollUIFlags().catch", "supervised UI polling"),
        ("if (controlLockAcquired)", "owner-only lock release"),
    ):
        require(app, marker, label)
    forbid(app, "wsIsRunning === 'true' ? 'false' : 'true'", "stale React-state toggle")

    for marker, label in (
        ("FOREGROUND_STOP_TIMEOUT_MS = 10_000", "stop bound"),
        ("resolveRequestedServiceState", "service-state resolver"),
        ("forceRestart = false", "force restart parameter"),
        ("forcedStart", "force restart result"),
        ("elapsed < 0 || elapsed >= Number(timeoutMs)", "rollback-safe timeout"),
    ):
        require(policy, marker, label)
    for marker, label in (
        ("FOREGROUND_HEARTBEAT_STALE_MS = 15_000", "heartbeat freshness"),
        ("forceRestart ? 'stale-runtime' : 'runtime-stopped'", "stale restart classification"),
    ):
        require(pending, marker, label)

    for marker, label in (
        ("FOREGROUND_RUNTIME_RESTART_TIMEOUT_MS = 10_000", "restart bound"),
        ("FOREGROUND_RUNTIME_START_TIMEOUT_MS = 8_000", "start bound"),
        ("createForegroundRuntimeCoordinator", "coordinator factory"),
        ("runStartTransition(task)", "serialized starts"),
        ("waitForActiveRuntime(", "callback lease wait"),
        ("requestRestart(", "serialized restart"),
        ("current.completion.then(() => true)", "exact lease completion wait"),
        ("foreground-runtime-stop-timeout", "restart timeout evidence"),
        ("activeRuntimeId()", "coordinator introspection"),
    ):
        require(coordinator, marker, label)

    for marker, label in (
        ("foregroundRuntimeCoordinator.acquire", "runtime lease"),
        ("foregroundRuntimeCoordinator.runStartTransition", "serialized start integration"),
        ("foregroundRuntimeCoordinator.requestRestart", "forced restart integration"),
        ("foregroundRuntimeCoordinator.waitForActiveRuntime", "runtime start confirmation"),
        ("`restart-waiting:${restartReason}`", "restart waiting evidence"),
        ("restart-stop-requested:", "old runtime stop evidence"),
        ("restart-old-runtime-stopped:", "old runtime completion evidence"),
        ("handler-confirmed:", "new runtime confirmation"),
        ("foreground runtime did not acquire a lease", "start failure evidence"),
        ("runtimeLease.finish()", "terminal lease release"),
        ("duplicate-runtime-suppressed", "duplicate suppression"),
        ("activeClipboardSubscriptions", "owned listener registry"),
        ("trackClipboardSubscription", "owned listener registration"),
        ("removeClipboardSubscription", "owned listener removal"),
        ("createDetachedTaskSupervisor", "detached supervisor"),
        ("const runRuntimeDetached = (scope, task) =>", "runtime-scoped supervisor"),
        ("pollFlagsLoop().catch", "poll-loop supervision"),
        ("handler-unhandled-failure", "terminal async failure state"),
        ("finishForegroundRuntime('failed')", "failure lease release"),
    ):
        require(service, marker, label)
    forbid(service, "let activeForegroundRuntimeId", "uncoordinated ownership")
    forbid(service, "removeAllListeners(", "global listener deletion")
    forbid(service, "new Promise(async", "async Promise executor")
    forbid(service, "        pollFlagsLoop();", "unsupervised poll loop")

    for scope in (
        "shared-text",
        "shared-image",
        "shared-files",
        "native-clipboard-change",
        "outbound-retry",
        "p2s-connect",
        "p2s-disconnect",
        "p2s-stomp-error",
        "p2s-websocket-error",
        "p2s-websocket-close",
        "p2s-subscription-message",
        "p2s-receipt-timeout",
        "p2s-receipt",
        "signaling-reconnect",
        "signaling-open",
        "signaling-message",
        "signaling-error",
        "signaling-close",
    ):
        require(service, f"runRuntimeDetached('{scope}'", f"supervised callback {scope}")
    for scope in (
        "ice-candidate",
        "datachannel-received",
        "peer-recovery",
        "datachannel-open",
        "datachannel-message",
        "datachannel-close",
        "datachannel-error",
    ):
        require(service, f"runRuntimeDetached(`{scope}:${{remotePeerId}}`", f"peer callback {scope}")

    require(detached, "Promise.resolve()", "safe detached chain")
    require(detached, ".catch(() => undefined)", "failure-recorder guard")

    # Legacy-server-compatible P2P controls only.
    for marker, label in (
        ("localCompatibility", "local compatibility descriptor"),
        ("case 'OFFER': {", "OFFER receiver"),
        ("case 'ANSWER': {", "ANSWER receiver"),
        ("compatibility: localCompatibility", "forwarded compatibility metadata"),
        ("compatibility.state !== 'incompatible'", "pre-connection mismatch guard"),
        ("!quarantinedPeers.has(peerId)", "quarantined peer filter"),
        ("for (const pid of peers)", "awaited peer reconciliation"),
        ("clearPeerErrorIfOwned", "same-peer error recovery"),
        ("let signalingReconnectTimer = null", "single reconnect timer"),
        ("const clearSignalingReconnect", "reconnect cancellation"),
        ("const scheduleSignalingReconnect", "reconnect scheduler"),
        ("Never send private control frames over the clipboard DataChannel", "legacy-safe liveness"),
    ):
        require(service, marker, label)
    for forbidden, label in (
        ("peers.forEach(async", "detached peer reconciliation"),
        (".then(() => op()).catch(() => {})", "swallowed peer failure"),
        ("setTimeout(async () =>", "detached async reconnect"),
        ("type: 'COMPATIBILITY'", "custom signaling type"),
        ("case 'COMPATIBILITY'", "custom signaling receiver"),
        ("P2P_COMPATIBILITY_JSON", "DataChannel compatibility frame"),
        ("P2P_DC_KEEPALIVE_JSON", "DataChannel keepalive frame"),
        ("keyFingerprint", "password-derived fingerprint"),
        ("localKeyFingerprint", "local password verifier"),
    ):
        forbid(service, forbidden, label)

    print("serialized service acquisition, owned callbacks and legacy-safe P2P controls: OK")


if __name__ == "__main__":
    main()

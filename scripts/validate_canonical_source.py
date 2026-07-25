#!/usr/bin/env python3
"""Validate the checked-in canonical source before upstream materialization."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FINALIZERS = 29


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> None:
    lock = read("UPSTREAM.lock")
    require("UPSTREAM_REPOSITORY=Sathvik-Rao/ClipCascade" in lock, "canonical upstream missing")
    require("UPSTREAM_COMMIT=" in lock, "pinned upstream commit missing")
    require("UPSTREAM_MOBILE_PATH=ClipCascade_Mobile/src" in lock, "mobile path missing")

    apply_overlay = read("scripts/apply_overlay.py")
    require("NotificationCaptureService" not in apply_overlay, "OTP service reintroduced")
    require("OtpExtractor" not in apply_overlay, "OTP extractor reintroduced")
    require('VERSION_CODE = "320005"' in apply_overlay, "canonical versionCode is not extended.5")
    require(
        'VERSION_NAME = "3.2.0-extended.5"' in apply_overlay,
        "canonical versionName is not extended.5",
    )

    i18n = read("overlay/ExtendedI18n.js")
    for locale in ("ja:", "zh:", "en:"):
        require(locale in i18n, f"canonical locale missing: {locale}")
    for marker in (
        "diagnosticsOverall:",
        "diagnosticNativeReact:",
        "diagnosticForeground:",
        "notificationMonitorChannel:",
    ):
        require(marker in i18n, f"canonical localization marker missing: {marker}")

    panel = read("overlay/ExtendedControlPanel.js")
    for marker in (
        "runEventBridgeProbe",
        "runNativeAutoDebug",
        "Clipboard.setString(dialog.copy)",
        "planShizukuSetup(status)",
        "createStyles(useColorScheme() === 'dark')",
    ):
        require(marker in panel, f"canonical control-panel marker missing: {marker}")

    shizuku_policy = read("overlay/ShizukuSetupPolicy.js")
    for marker in (
        "already-configured",
        "not-installed",
        "not-running",
        "permission-required",
        "ready-to-apply",
    ):
        require(marker in shizuku_policy, f"canonical Shizuku state missing: {marker}")

    inbound_policy = read("overlay/InboundErrorPolicy.js")
    for marker in (
        "encryption-mismatch",
        "createInboundErrorCoalescer",
        "shouldReport: false",
    ):
        require(marker in inbound_policy, f"canonical inbound-error marker missing: {marker}")

    queue = read("overlay/DurableOutboundQueue.js")
    for marker in (
        "createDurableOutboundQueue",
        "enqueue(content, type, shouldEnqueue = null)",
        "acknowledge(id)",
        "recordFailure(id, error)",
        "snapshot()",
        "clear()",
        "scopeFingerprint",
    ):
        require(marker in queue, f"canonical outbound queue marker missing: {marker}")
    require(
        "expired > 0 || state !== raw || normalized" not in queue,
        "cross-scope queue read overwrite returned",
    )

    detached = read("overlay/DetachedTaskSupervisor.js")
    for marker in (
        "createDetachedTaskSupervisor",
        "Promise.resolve()",
        ".catch(() => undefined)",
    ):
        require(marker in detached, f"canonical detached-task supervisor marker missing: {marker}")

    signaling = read("overlay/P2PSignalingValidation.js")
    for marker in (
        "MAX_SIGNALING_MESSAGE_CHARS = 1024 * 1024",
        "MAX_PEERS = 4096",
        "normalizeP2PPeerId",
        "normalizeP2PPeerList",
        "parseP2PSignalingMessage",
    ):
        require(marker in signaling, f"canonical P2P signaling marker missing: {marker}")

    materialize = read("scripts/materialize_upstream.sh")
    finalizer_count = materialize.count('python3 "$ROOT_DIR/scripts/finalize_')
    require(
        finalizer_count <= MAX_FINALIZERS,
        f"finalizer count grew to {finalizer_count}; maximum is {MAX_FINALIZERS}",
    )

    # A previously rejected project must never become an input again. Keep its
    # literal out of all user-facing documentation and compare only a digest here,
    # so future handoffs cannot accidentally promote it by name.
    excluded_literal = "GoodLight999/" + "Trash-ClipCascade"
    excluded_digest = hashlib.sha256(excluded_literal.encode("utf-8")).hexdigest()
    require(
        excluded_digest == "fc4a330962e6551d6447b26270ec94967209907509fd0e8787fffa869eb9e095",
        "permanent-exclusion digest changed unexpectedly",
    )
    for relative in (
        "README.md",
        "HANDOFF.md",
        "WORKLOG.md",
        "docs/TEST_PLAN.md",
        ".github/workflows/android-ci.yml",
    ):
        require(
            excluded_literal not in read(relative),
            f"permanently excluded project reference in {relative}",
        )

    handoff = read("HANDOFF.md")
    exclusion_rule = (
        "過去の破綻した派生物、archive、trash、別リポジトリを資料として復活させない。"
    )
    require(
        handoff.count(exclusion_rule) == 1,
        "HANDOFF must contain exactly one generalized permanent-exclusion rule",
    )

    print(
        "Canonical source cleanliness validated: no OTP/version staging, "
        "canonical i18n, migrated stop-safe UTF-8 queue, bounded signaling and "
        "detached supervision complete, no excluded-project input, "
        f"finalizers={finalizer_count}/{MAX_FINALIZERS}"
    )


if __name__ == "__main__":
    main()

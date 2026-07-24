#!/usr/bin/env python3
"""Reject historical patch-chain debt before materialization begins."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> None:
    removed_files = (
        "scripts/finalize_deferred_otp.py",
        "scripts/finalize_accessibility_phase.py",
    )
    for relative in removed_files:
        require(not (ROOT / relative).exists(), f"obsolete pipeline file returned: {relative}")

    generation_files = (
        "scripts/apply_overlay.py",
        "scripts/apply_accessibility_overlay.py",
        "scripts/finalize_shizuku_guidance.py",
        "scripts/materialize_upstream.sh",
    )
    forbidden_generation_tokens = (
        "NotificationCaptureService",
        "OtpExtractor",
        "Notification Access (OTP Sync)",
        "3.2.0-extended.1",
        "versionCode 320001",
        "EXTENDED_SETUP_TEXT",
        "finalize_deferred_otp.py",
        "finalize_accessibility_phase.py",
    )
    for relative in generation_files:
        text = read(relative)
        for token in forbidden_generation_tokens:
            require(token not in text, f"historical staging token {token!r} remained in {relative}")

    for path in sorted((ROOT / "overlay").rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".js", ".tsx", ".kt", ".xml", ".aidl"}:
            continue
        text = path.read_text(encoding="utf-8")
        for token in (
            "NotificationCaptureService",
            "OtpExtractor",
            "Notification Access (OTP Sync)",
            "3.2.0-extended.1",
        ):
            require(token not in text, f"deferred OTP/version staging token {token!r} in {path.relative_to(ROOT)}")

    panel = read("overlay/ExtendedControlPanel.js")
    require(
        "formatDiagnosticsReport(report, text);" in panel,
        "canonical diagnostics must pass the complete locale dictionary",
    )
    require(
        "localizeRuntimeMessage" in panel,
        "canonical status panel must localize runtime messages",
    )
    require(
        "foregroundRecoveryLabel" in panel,
        "canonical status panel must include Foreground Service recovery",
    )
    for stale in (
        "`Package: ${status.packageName}`",
        "`Service requested: ${status.serviceRequested}`",
        "`Connection: ${status.connectionStatus",
    ):
        require(stale not in panel, f"hard-coded English status field remained: {stale}")

    materialize = read("scripts/materialize_upstream.sh")
    finalizer_count = materialize.count('python3 "$ROOT_DIR/scripts/finalize_')
    require(
        finalizer_count <= 30,
        f"finalizer count grew to {finalizer_count}; consolidate instead of adding patches",
    )

    forbidden_repo = "GoodLight999/Trash-ClipCascade"
    for relative in (
        "README.md",
        "WORKLOG.md",
        "docs/TEST_PLAN.md",
        ".github/workflows/android-ci.yml",
    ):
        require(forbidden_repo not in read(relative), f"forbidden repository reference in {relative}")
    handoff = read("HANDOFF.md")
    require(
        handoff.count(forbidden_repo) == 1 and "永久除外" in handoff,
        "HANDOFF must contain exactly one explicit permanent-exclusion rule",
    )

    print(
        "Canonical source cleanliness validated: no OTP/version staging, "
        f"no forbidden-project input, finalizers={finalizer_count}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT_DIR/UPSTREAM.lock"

DESTINATION="${1:-$ROOT_DIR/build/mobile}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

printf 'Materializing %s@%s\n' "$UPSTREAM_REPOSITORY" "$UPSTREAM_COMMIT"
git -C "$WORK_DIR" init --quiet upstream
git -C "$WORK_DIR/upstream" remote add origin \
  "https://github.com/${UPSTREAM_REPOSITORY}.git"
git -C "$WORK_DIR/upstream" sparse-checkout init --cone
git -C "$WORK_DIR/upstream" sparse-checkout set "$UPSTREAM_MOBILE_PATH"
git -C "$WORK_DIR/upstream" fetch --quiet --depth=1 origin "$UPSTREAM_COMMIT"
git -C "$WORK_DIR/upstream" checkout --quiet --detach FETCH_HEAD

actual_commit="$(git -C "$WORK_DIR/upstream" rev-parse HEAD)"
if [[ "$actual_commit" != "$UPSTREAM_COMMIT" ]]; then
  printf 'Pinned commit mismatch: expected %s, got %s\n' \
    "$UPSTREAM_COMMIT" "$actual_commit" >&2
  exit 1
fi

rm -rf "$DESTINATION"
mkdir -p "$DESTINATION"
cp -a "$WORK_DIR/upstream/$UPSTREAM_MOBILE_PATH/." "$DESTINATION/"

python3 "$ROOT_DIR/scripts/apply_overlay.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/apply_accessibility_overlay.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_deferred_otp.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_shizuku_guidance.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_accessibility_phase.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/fix_upstream_js.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_truthful_p2p_status.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_transport_retry_safety.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_outbound_queue.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_outbound_queue_hardening.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_listener_queue_safety.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_event_delivery_order.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_p2p_fragment_reliability.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_p2p_idempotency.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_p2p_backpressure.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_p2p_compatibility.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_p2p_compatibility_helpers.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_p2p_compatibility_signaling.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_p2s_echo_ack.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_p2s_decrypt_error.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_outbound_file_uris.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_restart_reliability.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_capture_runtime_recovery.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_reliability_diagnostics.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_auto_debug.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_foreground_service_reliability.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_single_foreground_runtime.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_foreground_heartbeat.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_foreground_loop_supervision.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_extended_product_ui.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_product_ui_cleanup.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_service_button_state.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_runtime_message_localization.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_control_panel_localization.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_runtime_recovery_localization.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/finalize_android_lint.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/validate_materialized_android.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/validate_active_diagnostics.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/validate_service_and_p2p_controls.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/validate_android_share_intents.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/validate_product_localization.py" "$DESTINATION"
python3 "$ROOT_DIR/scripts/validate_final_scope.py" "$DESTINATION"
printf 'Materialized and validated patched Android source at %s\n' "$DESTINATION"

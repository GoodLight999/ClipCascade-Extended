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
python3 "$ROOT_DIR/scripts/fix_upstream_js.py" "$DESTINATION"
printf 'Materialized patched Android source at %s\n' "$DESTINATION"

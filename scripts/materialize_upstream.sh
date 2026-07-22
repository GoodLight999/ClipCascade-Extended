#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT_DIR/UPSTREAM.lock"

DESTINATION="${1:-$ROOT_DIR/build/mobile}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

printf 'Materializing %s@%s\n' "$UPSTREAM_REPOSITORY" "$UPSTREAM_COMMIT"
git clone --quiet --filter=blob:none --no-checkout \
  "https://github.com/${UPSTREAM_REPOSITORY}.git" "$WORK_DIR/upstream"
git -C "$WORK_DIR/upstream" sparse-checkout init --cone
git -C "$WORK_DIR/upstream" sparse-checkout set "$UPSTREAM_MOBILE_PATH"
git -C "$WORK_DIR/upstream" checkout --quiet --detach "$UPSTREAM_COMMIT"

rm -rf "$DESTINATION"
mkdir -p "$DESTINATION"
cp -a "$WORK_DIR/upstream/$UPSTREAM_MOBILE_PATH/." "$DESTINATION/"

python3 "$ROOT_DIR/scripts/apply_overlay.py" "$DESTINATION"
printf 'Materialized patched Android source at %s\n' "$DESTINATION"

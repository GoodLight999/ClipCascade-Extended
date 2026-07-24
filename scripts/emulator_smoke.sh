#!/usr/bin/env bash
set -Eeuo pipefail

api="${1:?Android API level is required}"
workspace="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"
package='com.clipcascade.extended'
component='com.clipcascade.extended/com.clipcascade.MainActivity'
apk="$workspace/artifact/dist/ClipCascade-Extended.apk"
out="$workspace/emulator-smoke/api-$api"
mkdir -p "$out"

checkpoint() {
  printf '%s\n' "$1" | tee "$out/checkpoint.txt"
}

collect_evidence() {
  set +e
  adb shell dumpsys package "$package" > "$out/package.txt" 2>&1
  adb shell dumpsys activity exit-info "$package" > "$out/exit-info.txt" 2>&1
  adb logcat -d -v threadtime > "$out/logcat.txt" 2>&1
  adb exec-out screencap -p > "$out/final-screen.png" 2>/dev/null
  adb shell pidof "$package" | tr -d '\r' > "$out/final-pid.txt" 2>&1
  set -e
}

on_exit() {
  local status=$?
  trap - EXIT
  collect_evidence
  printf '%s\n' "$status" > "$out/script-exit-code.txt"
  exit "$status"
}
trap on_exit EXIT

run_activity() {
  local label="$1"
  shift
  local output="$out/$label.txt"
  adb shell am start -W "$@" > "$output" 2>&1
  cat "$output"
  grep -Fq 'Status: ok' "$output"
  sleep 2
  local pid
  pid="$(adb shell pidof "$package" | tr -d '\r')"
  test -n "$pid"
  printf '%s\n' "$pid" > "$out/$label-pid.txt"
}

test -s "$apk"
checkpoint 'emulator-ready'
adb wait-for-device
adb shell getprop ro.build.version.sdk | tr -d '\r' | tee "$out/device-api.txt"
grep -Fxq "$api" "$out/device-api.txt"
adb shell getprop ro.product.cpu.abi | tr -d '\r' | tee "$out/device-abi.txt"
adb logcat -c

checkpoint 'installing'
adb install -r "$apk" | tee "$out/install.txt"
grep -Fq 'Success' "$out/install.txt"
adb shell pm path "$package" | tee "$out/package-path.txt"
grep -Fq 'package:' "$out/package-path.txt"

checkpoint 'launch-light'
adb shell cmd uimode night no > "$out/uimode-light.txt" 2>&1 || true
adb shell am force-stop "$package"
run_activity launch-light -n "$component"

checkpoint 'share-text'
run_activity share-text \
  -a android.intent.action.SEND \
  -t text/plain \
  --es android.intent.extra.TEXT "ClipCascade CI share API $api" \
  -n "$component"

checkpoint 'process-text'
run_activity process-text \
  -a android.intent.action.PROCESS_TEXT \
  -t text/plain \
  --es android.intent.extra.PROCESS_TEXT "ClipCascade CI process text API $api" \
  --ez android.intent.extra.PROCESS_TEXT_READONLY true \
  -n "$component"

checkpoint 'launch-dark'
adb shell cmd uimode night yes > "$out/uimode-dark.txt" 2>&1 || true
adb shell am force-stop "$package"
run_activity launch-dark -n "$component"
sleep 2

checkpoint 'collecting-evidence'
collect_evidence

if grep -Eq 'reason=REASON_(CRASH|CRASH_NATIVE|ANR)' "$out/exit-info.txt"; then
  echo 'ClipCascade abnormal exit detected by ActivityManager' >&2
  exit 1
fi
if grep -Fq 'ANR in com.clipcascade.extended' "$out/logcat.txt"; then
  echo 'ClipCascade ANR detected in logcat' >&2
  exit 1
fi
if grep -A8 -F 'FATAL EXCEPTION' "$out/logcat.txt" | grep -Fq 'Process: com.clipcascade.extended'; then
  echo 'ClipCascade fatal exception detected in logcat' >&2
  exit 1
fi

checkpoint 'passed'
trap - EXIT
collect_evidence
printf '0\n' > "$out/script-exit-code.txt"

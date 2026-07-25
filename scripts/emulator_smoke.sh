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

assert_no_abnormal_exit() {
  local label="$1"
  local exit_info="$out/$label-exit-info.txt"
  local logcat="$out/$label-logcat.txt"
  adb shell dumpsys activity exit-info "$package" > "$exit_info" 2>&1 || true
  adb logcat -d -v threadtime > "$logcat" 2>&1
  if grep -Eq 'reason=REASON_(CRASH|CRASH_NATIVE|ANR)' "$exit_info"; then
    echo "ClipCascade abnormal exit detected after $label" >&2
    return 1
  fi
  if grep -Fq 'ANR in com.clipcascade.extended' "$logcat"; then
    echo "ClipCascade ANR detected after $label" >&2
    return 1
  fi
  if grep -A8 -F 'FATAL EXCEPTION' "$logcat" | grep -Fq 'Process: com.clipcascade.extended'; then
    echo "ClipCascade fatal exception detected after $label" >&2
    return 1
  fi
  if grep -Eq \
    'ReactNativeHost[.]getReactInstanceManager[(][)] on a null object reference|StatusBar[.]_updatePropsStack: Unexpected color|ForegroundServiceStartNotAllowedException|BadForegroundServiceNotificationException|RemoteServiceException.*foreground|AEADBadTagException|Encryption must be enabled on all devices if enabled' \
    "$logcat"; then
    echo "Known ClipCascade regression signature detected after $label" >&2
    return 1
  fi
}

capture_ui() {
  local label="$1"
  adb exec-out screencap -p > "$out/$label-screen.png"
  adb shell uiautomator dump "/sdcard/$label-window.xml" > "$out/$label-uiautomator.txt" 2>&1 || true
  adb pull "/sdcard/$label-window.xml" "$out/$label-window.xml" > "$out/$label-uiautomator-pull.txt" 2>&1 || true
}

assert_log_marker() {
  local label="$1"
  local marker="$2"
  grep -Fq "$marker" "$out/$label-logcat.txt" || {
    echo "Expected runtime evidence missing after $label: $marker" >&2
    return 1
  }
}

run_activity() {
  local label="$1"
  shift
  local output="$out/$label.txt"
  adb shell am start -W "$@" > "$output" 2>&1
  cat "$output"
  grep -Fq 'Status: ok' "$output"
  sleep 3
  assert_no_abnormal_exit "$label"
  local pid
  pid="$(adb shell pidof "$package" | tr -d '\r')"
  test -n "$pid"
  printf '%s\n' "$pid" > "$out/$label-pid.txt"
}

create_media_image() {
  local local_png="$out/share-probe.png"
  local remote_png="/sdcard/Download/ClipCascade_CI_share_API_$api.png"
  printf '%s' \
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Z2WQAAAAASUVORK5CYII=' \
    | base64 --decode > "$local_png"
  adb push "$local_png" "$remote_png" > "$out/share-image-push.txt"

  local inserted
  inserted="$(adb shell content insert \
    --uri content://media/external/images/media \
    --bind _display_name:s:"ClipCascade_CI_share_API_$api.png" \
    --bind mime_type:s:image/png \
    --bind relative_path:s:Pictures | tr -d '\r')"
  printf '%s\n' "$inserted" > "$out/share-image-insert.txt"
  local uri="${inserted##* }"
  [[ "$uri" == content://* ]]
  adb shell "content write --uri '$uri' < '$remote_png'" > "$out/share-image-write.txt" 2>&1
  printf '%s\n' "$uri"
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
adb shell pm grant "$package" android.permission.POST_NOTIFICATIONS \
  > "$out/grant-notifications.txt" 2>&1 || true
adb shell cmd activity clear-exit-info "$package" > "$out/clear-exit-info.txt" 2>&1 || true

checkpoint 'launch-light'
adb shell cmd uimode night no > "$out/uimode-light.txt" 2>&1 || true
adb shell am force-stop "$package"
run_activity launch-light -n "$component"
capture_ui launch-light
if grep -Eqi 'notification permission|send you notifications|通知を送信|发送通知' \
  "$out/launch-light-window.xml" 2>/dev/null; then
  echo 'Notification permission dialog obscured the application UI' >&2
  exit 1
fi

checkpoint 'share-text'
run_activity share-text \
  -a android.intent.action.SEND \
  -t text/plain \
  --es android.intent.extra.TEXT "ClipCascade_CI_share_API_$api" \
  -n "$component"
assert_log_marker share-text 'Native event accepted: event=SHARED_TEXT'

checkpoint 'process-text'
run_activity process-text \
  -a android.intent.action.PROCESS_TEXT \
  -t text/plain \
  --es android.intent.extra.PROCESS_TEXT "ClipCascade_CI_process_text_API_$api" \
  --ez android.intent.extra.PROCESS_TEXT_READONLY true \
  -n "$component"
assert_log_marker process-text 'Native event accepted: event=SHARED_TEXT'

checkpoint 'share-image'
image_uri="$(create_media_image)"
printf '%s\n' "$image_uri" > "$out/share-image-uri.txt"
run_activity share-image \
  -a android.intent.action.SEND \
  -t image/png \
  --eu android.intent.extra.STREAM "$image_uri" \
  --grant-read-uri-permission \
  -n "$component"
assert_log_marker share-image 'Shared payload staged: event=SHARED_IMAGE;count=1'
assert_log_marker share-image 'Native event accepted: event=SHARED_IMAGE'

checkpoint 'background-lifecycle'
adb shell input keyevent KEYCODE_HOME
sleep 6
assert_no_abnormal_exit background-lifecycle
background_pid="$(adb shell pidof "$package" | tr -d '\r')"
test -n "$background_pid"
printf '%s\n' "$background_pid" > "$out/background-lifecycle-pid.txt"

checkpoint 'launch-dark'
adb shell cmd uimode night yes > "$out/uimode-dark.txt" 2>&1 || true
adb shell am force-stop "$package"
run_activity launch-dark -n "$component"
capture_ui launch-dark
sleep 2

checkpoint 'collecting-evidence'
collect_evidence
assert_no_abnormal_exit final

cat > "$out/summary.json" <<EOF
{
  "api": $api,
  "package": "$package",
  "install": "passed",
  "launchLight": "passed",
  "shareText": "passed",
  "processText": "passed",
  "shareImage": "passed",
  "backgroundLifecycle": "passed",
  "launchDark": "passed"
}
EOF

checkpoint 'passed'
trap - EXIT
collect_evidence
printf '0\n' > "$out/script-exit-code.txt"

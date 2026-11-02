#!/usr/bin/env bash
# Activates a face, screenshots it, and reports the face renderer's memory.
# Usage: scripts/check_face.sh <package> [--ambient]
#   --ambient  also puts the watch to sleep and screenshots always-on mode (if the watch allows it)
set -euo pipefail
PKG="${1:?usage: check_face.sh <package> [--ambient]}"
TS=$(date +%Y%m%d-%H%M%S)
adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface --es watchFaceId "$PKG" >/dev/null || true
adb shell input keyevent KEYCODE_WAKEUP
sleep 4
adb exec-out screencap -p > "face-$TS.png"
echo "screenshot: face-$TS.png"

echo "renderer memory (PSS):"
for p in $(adb shell ps -A -o NAME | tr -d '\r' | grep -iE 'watchface|wallpaper' | sort -u); do
  pss=$(adb shell dumpsys meminfo "$p" | tr -d '\r' | grep -E 'TOTAL PSS:|^ +TOTAL ' | head -1 | awk '{print $3}')
  echo "  $p: ${pss:-?} KB"
done

if [[ "${2:-}" == "--ambient" ]]; then
  adb shell input keyevent KEYCODE_SLEEP
  sleep 4
  adb exec-out screencap -p > "ambient-$TS.png"
  adb shell input keyevent KEYCODE_WAKEUP
  echo "always-on screenshot: ambient-$TS.png  (check: python3 -I scripts/aod_check.py ambient-$TS.png)"
fi

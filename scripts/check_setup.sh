#!/usr/bin/env bash
# Checks everything this skill needs and says how to fix what's missing.
# Usage: scripts/check_setup.sh             check only
#        scripts/check_setup.sh --install   also create the debug signing key if it's missing
set -uo pipefail
INSTALL=0; [[ "${1:-}" == "--install" ]] && INSTALL=1
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
MISSING=0
ok() { printf '  ok    %s\n' "$1"; }
bad() { printf '  MISS  %s\n        fix: %s\n' "$1" "$2"; MISSING=1; }

echo "Checking tools for the wearos-watchface skill"
command -v adb >/dev/null && ok "adb" \
  || bad "adb" "install Android platform-tools (Android SDK) or your OS package 'android-tools'"
python3 -I -c "import PIL, numpy" 2>/dev/null && ok "python3 with Pillow and numpy" \
  || bad "Pillow / numpy" "python3 -m pip install --user pillow numpy  (or your OS packages, or a virtual env)"
BT=$(ls -d "$SDK"/build-tools/* 2>/dev/null | sort -V | tail -1)
if [[ -n "$BT" && -x "$BT/aapt2" && -x "$BT/apksigner" && -x "$BT/zipalign" ]]; then
  ok "Android SDK build-tools ($(basename "$BT"))"
else
  bad "Android SDK build-tools" "install with Android Studio's SDK Manager or sdkmanager \"build-tools;35.0.0\"; set ANDROID_HOME"
fi
API=$(ls "$SDK"/platforms 2>/dev/null | sed 's/android-//' | grep -E '^[0-9]+$' | sort -n | tail -1)
[[ -n "$API" && "$API" -ge 33 ]] && ok "Android platform API $API" \
  || bad "Android platform API 33+" "sdkmanager \"platforms;android-35\""
KS="$HOME/.android/debug.keystore"
if [[ -f "$KS" ]]; then
  ok "signing key ($KS)"
elif [[ $INSTALL -eq 1 ]] && command -v keytool >/dev/null; then
  mkdir -p "$HOME/.android"
  keytool -genkeypair -keystore "$KS" -storepass android -keypass android -alias androiddebugkey \
    -dname "CN=Android Debug" -keyalg RSA -validity 10000 >/dev/null 2>&1 && ok "signing key created ($KS)"
else
  bad "signing key" "run this script with --install (needs Java's keytool)"
fi
if adb devices 2>/dev/null | grep -qE '\sdevice$'; then
  ok "a device is connected over adb"
else
  printf '  info  no watch connected yet: turn on Wireless debugging on the watch, then\n        adb pair <ip:pair-port> <code>  and  adb connect <ip:port>\n'
fi
[[ $MISSING -eq 0 ]] && echo "Ready." || echo "Fix the MISS lines above, then run this again."
exit $MISSING

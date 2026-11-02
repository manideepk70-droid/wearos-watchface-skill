#!/usr/bin/env bash
# Builds and signs this watch face APK with plain SDK tools (no Gradle).
# Usage: ./build.sh            -> build/face.apk
#        ./build.sh install    -> also installs it on the connected watch (adb)
# Optional env: ANDROID_HOME, BUILD_TOOLS (version folder), PLATFORM_API, KEYSTORE,
#               KS_PASS, KEY_ALIAS, VERSION_CODE
set -euo pipefail
cd "$(dirname "$0")"

SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
BT="$SDK/build-tools/${BUILD_TOOLS:-$(ls "$SDK/build-tools" | sort -V | tail -1)}"
PLATFORM="$SDK/platforms/android-${PLATFORM_API:-$(ls "$SDK/platforms" | sed 's/android-//' | grep -E '^[0-9]+$' | sort -n | tail -1)}/android.jar"
KEYSTORE="${KEYSTORE:-$HOME/.android/debug.keystore}"
KS_PASS="${KS_PASS:-android}"
KEY_ALIAS="${KEY_ALIAS:-androiddebugkey}"
VC="${VERSION_CODE:-1}"

rm -rf build && mkdir -p build
"$BT/aapt2" compile --dir res -o build/res.zip
"$BT/aapt2" link -o build/unsigned.apk -I "$PLATFORM" \
  --manifest AndroidManifest.xml build/res.zip \
  --min-sdk-version 33 --target-sdk-version 34 \
  --version-code "$VC" --version-name "1.0.$VC"
"$BT/zipalign" -f -p 4 build/unsigned.apk build/aligned.apk
"$BT/apksigner" sign --ks "$KEYSTORE" --ks-pass "pass:$KS_PASS" --key-pass "pass:$KS_PASS" \
  --ks-key-alias "$KEY_ALIAS" --out build/face.apk build/aligned.apk
echo "built: build/face.apk ($(stat -c %s build/face.apk) bytes)"

if [[ "${1:-}" == "install" ]]; then
  adb install -r build/face.apk
fi

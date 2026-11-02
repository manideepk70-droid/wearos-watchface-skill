#!/usr/bin/env bash
# Restores what backup.sh saved.
# Usage: scripts/restore.sh <backup-dir> [--remove <custom-package>] [--activate <package>] [--project <dir>]
#   --remove     uninstall the custom face this skill installed
#   --activate   switch the watch to this face package (Watch Face Format faces)
#   --project    unpack the saved project into <dir>
set -euo pipefail
B="${1:?usage: restore.sh <backup-dir> [--remove pkg] [--activate pkg] [--project dir]}"; shift
REMOVE= ACTIVATE= PROJECT=
while [[ $# -gt 0 ]]; do
  case "$1" in
    --remove) REMOVE="$2"; shift 2 ;;
    --activate) ACTIVATE="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
adb get-state >/dev/null 2>&1 || { echo "No device on adb. Connect the watch first." >&2; exit 1; }

for d in "$B"/apks/*/; do
  [[ -d "$d" ]] || continue
  pkg=$(basename "$d")
  if adb shell pm path "$pkg" >/dev/null 2>&1; then
    echo "already installed: $pkg"
  else
    echo "reinstalling: $pkg"
    adb install-multiple -r "$d"*.apk
  fi
done

if [[ -n "$REMOVE" ]]; then
  echo "removing: $REMOVE"
  adb uninstall "$REMOVE" || true
fi

if [[ -n "$ACTIVATE" ]]; then
  adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
    --es operation set-watchface --es watchFaceId "$ACTIVATE" >/dev/null
  echo "asked the watch to show $ACTIVATE"
else
  echo "To get your old face back, long-press the watch face and pick the one in $B/active-face.png"
fi

if [[ -n "$PROJECT" && -f "$B/project.tar.gz" ]]; then
  mkdir -p "$PROJECT" && tar -xzf "$B/project.tar.gz" -C "$PROJECT"
  echo "project unpacked into $PROJECT"
fi

#!/usr/bin/env bash
# Backs up a Wear OS watch's faces before you change anything (and a face project, if given).
# Usage: scripts/backup.sh <backup-dir> [project-dir]
#
# Saves into <backup-dir>:
#   device.txt          model, Android version, screen size
#   active-face.png     screenshot of the face that is showing now
#   wallpaper.txt       what the watch reports as the active face service
#   faces.txt           third-party watch face packages, one per line
#   apks/<package>/     their APK files, for restore.sh
#   project.tar.gz      the face project (optional)
set -euo pipefail
OUT="${1:?usage: backup.sh <backup-dir> [project-dir]}"
PROJECT="${2:-}"
adb get-state >/dev/null 2>&1 || { echo "No device on adb. Connect the watch first." >&2; exit 1; }
mkdir -p "$OUT/apks"
sh_() { adb shell "$@" | tr -d '\r'; }

{
  echo "backup_date: $(date -Iseconds)"
  echo "model: $(sh_ getprop ro.product.model)"
  echo "android: $(sh_ getprop ro.build.version.release) (sdk $(sh_ getprop ro.build.version.sdk))"
  echo "$(sh_ wm size)"
  echo "$(sh_ wm density)"
} > "$OUT/device.txt"

adb exec-out screencap -p > "$OUT/active-face.png" || true
sh_ dumpsys wallpaper > "$OUT/wallpaper.txt" 2>&1 || true

: > "$OUT/faces.txt"
for pkg in $(sh_ pm list packages -3 | cut -d: -f2); do
  info=$(sh_ dumpsys package "$pkg")
  # Watch Face Format packages have no code; older faces are wallpaper services.
  if ! grep -q 'pkgFlags=\[.*HAS_CODE' <<<"$info" || grep -q 'android.service.wallpaper' <<<"$info"; then
    mkdir -p "$OUT/apks/$pkg"
    for p in $(sh_ pm path "$pkg" | cut -d: -f2); do adb pull "$p" "$OUT/apks/$pkg/" >/dev/null; done
    if unzip -p "$OUT/apks/$pkg/base.apk" AndroidManifest.xml 2>/dev/null | python3 -I -c '
import sys; d = sys.stdin.buffer.read()
sys.exit(0 if (b"watchface" in d or "watchface".encode("utf-16-le") in d or b"wallpaper" in d or "wallpaper".encode("utf-16-le") in d) else 1)'; then
      echo "$pkg" >> "$OUT/faces.txt"
    else
      rm -rf "$OUT/apks/$pkg"
    fi
  fi
done

if [[ -n "$PROJECT" ]]; then
  tar -czf "$OUT/project.tar.gz" --exclude=build -C "$(dirname "$PROJECT")" "$(basename "$PROJECT")"
fi
echo "Backup saved to $OUT: $(wc -l < "$OUT/faces.txt") face package(s), screenshot of the current face."

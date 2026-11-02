---
name: wearos-watchface
description: Design, build, install and battery-tune a custom Wear OS watch face (Watch Face Format, no code, no Gradle) from the user's theme reference images, with backup and restore of the watch's faces. Use when the user wants a custom or themed face for a Wear OS watch, wants an existing Wear OS face to use less battery or memory, or wants to back up or restore the faces on a Wear OS watch.
---

# Wear OS watch face

Builds a Watch Face Format (WFF) face: an APK with no code. The watch's own renderer
draws `res/raw/watchface.xml`, which keeps battery and memory use low. Shows time, date,
steps and battery by default; these exist on every Wear OS watch.

Paths below are relative to this skill's folder (`scripts/`, `templates/`, `references/`).

## Ground rules

- Only work on a watch the user owns, through their own adb connection.
- Back up before installing anything (step 3). Never uninstall or change faces the user
  didn't ask about.
- Reference images are the user's responsibility. If they show characters, logos or art
  the user may not own, say once that the face is for private use and not for publishing,
  then carry on. Never write character, brand or app names into files that get shared
  (README, store listing) unless the user says they hold the rights.
- Point to `DISCLAIMER.md` the first time you run commands on their device.

## 0. Responsibility (always first, before any command on a device)

Show this to the user, word for word, and wait for "I agree". If they don't agree, stop.

> **Before we start**
> - You are responsible for what this skill does on your devices.
> - Use it only on your own phone and watch.
> - Something could go wrong, so I'll make a backup first.
> - The people who made this skill are not responsible.
>
> Type **I agree** to continue.

Save the date and their reply at the top of `<project>/NOTES.md`. Before each step that
changes a device (install, upload, uninstall), ask a quick "OK to go ahead?".

## 1. Gather inputs (ask once, only for what's missing)

| Input | Example | Notes |
|---|---|---|
| Theme name | "Midnight Sail" | becomes the label and package name |
| Reference images | `~/refs/art.png` | 1+ images: mood, palette, lettering, main artwork |
| Watch model | "Example Watch S1" | read it from the device in step 2 if unknown |
| Screen shape and size | round 450 x 450, square 410 x 410, rectangle 410 x 502 | `adb shell wm size` gives pixels; ask for the shape if unsure |
| Connection | `192.168.1.20:41563` or USB | watch's Wireless debugging address; pairing code if not yet paired |
| Data to show | time, date, steps, battery | default; others only if asked |
| Priority | battery / balanced / looks | default: balanced |

Write them to `face.config.json` (copy `face.config.example.json`).

## 2. Check tools and connect

- Needs: `adb`, Android SDK build-tools (`aapt2`, `zipalign`, `apksigner`), a platform
  `android.jar` (API 33+), `python3` with Pillow and numpy, and `~/.android/debug.keystore`.
  If the keystore is missing:
  `keytool -genkeypair -keystore ~/.android/debug.keystore -storepass android -keypass android -alias androiddebugkey -dname "CN=Android Debug" -keyalg RSA -validity 10000`
- Pair/connect: `adb pair <ip:pair-port> <code>` then `adb connect <ip:port>`.
- Identify: `adb shell getprop ro.product.model`, `adb shell getprop ro.build.version.sdk`
  (WFF v1 needs 33+), `adb shell wm size`. Shape: round, square or rectangle. Equal
  width and height can be round or square, so ask if the user didn't say.

## 3. Back up

`scripts/backup.sh <backup-dir> [project-dir]` saves device info, the active face
(as far as the watch reports it), every third-party watch face APK, and the project.
Tell the user where it went. `scripts/restore.sh <backup-dir>` puts it back (step 10).

## 4. Design from the reference images

Look at every reference image. Write a short brief (palette as hex, lettering style, focal
art, calm areas where data can sit, what to drop) and the layout: where time, date, steps
and battery go on the design grid (450 wide; a 450 x 450 square centred on the screen
for the data; round screens lose the corners, rectangles gain top and bottom bands). Keep text over calm, high-contrast areas.
If the art has text or numbers baked in, plan to erase them (`references/design.md`).
Show the brief and wait for a yes before building, unless the user said "just build it".

## 5. Scaffold the project

`python3 -I scripts/new_face.py face.config.json <project-dir>` creates a working face
(background image if given, time, date, steps, battery, always-on variant) and
`build.sh`. Build it once as-is to prove the toolchain: `<project-dir>/build.sh`.

## 6. Make it match the theme

- Background: the main artwork, cropped to the screen shape (circle for round; full
  frame for square and rectangle, keeping detail away from rounded corners), at the
  watch's pixel size (not larger). Erase baked-in text; darken under where data sits.
- Lettering: device font (`SYNC_TO_DEVICE`, cheapest) or a bitmap font that matches the
  art: `scripts/fontkit.py` renders digits/letters from any TTF with fill, outline,
  shadow and wear, and prints the `<BitmapFonts>` XML.
- Layout: edit `res/raw/watchface.xml`. Rules and syntax: `references/wff-cheatsheet.md`.

## 7. Battery and memory pass

Go through `references/battery-and-memory.md` and fix every miss before installing.
The non-negotiables: always-on mode shows little more than the time, dim and on black;
no seconds unless asked; no looping animations; decoded image memory kept small.

## 8. Build, install, look at it

- `<project-dir>/build.sh install` builds, signs and installs.
- Activate: `adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE --es operation set-watchface --es watchFaceId <package>`
  (if the watch ignores it, ask the user to pick the face by long-pressing the current one).
- Screenshot: `adb exec-out screencap -p > shot.png`, then look at it. Compare with the
  reference images and fix spacing, contrast and clipping.

## 9. Measure

`scripts/check_face.sh <package>` reports the face renderer's memory (PSS) and saves a
screenshot; `python3 -I scripts/aod_check.py <ambient-screenshot.png>` reports the share
of lit pixels in always-on mode (aim at or below 15%). Report both numbers to the user.

## 10. Restore

If the user wants their old setup back: `scripts/restore.sh <backup-dir> [--remove <package>]`.
It reinstalls the saved face APKs, optionally removes the custom face, and re-activates the
previous face when the backup recorded it (otherwise it tells the user to pick it).

## Finish

Tell the user: what's on the watch, renderer memory and always-on lit %, where the project
and backup are, and how to rebuild (`./build.sh install`). Keep it short.

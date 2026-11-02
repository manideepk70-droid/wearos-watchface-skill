# wearos-watchface (Claude Code skill)

A free, open-source [Claude Code](https://claude.com/claude-code) skill that turns your
theme images into a custom Wear OS watch face, tuned for battery, with backup and
restore of the faces already on your watch.

- **Watch Face Format**: the face is an APK with no code. The watch's own renderer
  draws it, which is the most battery-friendly way to make a Wear OS face.
- **No Gradle, no Android Studio**: plain Android SDK tools.
- **Shows time, date, steps and battery** (on every Wear OS watch); more if you ask.
- **Battery pass built in**: always-on mode checks, memory measurement, lit-pixel check.
- **Backup and restore**: saves your current faces and puts them back.

> **You are responsible for what you do with this skill.** Use it only on your own
> devices. The people who made it are not responsible. Details: [DISCLAIMER.md](DISCLAIMER.md).

## What you need

- A Wear OS 4+ watch (API 33+) with **Developer options → Wireless debugging** on
- A computer with `adb`, the Android SDK build-tools and a platform (API 33+), Python 3
  with `Pillow` and `numpy`, and Claude Code
- One or more theme reference images (art, colours, lettering you like)

## Install: just ask your AI assistant

Paste this into Claude Code:

```
Install the skill from https://github.com/manideepk70-droid/wearos-watchface-skill
by following the "For AI assistants" section of its README.
```

It downloads the skill, checks your computer and tells you if anything is missing.
Then start a new Claude Code session.

Or by hand:
```bash
git clone https://github.com/manideepk70-droid/wearos-watchface-skill ~/.claude/skills/wearos-watchface
~/.claude/skills/wearos-watchface/scripts/check_setup.sh --install
```

## For AI assistants: how to install this skill

Do these steps, then tell the user the result in plain words.

1. **Get the files.** `git clone https://github.com/manideepk70-droid/wearos-watchface-skill ~/.claude/skills/wearos-watchface`
   (already there? `git -C ~/.claude/skills/wearos-watchface pull`). If the user wants it
   for one project only, clone into `<project>/.claude/skills/wearos-watchface` instead.
2. **Check the computer.** Run `~/.claude/skills/wearos-watchface/scripts/check_setup.sh --install`
   and fix each `MISS` line using the `fix:` hint. Ask before installing system packages.
   If `pip` refuses ("externally managed environment"), use the OS packages
   (e.g. `python-pillow`, `python-numpy`) or a virtual environment.
3. **Confirm** that `~/.claude/skills/wearos-watchface/SKILL.md` exists.
4. **Tell the user:** it's installed; start a new Claude Code session; then ask for a face,
   e.g. "Make me a Wear OS watch face from ~/refs/art.png". Show them the short
   disclaimer at the top of `DISCLAIMER.md`.

Don't run anything on a watch while installing.

## Use it

1. On the watch: Settings → Developer options → Wireless debugging → *Pair new device*.
2. On the computer: `adb pair <ip:pair-port> <code>` then `adb connect <ip:port>`.
3. Ask Claude, for example:

> Make me a Wear OS watch face called "Midnight Sail" from `~/refs/sea.png` and
> `~/refs/lettering.png`. My watch is round, 450 x 450, at 192.168.1.20:41563.
> Show time, date, steps and battery. Battery matters most.

Claude will: check your tools, connect, **back up your current faces**, read your images
and propose a design, build the face, install it, screenshot it, measure memory and
always-on brightness, and tell you how to rebuild or restore.

You can fill `face.config.example.json` instead of typing everything:

| Field | Meaning |
|---|---|
| `theme_name` | name shown in the watch's face picker |
| `package` | unique Android package name (optional, derived from the theme name) |
| `watch_model` | your watch model |
| `connection.adb_target` | watch's wireless debugging `ip:port` (or USB serial) |
| `screen.shape` | `round`, `square` or `rectangle` |
| `screen.width` / `screen.height` | screen size in pixels (`adb shell wm size`) |
| `reference_images` | your theme images |
| `background_image` | which image becomes the background (optional) |
| `fields` | `time`, `date`, `steps`, `battery` |
| `hour_format` | `12h` or `24h` |
| `colors` | `time`, `text`, `accent` as `#RRGGBB` |
| `priority` | `battery`, `balanced` or `looks` |

## Backup and restore

```bash
scripts/backup.sh ~/watch-backup [my-face-project]     # before changes
scripts/restore.sh ~/watch-backup --remove com.example.midnightsail.watchface
```
The backup keeps a screenshot of the face you had, your third-party face APKs, and your
project. Restore reinstalls them, removes the custom face if you ask, and switches back
(or tells you which face to pick).

## How it works (and how to make your own skill like it)

```
SKILL.md                     the instructions Claude follows (frontmatter + steps)
scripts/new_face.py          creates a working face project from face.config.json
scripts/fontkit.py           bitmap lettering from any TTF (gradient, outline, shadow, wear)
scripts/backup.sh/restore.sh save and restore the watch's faces
scripts/check_face.sh        screenshot + renderer memory
scripts/aod_check.py         always-on lit-pixel check
scripts/check_setup.sh       checks the computer has everything (used at install)
templates/face/              the face template (manifest, XML, build.sh)
references/                  WFF syntax, battery checklist, design guide
```
A Claude Code skill is a folder with a `SKILL.md` whose frontmatter has a `name` and a
`description` (when to use it). Claude loads the body when a request matches, and can
run the scripts next to it. To make one for another platform, copy this layout, rewrite
the steps, and keep scripts small and testable.

### Other watches

This skill is for Wear OS. Watches that rely on a phone companion app (most fitness and
budget smartwatches) need a different route: learning the watch's own face format and
upload protocol. That is a separate skill, *generic-watchface*.

## Contributing

Issues and pull requests are welcome. Please don't add brand, app or character names,
or copyrighted art, to the repo.

## License

[MIT](LICENSE). See also [DISCLAIMER.md](DISCLAIMER.md).

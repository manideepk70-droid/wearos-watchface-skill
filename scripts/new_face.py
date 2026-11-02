"""Creates a Wear OS watch face project (Watch Face Format) from face.config.json.

Usage: python3 -I scripts/new_face.py face.config.json <project-dir>

The project shows time plus any of date, steps and battery, has a dim always-on mode,
and builds with ./build.sh (plain SDK tools, no Gradle). Edit res/raw/watchface.xml
afterwards to match the theme.
"""
import json
import os
import re
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "templates", "face")
FIELDS = ("date", "steps", "battery")


def die(msg):
    sys.exit("new_face: " + msg)


def argb(c, default):
    """'#RRGGBB' or '#AARRGGBB' -> '#AARRGGBB'."""
    c = (c or default).strip()
    if not re.fullmatch(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})", c):
        die(f"bad colour {c!r}; use #RRGGBB or #AARRGGBB")
    return ("#FF" + c[1:] if len(c) == 7 else c).upper()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower()) or "custom"


def cover(img, tw, th):
    """Scales and centre-crops img to fill tw x th."""
    w, h = img.size
    s = max(tw / w, th / h)
    img = img.resize((max(tw, round(w * s)), max(th, round(h * s))), Image.LANCZOS)
    x, y = (img.width - tw) // 2, (img.height - th) // 2
    return img.crop((x, y, x + tw, y + th))


def main():
    if len(sys.argv) != 3:
        die("usage: new_face.py face.config.json <project-dir>")
    cfg_path, out = sys.argv[1], sys.argv[2]
    cfg = json.load(open(cfg_path))
    base = os.path.dirname(os.path.abspath(cfg_path))

    name = cfg.get("theme_name") or die("theme_name is required")
    pkg = cfg.get("package") or f"com.example.{slug(name)}.watchface"
    if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", pkg):
        die(f"bad package name {pkg!r}")
    screen = cfg.get("screen", {})
    shape = screen.get("shape", "round").lower()
    if shape not in ("round", "square", "rectangle"):
        die(f"screen.shape must be round, square or rectangle, not {shape!r}")
    pw = int(screen.get("width", screen.get("pixels", 450)))
    ph = int(screen.get("height", pw)) if shape == "rectangle" else pw
    gh = round(450 * ph / pw)          # design grid height (width is always 450)
    fields = [f.lower() for f in cfg.get("fields", ["time", *FIELDS])]
    colors = cfg.get("colors", {})
    c_time = argb(colors.get("time"), "#FFFFFF")
    c_text = argb(colors.get("text"), "#B8B8B8")
    c_acc = argb(colors.get("accent"), "#FFC14D")
    hours = "HH" if str(cfg.get("hour_format", "12h")).startswith("24") else "hh"

    if os.path.exists(out) and os.listdir(out):
        die(f"{out} exists and is not empty")
    shutil.copytree(TEMPLATE, out, dirs_exist_ok=True)

    # fill in the template
    xml_path = os.path.join(out, "res", "raw", "watchface.xml")
    xml = open(xml_path).read()
    for f in FIELDS:
        block = re.compile(r"\s*<!--@@%s@@ -->.*?<!-- @@%s@@-->" % (f.upper(), f.upper()), re.S)
        xml = block.sub("" if f not in fields else lambda m: m.group(0), xml)
        xml = xml.replace(f"<!--@@{f.upper()}@@ -->", "").replace(f"<!-- @@{f.upper()}@@-->", "")
    subs = {"@@LABEL@@": name, "@@CLIP@@": "CIRCLE" if shape == "round" else "NONE",
            "@@SHAPE@@": f"{shape} {pw} x {ph} px", "@@H@@": str(gh), "@@DY@@": str((gh - 450) // 2),
            "@@HOURS@@": hours, "@@TIME@@": c_time, "@@TEXT@@": c_text, "@@ACCENT@@": c_acc,
            "@@PACKAGE@@": pkg}
    for path in [xml_path, os.path.join(out, "AndroidManifest.xml"),
                 os.path.join(out, "res", "values", "strings.xml")]:
        s = open(path).read() if path != xml_path else xml
        for k, v in subs.items():
            s = s.replace(k, v.replace("&", "&amp;").replace("<", "&lt;"))
        open(path, "w").write(s)

    # background: the chosen artwork at screen size, or plain black
    bg_src = cfg.get("background_image")
    if bg_src:
        bg = cover(Image.open(os.path.join(base, os.path.expanduser(bg_src))).convert("RGB"), pw, ph)
    else:
        bg = Image.new("RGB", (pw, ph), "black")
    if shape == "round":
        mask = Image.new("L", (pw * 4, ph * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, pw * 4 - 1, ph * 4 - 1), fill=255)
        black = Image.new("RGB", (pw, ph), "black")
        bg = Image.composite(bg, black, mask.resize((pw, ph), Image.LANCZOS))
    draw_dir = os.path.join(out, "res", "drawable-nodpi")
    bg.save(os.path.join(draw_dir, "bg.png"), optimize=True)

    # rough preview for the watch's face picker (replace with a real screenshot later)
    prev = bg.copy()
    d = ImageDraw.Draw(prev)
    k = pw / 450
    dy = (ph - pw) / 2                 # layout square is centred vertically
    try:
        big, small = ImageFont.load_default(size=round(96 * k)), ImageFont.load_default(size=round(22 * k))
    except TypeError:
        big = small = ImageFont.load_default()
    rgb = lambda c: tuple(int(c[i:i + 2], 16) for i in (3, 5, 7))
    d.text((pw / 2, dy + 198 * k), "10:08", font=big, fill=rgb(c_time), anchor="mm")
    if "date" in fields:
        d.text((pw / 2, dy + 119 * k), "Mon  Jan 1", font=small, fill=rgb(c_text), anchor="mm")
    prev.save(os.path.join(draw_dir, "preview.png"), optimize=True)

    os.chmod(os.path.join(out, "build.sh"), 0o755)
    print(f"created {out}  (package {pkg}, {shape} {pw}x{ph}px, fields: time {' '.join(f for f in FIELDS if f in fields)})")
    print(f"next: {out}/build.sh   then   {out}/build.sh install")


if __name__ == "__main__":
    main()

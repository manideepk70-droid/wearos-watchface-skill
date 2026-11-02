"""Renders a bitmap font (one image per character) from any TTF/OTF, styled to match artwork.

As a command (Wear OS): writes PNGs into res/drawable-nodpi and prints the
<BitmapFont> XML to paste inside <BitmapFonts> in watchface.xml:

  python3 -I scripts/fontkit.py --font MyFont.ttf --name tw --chars 0123456789 \
      --cap 50 --px-per-unit 1.07 --top "#FFFFFF" --bottom "#E6DCC4" --outline 3 \
      --shadow 2 --condense 0.85 --wear 0.07 --out <project>/res/drawable-nodpi

  --cap          capital height in design units (450 x 450 grid)
  --px-per-unit  image pixels per design unit (watch pixels / 450; use more for sharper)
  --top/--bottom fill gradient colours; --speck colour of worn spots (with --wear)
  --outline      outline width (design units, dark), --shadow drop shadow offset
  --condense     horizontal squeeze (1 = none), --wear share of worn spots (0-0.2)

As a module: render_set(...) returns {char: float RGBA array} for compositing.
Only use fonts whose licence allows embedding (e.g. SIL OFL).
"""
import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HI = 8  # supersampling
NAMES = {":": "colon", "%": "pct", ",": "comma", ".": "dot", " ": "space", "/": "slash", "-": "dash", "+": "plus"}


def res_name(prefix, ch):
    return f"{prefix}_{NAMES.get(ch, ch.lower())}"


def _speckles(w, h, density, seed):
    rnd = np.random.default_rng(seed)
    fine = rnd.random((max(2, h // (HI // 2)), max(2, w // (HI // 2)))).astype(np.float32)
    f = np.asarray(Image.fromarray(fine * 255).convert("L").filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32)
    m = np.clip((f - np.quantile(f, 1 - density)) / 6.0, 0, 1)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32) / 255


def render_set(font_path, chars, cap, px_per_unit, top=(255, 255, 255), bottom=None, speck=None,
               outline=0.0, outline_color=(10, 7, 4), shadow=0.0, condense=1.0, wear=0.0, seed=1):
    """Returns ({char: HxWx4 float array, RGB 0-255, alpha 0-1}, cap_offset_px).
    cap_offset_px = distance from the image top to the top of the capitals."""
    bottom = bottom or top
    cap_hi = cap * px_per_unit * HI
    probe = ImageFont.truetype(font_path, 200)
    pb = probe.getbbox("0")
    font = ImageFont.truetype(font_path, round(200 * cap_hi / (pb[3] - pb[1])))
    font_top = font.getbbox("0")[1]
    o, sh = outline * px_per_unit * HI, shadow * px_per_unit * HI
    pad_t = o + 2 * HI
    h_px = math.ceil((pad_t + cap_hi + o + sh + 2 * HI) / HI)
    Hh = h_px * HI
    out = {}
    for i, ch in enumerate(chars):
        w_px = max(2, math.ceil((font.getlength(ch) * condense + 2 * o + sh) / HI))
        Ww = w_px * HI
        rgba = np.zeros((Hh, Ww, 4), np.float32)
        if ch != " ":
            raw_w = int(font.getlength(ch) + 2 * o + 4 * HI)
            fm, om = Image.new("L", (raw_w, Hh), 0), Image.new("L", (raw_w, Hh), 0)
            ImageDraw.Draw(fm).text((o + HI, pad_t - font_top), ch, font=font, fill=255)
            if o:
                ImageDraw.Draw(om).text((o + HI, pad_t - font_top), ch, font=font, fill=255,
                                        stroke_width=round(o), stroke_fill=255)
            cw = max(1, round(raw_w * condense))
            fm, om = fm.resize((cw, Hh), Image.LANCZOS), om.resize((cw, Hh), Image.LANCZOS)
            left = max(0, int((Ww - sh - cw) // 2))

            def place(mask, dx=0, dy=0):
                m = np.zeros((Hh, Ww), np.float32)
                a = np.asarray(mask).astype(np.float32) / 255
                x0, y0 = int(left + dx), int(dy)
                x1, y1 = min(Ww, x0 + a.shape[1]), min(Hh, y0 + a.shape[0])
                m[y0:y1, x0:x1] = a[: y1 - y0, : x1 - x0]
                return m

            f_a = place(fm)
            o_a = place(om) if o else f_a
            if sh:
                rgba[..., 3] = place(om if o else fm, sh, sh) * 0.55
            if o:
                rgba[..., :3] = rgba[..., :3] * (1 - o_a[..., None]) + np.array(outline_color) * o_a[..., None]
                rgba[..., 3] = o_a + rgba[..., 3] * (1 - o_a)
            t = np.clip((np.arange(Hh) - pad_t) / cap_hi, 0, 1)[:, None, None]
            col = np.broadcast_to(np.array(top) * (1 - t) + np.array(bottom) * t, (Hh, Ww, 3)).copy()
            if wear:
                sp = _speckles(Ww, Hh, wear, seed * 1000 + i)
                if speck:
                    col = col * (1 - 0.8 * sp[..., None]) + np.array(speck) * 0.8 * sp[..., None]
                else:
                    f_a = f_a * (1 - 0.75 * sp)
            rgba[..., :3] = rgba[..., :3] * (1 - f_a[..., None]) + col * f_a[..., None]
            rgba[..., 3] = f_a + rgba[..., 3] * (1 - f_a)
        pm = rgba.copy()
        pm[..., :3] *= pm[..., 3:4]
        small = np.stack([np.asarray(Image.fromarray(pm[..., c], "F").resize((w_px, h_px), Image.BOX))
                          for c in range(4)], -1)
        al = np.clip(small[..., 3:4], 1e-6, None)
        rgb = np.where(small[..., 3:4] > 1e-4, small[..., :3] / al, 0)
        out[ch] = np.concatenate([np.clip(rgb, 0, 255), np.clip(small[..., 3:4], 0, 1)], -1)
    return out, pad_t / HI


def to_png(rgba):
    a = np.concatenate([rgba[..., :3], rgba[..., 3:4] * 255], -1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def _rgb(s):
    s = s.lstrip("#")
    s = s[-6:]
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--font", required=True)
    p.add_argument("--name", required=True, help="font family name, also the image name prefix (a-z0-9_)")
    p.add_argument("--chars", default="0123456789")
    p.add_argument("--cap", type=float, required=True)
    p.add_argument("--px-per-unit", type=float, default=1.0)
    p.add_argument("--top", default="#FFFFFF")
    p.add_argument("--bottom")
    p.add_argument("--speck")
    p.add_argument("--outline", type=float, default=0)
    p.add_argument("--shadow", type=float, default=0)
    p.add_argument("--condense", type=float, default=1.0)
    p.add_argument("--wear", type=float, default=0)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    glyphs, cap_off = render_set(a.font, a.chars, a.cap, a.px_per_unit, _rgb(a.top),
                                 _rgb(a.bottom) if a.bottom else None, _rgb(a.speck) if a.speck else None,
                                 a.outline, shadow=a.shadow, condense=a.condense, wear=a.wear, seed=a.seed)
    os.makedirs(a.out, exist_ok=True)
    lines = [f'<BitmapFont name="{a.name}">']
    for ch, g in glyphs.items():
        name = res_name(a.name, ch)
        to_png(g).save(os.path.join(a.out, name + ".png"), optimize=True)
        w_u, h_u = round(g.shape[1] / a.px_per_unit), round(g.shape[0] / a.px_per_unit)
        esc = {"&": "&amp;", "<": "&lt;", '"': "&quot;"}.get(ch, ch)
        lines.append(f'  <Character name="{esc}" resource="{name}" width="{w_u}" height="{h_u}"/>')
    lines.append("</BitmapFont>")
    print("\n".join(lines))
    print(f"<!-- caps start {cap_off / a.px_per_unit:.1f} units below the image top; "
          f"use <BitmapFont family=\"{a.name}\" size=\"{round(next(iter(glyphs.values())).shape[0] / a.px_per_unit)}\"/> -->")


if __name__ == "__main__":
    main()

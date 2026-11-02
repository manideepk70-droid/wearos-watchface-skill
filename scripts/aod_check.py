"""Reports how much of an always-on (ambient) screenshot is lit.

Usage: python3 -I scripts/aod_check.py ambient.png [--limit 15] [--shape round|square|rectangle]

lit %   share of pixels that are visibly on (any channel above 24/255)
OPR %   on-pixel ratio: average brightness, what OLED power roughly follows
Aim for lit % at or below the limit (default 15) in always-on mode.
"""
import argparse

import numpy as np
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument("image")
p.add_argument("--limit", type=float, default=15)
p.add_argument("--shape", default="round", choices=["round", "square", "rectangle"])
a = p.parse_args()
img = np.asarray(Image.open(a.image).convert("RGB")).astype(np.float32)
h, w, _ = img.shape
yy, xx = np.mgrid[0:h, 0:w]
if a.shape == "round":
    inside = ((xx - w / 2 + 0.5) / (w / 2)) ** 2 + ((yy - h / 2 + 0.5) / (h / 2)) ** 2 <= 1
else:
    inside = np.ones((h, w), bool)
lit = (img.max(2) > 24) & inside
lum = (0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]) / 255
lit_pct = 100 * lit.sum() / inside.sum()
opr = 100 * lum[inside].mean()
print(f"lit: {lit_pct:.1f}%   OPR: {opr:.1f}%   ({'OK' if lit_pct <= a.limit else 'too bright for always-on'}, limit {a.limit:.0f}%)")

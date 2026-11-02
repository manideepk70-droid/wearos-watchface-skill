# Battery and memory checklist (Wear OS)

Most watches have OLED screens: black pixels are off and cost nothing; bright pixels and
redraws cost power. Image memory is decoded size, not file size.

## Always-on mode (largest effect: it is on for hours)

- [ ] Background is pure black; artwork and images are hidden (`Variant ... alpha 0`).
- [ ] Shows the time, little else. Date is fine if small; no steps, no rings.
- [ ] Time is dimmed (`alpha` around 150-180) or drawn as outlines, in grey or a muted
      colour, never full white fills.
- [ ] Lit pixels at or below **15%** of the screen
      (`python3 -I scripts/aod_check.py ambient.png`).
- [ ] No large static bright areas (burn-in) and nothing updating per second.

## Interactive mode

- [ ] No seconds unless the user asked: a seconds display forces a redraw every second.
- [ ] No looping animations. Play once on wake or tap (`loopCount="1"`), and animate
      only the moving region, not the whole screen.
- [ ] Dark artwork backgrounds beat bright ones; keep large white areas small.
- [ ] Only built-in data (time, date, steps, battery). Every extra data source or
      complication can wake other apps.

## Memory

- [ ] Images at the watch's pixel size. A full-screen image costs width x height x 4
      bytes when decoded (480 x 480 = 0.9 MB) no matter how small the PNG is.
- [ ] Parts hidden with `alpha 0` may still be decoded: don't stack many full-screen
      variants. Prefer one background plus small images.
- [ ] Bitmap fonts: only the characters you need (digits + a few letters), at the size
      they are drawn.
- [ ] Device font (`SYNC_TO_DEVICE`) costs no images at all.

Measure with `scripts/check_face.sh <package>`: it prints the face renderer's PSS.
As a guide from real faces: an all-vector face used about 29 MB; the same renderer with
a full-screen artwork background, bitmap fonts and two short animations used about 39 MB.

## Battery test (optional, slow)

1. Charge to 100%, show the face, leave the watch on the wrist for a normal half day.
2. `adb shell dumpsys batterystats --charged | grep -iE 'screen|discharge'`.
3. Repeat with the watch's default face and compare the drain per hour.

## Priority settings

| Priority | Always-on | Interactive |
|---|---|---|
| battery | dim outline time only | dark art, no animation, device font |
| balanced (default) | dim time + small date | art + bitmap fonts, animations play once |
| looks | dim time + date | richer art; still no loops, no seconds unless asked |

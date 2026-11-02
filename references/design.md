# Turning reference images into a face

## Read the references

For each image note: palette (5-6 hex colours), lettering style (slab, script, stencil,
pixel...), the focal art, calm areas (sky, plain panels, dark corners) and any text or
numbers baked into the art.

## Layout by screen shape

The design grid is 450 wide. The template centres a 450 x 450 "layout" square on the
screen, so the same positions work everywhere:

| Shape | Grid | Safe area for text |
|---|---|---|
| round | 450 x 450, clipped to a circle | inside a circle of radius ~200 around (225, 225) |
| square | 450 x 450 | 20 units from each edge; avoid rounded corners |
| rectangle | 450 x (450 x height / width), e.g. 450 x 551 | the centred square, plus the top and bottom bands for extras |

- Time: biggest element, usually centred between y 130 and 260.
- Date: above the time (y 90-130) or below it.
- Steps and battery: lower half, left and right (around y 270-330), or on panels in the art.
- Put data where the art is calm or darken a soft plate under it (a blurred ellipse at
  40-60% black keeps the art visible and the text readable).

## Preparing the artwork

1. Crop to the screen's shape around the focal art; scale to the watch's pixel size.
2. Erase baked-in text/numbers that the face will draw live: mask them (threshold by
   colour + dilate a few pixels) and fill the hole from its surroundings (repeated
   neighbour averaging works well), then add back a little grain sampled from a clean
   patch so the fill doesn't look smooth.
3. Round screens: cut to a circle with a soft edge. Square and rectangular screens: keep
   the full frame, but keep faces and text away from the rounded corners.
4. Save as PNG (or WebP) in `res/drawable-nodpi/`.

## Lettering that matches the art

- Pick a font with a similar feel (licence must allow embedding, e.g. SIL OFL).
- `scripts/fontkit.py` adds a vertical gradient, dark outline, drop shadow and worn
  specks so digits look painted into the art. Render only the characters you need.
- Check sizes against the art: compare the cap height of the art's own lettering.

## Preview image

`res/drawable-nodpi/preview.png` is shown in the watch's face picker. After the first
install, replace the generated one with a real screenshot
(`adb exec-out screencap -p > preview.png`), resized to the watch's pixel size.

## Private art

If the references contain characters, logos or other people's art, the face is for the
user's own wrist. Don't publish it or put those names into shared files.

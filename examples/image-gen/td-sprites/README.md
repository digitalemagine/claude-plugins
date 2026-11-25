# Case study: game sprites with image-gen

A record of one run of the `image-gen` skill, kept mainly to show the **method**.
Images generated with Gemini (web app, Nov 2026); they carry
Google's SynthID watermark.

The skill builds specs from your own request by default and does not read this folder.
You can still reuse it on purpose: ask Claude to "start from the td-sprites example"
(its style, its spec structure, or the whole spec) and it fetches these files from the
repo. Expect a similar result, not the same one: there is no seed control.

## The request

A military-themed, slightly cartoony tower defence game: one sprite each for a cannon
tower, a laser tower, a missile launcher, its missile, an incoming quadcopter and a
fixed-wing drone.

## What was done

1. **Style first.** `style.json` fixes palette (hex values with roles), outlines, shading,
   proportions, the view angle and a flat `#FF00FF` key background. Enemies get their own
   colour so they read apart from the towers.
2. **One sheet, not six images.** `v1/spec.json` puts all six assets in a 3x2 grid of
   invisible cells (`panels`), so style and scale stay consistent.
3. **Render, then slice.** The sheet was cut into named transparent PNGs:
   ```
   uv run --with pillow python3 plugins/image-gen/skills/image-gen/scripts/slice_sheet.py \
     examples/image-gen/td-sprites/v2/sheet.png --out-dir /tmp/td-sprites \
     --names tower-cannon,tower-laser,tower-missile,missile,enemy-quadcopter,enemy-fixedwing
   ```
4. **Check on a game background.** `v1/preview-on-grass.jpg`: the sprites over grass, full
   size and at 96px. The solid objects keyed cleanly (bold outlines help), but the
   see-through rotor discs carried the magenta.
5. **Fix in the spec, one JSON edit.** `v2/prompt.txt` sends the whole updated spec with
   the changed fields listed (opaque rotor and propeller discs, all launcher tubes
   loaded, nothing semi-transparent over the background), in the same chat.
   `v2/preview-on-grass.jpg`: fixed, and the four untouched assets came back nearly
   pixel-identical (crop sizes within 1-2px).

## What did not work

- The fixed-wing drone's V-tail was ignored twice (single fin both times). Next levers:
  a reference image, or a stronger model.
- The background is close to, not exactly, `#FF00FF` (corners up to ~45 away), which is
  why the slicer keys with a tolerance and reports the drift.
- Multi-direction or animated sprites were not attempted; a dedicated sprite tool fits
  those better.

`v2/sheet.png` is also the input of `tests/image-gen/test_slice_sheet.py`.

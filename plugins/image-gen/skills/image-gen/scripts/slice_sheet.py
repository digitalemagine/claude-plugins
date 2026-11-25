#!/usr/bin/env python3
"""Cut a sprite sheet on a flat key colour into separate transparent PNGs.

    uv run --with pillow python3 slice_sheet.py SHEET --out-dir DIR \
        [--key FF00FF] [--tol 60] [--soft 60] [--gap 6] [--pad 4] [--names a,b,c]

1. Key: pixels within --tol (RGB distance) of the key colour become transparent; the
   next --soft of distance fades from transparent to opaque (anti-aliased edges,
   semi-transparent rotor discs). Key colour spilled into kept pixels is removed.
2. Cut: rows, then columns inside each row, separated by at least --gap fully
   transparent lines (so parts of one sprite closer than --gap stay together).
3. Crop each piece to its content plus --pad, save as DIR/<name>.png (names in reading
   order from --names, else sprite-01...).

Prints a JSON report: key colour measured at the corners, how far the background drifts
from it, and every sprite's box and size. Needs Pillow only.
"""

import argparse
import json
import os
import sys

from PIL import Image


def hex_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def bands(flags, gap):
    """[start, end) runs of True in flags, merging runs separated by < gap False."""
    runs, start, last = [], None, None
    for i, f in enumerate(flags):
        if f:
            if start is None:
                start = i
            elif i - last - 1 >= gap:
                runs.append((start, last + 1))
                start = i
            last = i
    if start is not None:
        runs.append((start, last + 1))
    return runs


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("sheet")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--key", default="FF00FF")
    p.add_argument("--tol", type=float, default=60)
    p.add_argument("--soft", type=float, default=60)
    p.add_argument("--gap", type=int, default=6)
    p.add_argument("--pad", type=int, default=4)
    p.add_argument("--min-size", type=int, default=12, help="drop specks smaller than this")
    p.add_argument("--names", default="")
    a = p.parse_args()

    im = Image.open(a.sheet).convert("RGBA")
    W, H = im.size
    px = im.load()
    key = hex_rgb(a.key)
    corners = [px[x, y][:3] for x, y in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1))]

    def dist(c):
        return ((c[0] - key[0]) ** 2 + (c[1] - key[1]) ** 2 + (c[2] - key[2]) ** 2) ** 0.5

    bg_drift = max(dist(c) for c in corners)
    # Spill axis: channels the key is high in vs low in (magenta: R,B high, G low).
    hi = [i for i in range(3) if key[i] >= 128]
    lo = [i for i in range(3) if key[i] < 128]

    opaque_cols = [False] * W
    opaque_rows = [False] * H
    for y in range(H):
        for x in range(W):
            r, g, b, _ = px[x, y]
            d = dist((r, g, b))
            if d <= a.tol:
                px[x, y] = (0, 0, 0, 0)
                continue
            alpha = 255 if d >= a.tol + a.soft else int(255 * (d - a.tol) / a.soft)
            c = [r, g, b]
            if hi and lo:  # despill: pull key-high channels down to the key-low level
                spill = min(c[i] for i in hi) - max(c[i] for i in lo)
                if spill > 0:
                    k = 1.0 if alpha < 255 else 0.5
                    for i in hi:
                        c[i] = max(0, int(c[i] - spill * k))
            px[x, y] = (c[0], c[1], c[2], alpha)
            if alpha > 32:
                opaque_cols[x] = True
                opaque_rows[y] = True

    os.makedirs(a.out_dir, exist_ok=True)
    names = [n.strip() for n in a.names.split(",") if n.strip()]
    sprites = []
    alpha = im.getchannel("A")
    for (y0, y1) in bands(opaque_rows, a.gap):
        row_cols = [False] * W
        for x in range(W):
            for y in range(y0, y1):
                if px[x, y][3] > 32:
                    row_cols[x] = True
                    break
        for (x0, x1) in bands(row_cols, a.gap):
            box = alpha.crop((x0, y0, x1, y1)).point(lambda v: 255 if v > 32 else 0).getbbox()
            if not box:
                continue
            bx0, by0, bx1, by1 = box[0] + x0, box[1] + y0, box[2] + x0, box[3] + y0
            if bx1 - bx0 < a.min_size or by1 - by0 < a.min_size:
                continue
            crop = (max(0, bx0 - a.pad), max(0, by0 - a.pad),
                    min(W, bx1 + a.pad), min(H, by1 + a.pad))
            name = names[len(sprites)] if len(sprites) < len(names) else f"sprite-{len(sprites) + 1:02d}"
            path = os.path.join(a.out_dir, f"{name}.png")
            im.crop(crop).save(path)
            sprites.append({"name": name, "box": crop, "size": [crop[2] - crop[0], crop[3] - crop[1]],
                            "path": os.path.abspath(path)})

    sheet_out = os.path.join(a.out_dir, "_sheet-keyed.png")
    im.save(sheet_out)
    report = {"sheet": os.path.abspath(a.sheet), "size": [W, H], "key": a.key,
              "corner_colours": ["#%02X%02X%02X" % c for c in corners],
              "background_drift": round(bg_drift, 1), "sprites": sprites,
              "keyed_sheet": os.path.abspath(sheet_out)}
    if bg_drift > a.tol:
        report["warning"] = "corners are further from the key than --tol: background not flat or wrong --key"
    if names and len(names) != len(sprites):
        report["warning_names"] = f"{len(names)} names for {len(sprites)} sprites: check the cut"
    print(json.dumps(report, indent=1))
    sys.exit(0 if sprites else 3)


if __name__ == "__main__":
    main()

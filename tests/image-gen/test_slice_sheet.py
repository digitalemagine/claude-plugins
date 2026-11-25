#!/usr/bin/env python3
"""Regression check for slice_sheet.py on the real sheet in examples/image-gen/td-sprites.

    uv run --with pillow python3 tests/image-gen/test_slice_sheet.py

Expects 6 sprites in reading order with the sizes measured when the example was made
(+-3px), a background drift under the tolerance, fully transparent corners, and no
strongly magenta opaque pixels left in any sprite.
"""

import json
import os
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "plugins/image-gen/skills/image-gen/scripts/slice_sheet.py")
SHEET = os.path.join(ROOT, "examples/image-gen/td-sprites/v2/sheet.png")
EXPECTED = {"tower-cannon": (373, 352), "tower-laser": (376, 358), "tower-missile": (365, 381),
            "missile": (308, 116), "enemy-quadcopter": (374, 228), "enemy-fixedwing": (349, 220)}
FAILED = False


def check(cond, msg):
    global FAILED
    print(("ok   " if cond else "FAIL ") + msg)
    FAILED |= not cond


with tempfile.TemporaryDirectory() as d:
    r = subprocess.run([sys.executable, SCRIPT, SHEET, "--out-dir", d, "--names", ",".join(EXPECTED)],
                       capture_output=True, text=True)
    check(r.returncode == 0, f"exit 0 ({r.stderr.strip()[:200]})")
    rep = json.loads(r.stdout or "{}")
    got = {s["name"]: tuple(s["size"]) for s in rep.get("sprites", [])}
    check(list(got) == list(EXPECTED), f"6 sprites in reading order: {list(got)}")
    for name, (w, h) in EXPECTED.items():
        gw, gh = got.get(name, (0, 0))
        check(abs(gw - w) <= 3 and abs(gh - h) <= 3, f"{name} size {gw}x{gh} ~ {w}x{h}")
    check(rep.get("background_drift", 999) < 60 and "warning" not in rep, "background drift under tolerance")
    for name in EXPECTED:
        im = Image.open(os.path.join(d, f"{name}.png")).convert("RGBA")
        W, H = im.size
        corners = [im.getpixel(p)[3] for p in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1))]
        raw = im.tobytes()
        magenta = sum(1 for i in range(0, len(raw), 4)
                      if raw[i + 3] > 200 and raw[i] > 180 and raw[i + 2] > 180 and raw[i + 1] < 90)
        check(max(corners) == 0 and magenta < 0.002 * W * H,
              f"{name}: transparent corners, {magenta} magenta pixels left")

sys.exit(1 if FAILED else 0)

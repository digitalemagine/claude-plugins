#!/usr/bin/env python3
"""Build one test deck per engine from the html-slides templates, with slide-edit.js
inlined, for checking edit mode by hand in a browser (see tests/README.md).

    python3 tests/build-test-decks.py                    # light theme, into tests/out/
    python3 tests/build-test-decks.py --theme path.css   # any theme file, e.g. from a pack
"""
import argparse, pathlib, re

SKILL = pathlib.Path(__file__).resolve().parent.parent / "plugins/html-slides/skills/html-slide-edit"
THEME_SLOT = "/* ── theme: paste the chosen theme file here, unchanged ── */"
ENGINES = [  # (template, editable roots, extra script attributes)
    ("responsive", ".slide", ""),
    ("fixed-canvas", ".slide", ""),
    ("reveal", ".reveal .slides section:not(:has(section))", ' data-download="off"'),
]

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", type=pathlib.Path, default=SKILL / "themes/light.css")
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent / "out")
    a = ap.parse_args()
    js = (SKILL / "slide-edit.js").read_text()
    assert "</script" not in js.lower(), "slide-edit.js must not contain a closing script tag"
    theme = a.theme.read_text()
    a.out.mkdir(parents=True, exist_ok=True)
    for engine, roots, extra in ENGINES:
        page = (SKILL / f"{engine}-template.html").read_text()
        assert THEME_SLOT in page, f"{engine}: theme slot not found"
        page = page.replace(THEME_SLOT, theme)
        name = f"t-{engine}-{a.theme.stem}.html"
        script = f'<script data-roots="{roots}" data-file="{name}"{extra}>\n{js}</script>'
        page, n = re.subn(r"<!-- slide-edit:.*?-->", lambda m: script, page, flags=re.S)
        assert n == 1, f"{engine}: slide-edit placeholder not found"
        (a.out / name).write_text(page)
        print(a.out / name)

if __name__ == "__main__":
    main()

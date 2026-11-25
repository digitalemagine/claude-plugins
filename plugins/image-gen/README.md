# image-gen

Image generation with fine control. Claude turns your request, a reference image or just
its style into a **JSON spec** (framing, subject, wardrobe, environment, lighting,
camera, style, post-processing, text, game-asset fields), renders it, and keeps every
render in its own `vN` folder with the spec and prompt that produced it. To change one
thing, change one field and render again: in the same chat, everything else stays put.

```
/plugin install image-gen@digitalemagine
```

Then ask for an image ("a realistic photo of ..., 85mm, window light"), give a reference
("recreate this photo but at night"), copy a style ("draw a fox in the style of this
screenshot"), or ask for game assets ("a sprite sheet of towers and enemies for ...").

## Backends

Picked in this order, unless you name one:

1. **Gemini API** when `GEMINI_API_KEY` is set (paid per image; Claude states the cost
   before the first render of a session).
2. **Gemini web app** in your Chrome through Claude in Chrome, when there is no key:
   uses your Google login and quota. Images are saved straight into the run folder
   through a small local receiver (no download dialogs) at the app's preview size;
   full size goes through Chrome's download if you ask for it.
3. **Hand-off**: the prompt, ready to paste into Gemini yourself.

**Mistral** (API key, or the key your Vibe CLI login stores) is available on request as
an experimental comparison: it rewrites the spec into its own prompt and has no
reference images or aspect-ratio control.

## Game assets

Several related assets go on one sheet with a flat key colour, and
`scripts/slice_sheet.py` cuts it into named transparent PNGs (needs Pillow; Claude runs
it with `uv run --with pillow`). A worked case, from spec to sprites, is in
[`examples/image-gen/td-sprites`](../../examples/image-gen/td-sprites/README.md); ask
for it by name if you want to start from it.

## Extending

No extension point yet. Saved styles live in your project
(`image-gen/styles/<name>.style.json`), not in the plugin.

## Maintaining

- Scripts are standard library only, except `slice_sheet.py` (Pillow). Prompts always
  travel in files, never as shell arguments.
- `references/gemini-web.md` records what the Gemini web app looked like when last
  checked (selectors, timings): re-check it when the app changes.
- Checks before tagging: `tests/README.md` at the repo root (three offline scripts).
- Design decisions and open items: `NOTES.md` at the repo root.

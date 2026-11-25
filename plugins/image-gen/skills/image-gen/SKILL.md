---
name: image-gen
description: Fine-grained image generation with Gemini (Nano Banana), and experimentally Mistral, through structured JSON specs. Use when the user asks to generate, recreate or edit an image with precise control (camera, lens, lighting, wardrobe, palette, composition), to reverse-engineer a reference image or screenshot into a reusable prompt/spec, to copy an illustration or photo style onto new content, to make consistent series or game art (sprites, tiles, icons), or to tweak one aspect of a previous generation. Renders through the Gemini API when a key is set, otherwise through the Gemini web app in the user's Chrome, otherwise hands over the prompt. Not for charts, diagrams or UI that can be drawn as code.
---

# image-gen

Images are described as a **spec** (a JSON object with named sections), rendered by a
**backend**, and every render is logged in a **run folder**, so any result can be
reproduced or changed one field at a time.

References next to this file (read when the step needs them):
- `references/spec.md`: the spec sections, defaults by genre, presets, realism and
  consistency rules.
- `references/extraction.md`: text → spec, image → spec, hybrid, style capture.
- `references/gemini-web.md`: the no-key path in Chrome.
- `scripts/gemini_image.py`: the Gemini API renderer (`--help`).
- `scripts/mistral_image.py`: the Mistral API renderer (experimental, see backends).
- `scripts/slice_sheet.py`: cuts a sprite sheet on a flat key colour into named
  transparent PNGs (needs Pillow: `uv run --with pillow python3 ...`).
- `scripts/receive_image.py`: local receiver that saves images from a web app without
  Chrome downloads (used by `gemini-web.md`).

## 1. Workspace

Use `image-gen/` in the current project (or where the user says). Layout:

```
image-gen/
  styles/<name>.style.json        reusable style blocks
  <slug>/                         one image or series
    spec.json                     current spec (the source of truth)
    v1/ v2/ ...                   one folder per render: spec.json, prompt.txt,
                                  request.json, response.json, image-N.*, meta.json
```

A new render never overwrites an earlier `vN`. Reference images the user gives stay
where they are; `meta.json` records their paths.

## 2. Build the spec

Pick the mode (`references/extraction.md`): text → spec, image → spec, hybrid, or style
capture. Follow its protocol: analyse, **declare assumptions in a few lines**, write
`spec.json`, offer two or three variations. Apply presets and saved styles by merging
(explicit fields win) and say which were applied.

Build every spec from the user's request and their own references. Never start from a
spec, style or preset made for someone else's project (including worked examples found
in repos) unless the user explicitly asks to reuse it: the point is their image, not a
variation of an earlier one.

Worked examples are not installed with the plugin; they live in the plugin's public repo
under `examples/image-gen/` (index: `https://github.com/digitalemagine/claude-plugins/tree/main/examples/image-gen`;
files: `https://raw.githubusercontent.com/digitalemagine/claude-plugins/main/examples/image-gen/<example>/<file>`,
e.g. `td-sprites/README.md`, `style.json`, `v2/spec.json`). Fetch one only when the user
asks for it by name or asks to see an example, read its README first, and then reuse
what they asked for (the style, the spec structure, or the whole spec) as the starting
point of a new spec in their workspace. Say that results will be similar, not
identical: there is no seed.

When the request is a quick one-liner and the user did not ask for control, still write
a spec, but a short one; do not interrogate the user. Ask (AskUserQuestion) only when a
choice changes the image fundamentally and nothing points either way (photo vs
illustration, which of several references is the subject).

## 3. Render the prompt

Write `vN/prompt.txt` from the spec. Two forms:

- **JSON (default).** One lead line, then the spec without `meta.priorities` noise:
  `Render this specification as a single image. Follow every field exactly; aspect ratio <a>.`
  followed by the JSON. Name reference images in the lead ("Reference 1 is Mara's face;
  reference 2 is the style").
- **Prose** (when the user prefers it, or for the web app if JSON gets echoed back as
  text): one paragraph per section in the order style, subject, setting, action,
  composition, lighting, camera, post-processing; words to render in the image in
  double quotes with their typography; the `avoid` items as a final sentence.

**Iterating on a spec (default).** Send the **full updated spec**, led by the list of
changed fields: `Re-render the last image from this updated specification. Changed
fields: camera.lens 85mm -> 35mm, frame.shot .... Same subject; every field not listed
stays as in the last image.` In the same chat / with `--previous`, this changed lens,
aperture and framing precisely while keeping the person, clothes and light. Keep the
spec coherent when changing a field (a smaller aperture also changes
`environment.depth`).

**Quick touch-up** (one visual detail, no spec change worth keeping): the change only,
plus what must stay: "Change the jacket to dark green wool. Keep everything else
identical: face, pose, light, framing." Still update `spec.json` so it stays the source
of truth.

## 4. Pick the backend

In this order, unless the user names one:

1. **Gemini API**, when `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is set. Paid per image;
   before the first paid render of the session, say the model, size, number of images
   and the rough cost, and go ahead only once the user has agreed (an earlier "go ahead
   and generate" counts). Rough prices per image (check current pricing):
   `gemini-nano-banana-2.1` ~$0.03–0.07 (default, recommended), `gemini-3.1-flash-image`
   ~$0.07, `gemini-3-pro-image` ~$0.13 (1K/2K) and ~$0.24 (4K), best for text rendering
   and style references.
2. **Gemini web app in Chrome**, when there is no key and Claude in Chrome is available:
   follow `references/gemini-web.md`.
3. **Mistral** (experimental, only when the user asks for it): `scripts/mistral_image.py`,
   key from `MISTRAL_API_KEY` or `~/.vibe/.env` (Vibe CLI login), billed to the user's
   Mistral plan. Mistral's agent rewrites the spec into its own prose prompt for a Black
   Forest Labs model (logged as `image_model_prompt` in `meta.json`); no reference
   images, no aspect or size control (a 16:9 request came back 1024x768). Tested
   against Gemini on the same spec, it missed framing, age, expression and skin
   texture. Use it for comparisons, not as a fallback.
4. **Hand-off**: no key and no browser. Give the user `prompt.txt` (and the reference
   images to attach) to paste into Gemini themselves, and ask them to drop the result in
   the run folder.

### API call

```
python3 "${CLAUDE_SKILL_DIR}/scripts/gemini_image.py" \
  --prompt-file image-gen/<slug>/vN/prompt.txt --spec image-gen/<slug>/spec.json \
  --out-dir image-gen/<slug>/vN [--ref <image> ...] [--aspect 16:9] [--size 2K] \
  [--model gemini-nano-banana-2.1] [--thinking high] [--previous <interaction id>]
```

- Never put prompt text on the command line; always the file.
- `--aspect`: 1:1 2:3 3:2 3:4 4:3 4:5 5:4 9:16 16:9 21:9, and on 2.1 / 3.1 Flash also
  1:4 4:1 1:8 8:1. `--size`: 1K (default) 2K 4K, uppercase.
- References: up to 14 (2.1 / 3.1 Flash: 10 objects + 4 characters; 3 Pro: 6 objects,
  5 characters, 3 styles).
- `--previous` with the `interaction_id` from the last `meta.json` continues a multi-turn
  edit; use it for small successive edits, a fresh call with `--ref` for big changes.
- `--dry-run` writes `request.json` without a key or a call: use it to show the user what
  would be sent.
- Exit 3 means no image came back: read `text.txt` (usually a refusal or a question)
  and report it rather than retrying unchanged.

## 5. Show and iterate

Open or Read the image and look at it before reporting: check it against the spec's
`meta.priorities` and say plainly what matches and what does not. Then:

- Change only the fields the feedback is about; update `spec.json`; render to `vN+1`.
- After two misses on the same field, try another lever: move that requirement to the
  top of the lead line, switch JSON ↔ prose, add or change a reference image, or switch
  to `gemini-3-pro-image`.
- When a look should be reused, save the `style` (and `post_processing`, `asset`)
  sections to `image-gen/styles/<name>.style.json`.

Report at the end: the image path(s), the backend and model, what changed since the
previous version, and the run folder.

## Game assets

For sprites, icons or tiles, put several related assets on **one sheet** (consistent
style and scale for free), using the `asset` section and a saved style file:
flat key background (`#FF00FF`, unless the art itself uses magenta), one asset per
invisible grid cell with wide margins, the same view angle stated for all, bold dark
outlines (they key cleanly), and **nothing semi-transparent** over the background: rotor
discs, glows, smoke and shadows must be asked for as opaque paint, or they carry the key
colour into the sprite. Then:

```
uv run --with pillow python3 "${CLAUDE_SKILL_DIR}/scripts/slice_sheet.py" <sheet> \
  --out-dir <run>/sprites --names tower-cannon,tower-laser,...
```

Check the report (count matches the names; `background_drift` well under `--tol`) and
composite the sprites over a typical game background, at full size and at in-game size
(e.g. 96px), before showing them: key-colour fringes and see-through parts only show
there. Fix such problems in the spec (one JSON edit in the same chat keeps the other
assets nearly pixel-identical) rather than with heavier keying. True pixel art and
multi-direction or animated sprites are better served by a dedicated tool; say so.

## Rules

- No images of real private individuals from their photos without their evident consent,
  no sexual content involving real people, no impersonation of real brands or people;
  decline these the same way on every backend.
- Do not name living artists as style references; describe the style instead.
- Reference images uploaded to a backend leave the machine; say so once per session
  when they look personal.

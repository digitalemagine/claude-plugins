# Getting a spec: from text, from an image, or both

Claude reads images itself, so extraction normally happens here, with no external call:
Read the reference image, then fill the spec. Ask Gemini to extract only when the user
wants Gemini's own reading of the image (the prompts below work pasted into Gemini too).

## Protocol (all three modes)

1. **Analyse.** List what is explicit (asked for or visible), implicit (follows from it:
   a bakery at dawn implies warm practicals), and inferred (your guesses).
2. **Declare assumptions.** Before rendering, tell the user the inferred choices in a few
   short lines (lens, light, age, palette...) so they can correct them cheaply.
3. **Write the spec.** Complete and coherent: lighting, environment and style must agree
   (no "harsh noon sun" with "long golden shadows"). Plausible and specific. No
   placeholder values.
4. **Offer variations.** Name two or three fields worth trying differently next.

## Text → spec

Start from the request, apply defaults and presets from `spec.md`, fill the sections the
intent needs.

## Image → spec (reverse-engineer)

Describe what is actually in the image, section by section, as if briefing a
photographer or illustrator to recreate it: framing and shot, subject, wardrobe with
materials, environment, every light (direction, size, colour), apparent lens and
aperture (from perspective compression and depth of field), grading and grain. Measure
the aspect ratio from the pixel size. Say which values are estimates.

Prompt, when Gemini does the extraction:

> Analyse this image and write a JSON specification that would let an image model
> recreate it closely. Use these sections: meta, frame, subject, wardrobe, accessories,
> environment, lighting (key, fill, rim, shadows, color_temperature), camera (lens,
> aperture, focus, perspective), style, post_processing, avoid. Be concrete and
> measurable; no praise words; no empty fields. Output only the JSON.

## Hybrid (image as base + text changes)

Extract the full spec from the image, then apply the requested changes to the named
fields only, and list the changed fields. For edits of the image itself (not a
recreation), pass the image as a reference and describe only the change; see SKILL.md.

## Style capture (copy an illustration or photo style)

Extract only the `style` and `post_processing` sections (plus `asset` for game art),
never the subject, so the style transfers to new content:

- medium and rendering technique; palette as 4–8 hex values read from the image, with
  roles (background, shadow, highlight, accent);
- line: presence, weight, colour, consistency;
- shading: number of tones, hard or soft, where shadows sit;
- texture and detail level; composition habits (flat vs depth, negative space);
- mood in two or three words.

Prompt, when Gemini does it (from the Artea method):

> Study this illustration and write a JSON style prompt covering its colors, line style,
> shading and mood, so I can reuse it to generate other illustrations in the same style.

Save it as `styles/<name>.style.json` in the image-gen folder (see SKILL.md). To use it,
merge its sections into a new spec, and pass the source image as a style reference when
the backend allows it (Gemini 3 Pro Image takes up to 3 style references). Tips: use a
clean, high-resolution source; test the style on a simple subject first; if the result
drifts, describe the difference and adjust the style file, not the one-off prompt. The
match is close, not exact.

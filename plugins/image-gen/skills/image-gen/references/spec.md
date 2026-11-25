# Image spec

One JSON object per image. Every section is optional: include what matters for this image,
leave out what does not (an absent section means "model's choice"; an empty string or
`"tbd"` is never written). Values are short, concrete phrases, not sentences of praise
("soft north-window light from camera left", not "beautiful lighting").

```json
{
  "meta": {
    "intent": "what the image is for, one line",
    "priorities": ["what must be right, most important first"],
    "mode": "photo | illustration | pixel_art | 3d_render | ui | diagram | other"
  },
  "frame": {
    "aspect": "16:9",
    "composition": "rule of thirds, subject left, negative space right",
    "shot": "medium close-up",
    "layout": "single panel"
  },
  "subject": {
    "identity": "who or what, named if a reference image fixes it (e.g. 'Mara, the woman in reference 1')",
    "demographics": "age range, build",
    "face": "features, skin texture, freckles, asymmetry",
    "hair": "colour, length, style, flyaways",
    "body": "",
    "expression": "neutral, direct eye contact",
    "pose": "three-quarter turn, weight on back foot",
    "action": ""
  },
  "wardrobe": [
    {"item": "linen shirt", "material": "washed linen", "color": "ecru", "fit": "loose",
     "light_behavior": "matte, slight translucency at the sleeves"}
  ],
  "accessories": ["thin gold ring, left hand"],
  "environment": {
    "setting": "small bakery counter, early morning",
    "surfaces": "flour-dusted marble, worn oak",
    "depth": "background shelves softly out of focus",
    "atmosphere": "faint steam, dust in the light",
    "time_weather": ""
  },
  "lighting": {
    "key": "large window, camera left, 45 degrees",
    "fill": "white wall bounce, low",
    "rim": "none",
    "shadows": "soft, open",
    "color_temperature": "5000K daylight, warm practicals in background"
  },
  "camera": {
    "body_film": "full-frame digital | Portra 400 | phone camera",
    "lens": "85mm",
    "aperture": "f/2",
    "focus": "eyes sharp, ears falling off",
    "perspective": "eye level",
    "distortion": "none"
  },
  "style": {
    "medium": "photograph | flat vector | gouache | cel-shaded | 16-bit pixel art | ...",
    "palette": ["#2B3A42", "muted teal", "warm cream"],
    "line": "no outlines | 2px uniform dark-brown outline | sketchy pencil",
    "shading": "two-tone cel | soft gradients | none",
    "texture": "paper grain | film grain fine | clean",
    "detail_level": "low, shapes over detail",
    "references": "described in words; never an artist's name for living artists",
    "mood": "calm, early-morning quiet"
  },
  "post_processing": {
    "color": "slightly lifted blacks, desaturated greens",
    "tonality": "low contrast",
    "texture": "fine grain",
    "film_qualities": "mild halation on highlights"
  },
  "text": [
    {"content": "OPEN", "placement": "sign on the door", "typography": "hand-painted serif, gold leaf"}
  ],
  "asset": {
    "kind": "character sprite | tile | tileset | icon | item | ui element | background",
    "view": "side | top-down | isometric | front",
    "size_px": "64x64",
    "directions": 1,
    "frames": "idle, 4 frames (as a sheet, left to right)",
    "background": "perfectly flat #FF00FF for keying, nothing semi-transparent over it",
    "grid": "pixel-perfect, no anti-aliasing, limited 16-colour palette"
  },
  "avoid": ["plastic skin", "extra fingers", "text artefacts", "bokeh balls"],
  "panels": []
}
```

## Defaults when the request says nothing (state them as assumptions)

| Genre | Lens, aperture, light |
|---|---|
| Fashion / editorial | 85mm, f/2.8, controlled studio light, styled subject |
| Street / documentary | 35mm, f/8, natural light, unposed |
| Portrait | 85mm, f/2, flattering soft light, moderate depth of field |
| Action / dynamic | 24–35mm, f/5.6, energetic angle |
| Product | 100mm macro, f/8, softbox key + rim, seamless background |

No age given: 25–30 for fashion, 30–40 for professional contexts. No expression given:
neutral with direct eye contact. These are conventions, not rules: change them when the
intent says otherwise.

## Presets

Named partial specs merged into a spec (preset first, explicit fields win). Mention which
ones were applied.

- `35mm-street`: camera 35mm f/8, natural light, eye level, slight motion blur on passers-by, Tri-X or Portra grain.
- `overcast-soft`: lighting key "overcast sky, large soft source", shadows "very soft", colour temperature 6500K, low contrast.
- `golden-hour`: low warm sun behind subject, rim light, long shadows, 3500K, lens flare minimal.
- `studio-headshot`: 85mm f/4, key softbox 45° + fill card, grey seamless, catchlights.
- `phone-snapshot`: phone camera, deep focus, slight overexposure, imperfect framing, no grading (strong against the "AI look").
- `editorial-flash`: direct on-camera flash, hard shadows behind subject, high contrast, night.
- `flat-vector`: style medium flat vector, no outlines, 4–6 colour palette, no gradients, no texture.
- `pixel-16bit`: style medium 16-bit pixel art, asset grid "pixel-perfect, no anti-aliasing", limited palette, 1px dark outline.
- `iso-tile`: asset view isometric 2:1, single tile, plain background, consistent top-left light.

## What makes photos read as real (keep in specs for photo mode)

Skin texture and pores, small asymmetries, flyaway hair, fabric creases, real lens choice
with matching depth of field, one plausible light source per role, slight imperfection in
framing or exposure, mild grain. The "AI look" comes from perfect symmetry, airbrushed
skin, rim light everywhere, teal-orange grading and centred subjects.

## Avoid list

Gemini has no negative-prompt parameter: `avoid` is rendered into the prompt text. Prefer
saying what should be there over listing what should not ("an empty street at dawn"
beats "no cars, no people"); keep `avoid` for persistent artefacts.

## Consistency across images

- Give each recurring character or object a name and bind it to its reference image
  ("Mara = reference 1"). Reuse the same `subject` and `style` blocks verbatim.
- Change one section per iteration; keep everything else byte-identical.
- For a series, save the shared parts as a style file (see `extraction.md`) and merge it.

---
name: html-slide-edit
description: Local HTML slide decks with token-based colour themes (built-in light, plus any installed theme packs) and in-browser text editing (off unless the URL carries ?edit). Use when creating a local HTML deck or page (it picks the engine — responsive, fixed canvas (deck.js) or reveal.js — and the theme, asking when either is ambiguous, and wires in edit mode from the start), when adding or upgrading edit mode in an existing one, or when the user pastes a "slide-edit change set" to apply to a source file.
---

# html-slide-edit

`slide-edit.js` (next to this file) adds an edit toolbar to a local HTML page. It is
inert unless the page is opened with `?edit` in the URL (`deck.html?edit`, also
`deck.html?edit#4`). Read the header comment in `slide-edit.js` for the full contract.

## New deck: settle engine and theme first, ask when ambiguous

Applies to **new** decks only. An existing deck keeps its engine and its local theme
(its own colour tokens, or a shared stylesheet it links); never switch either unasked.

Before writing any slide, settle both choices from these signals, strongest first:
1. The user names it ("use reveal", "the dark one", "like the deck in that folder").
2. The project: its CLAUDE.md, then the decks already in the folder. A project that
   has its own deck engine or shared stylesheet (for example a `deck.css`/`deck.js` pair)
   uses that, linked as its CLAUDE.md says, not a template from this skill.
3. The request: the "Use when" column of the engine table, and the "use when" line of
   each theme (built-in and theme packs, see below).

**Clear** = one engine and one theme follow from those signals without conflict. Then
proceed, and state both in one line with the reason ("Responsive, light: a text-led
options summary for a meeting.") so the user can override.

**Ambiguous** = no signal for one of the two, or signals conflict (for example: a
roadmap to be presented with speaker notes; a formal deck that must read on a phone;
content that belongs to a project with its own deck style but is being created
elsewhere; a folder whose decks use two different looks; two themes whose "use when"
both fit). Then **ask before writing anything**, with AskUserQuestion: one
question for the engine and/or one for the theme, only for what is ambiguous. Put the
best-fitting option first marked "(Recommended)", and give each option a one-line
trade-off. Do not fall back to a default silently: a default is only the recommended
option in the question.

## Choosing the deck engine (decide before writing the deck)

Three engines, one template each next to this file. All use `<section class="slide">`
(reveal: `<section>`), so moving a deck between engines is mechanical.

| Engine | Template | Use when |
|---|---|---|
| **Responsive** | `responsive-template.html` | Text-led decks read on screen or walked through in a meeting: options, positions, briefings. Reflows; readable on a phone. Offline. |
| **Fixed canvas** (deck.js) | `fixed-canvas-template.html` | Dense, designed layouts where position matters: roadmaps, timelines, org charts, KPI strips, chip grids, diagrams. Pixel-exact 1920x1080, scaled to fit, click-half and swipe navigation. Exports to PNG/PDF/PPTX by screenshotting the canvas. Offline. Not for phones. |
| **reveal.js** | `reveal-template.html` | Presented live with speaker notes or a presenter view, step-by-step reveals, a PDF via `?print-pdf`, or the user asks for reveal. Needs network (cdnjs). |

- **Project rules win.** A project with its own deck engine keeps it, and a project that
  forbids CDNs rules out reveal.js. The fixed-canvas template is a self-contained
  `deck.css`/`deck.js`-style engine for projects that have none.
- Responsive sizes are in `cqw` (1% of the stage); fixed-canvas sizes in px or `cqw/cqh`.
  Never `vw`/`vh` in either: they resolve against the window and break the scaling.

## Theme (colours and fonts)

Every theme is one CSS file defining the same tokens: `--bg --surface --surface-2
--ink --muted --faint --line --line-soft --primary --accent --accent-soft --good --warn
--font-display --font-body --font-mono`. A theme may add its own extra tokens (for
example a status palette); deck CSS that uses them only works with that theme.

Built in, in `themes/`:
- `light.css` — marine and brass on warm grey, with a dark variant that follows the OS.
  Use when: working and discussion documents, or no theme pack fits.

### Theme packs

Other plugins add themes through a **theme-pack skill**: a skill whose description
starts with "Theme pack for html-slides". For a new deck, before settling the theme,
look in the available skills list for such skills and invoke each one. A pack lists its
themes, each with a file path and a "use when" line, and may name the material it is the
default for. Treat pack themes exactly like `light.css`: same rules below, same signals
above (a pack's "default for" counts as signal 3, below the project and the user).
If no pack is installed, `light.css` is the only theme; do not invent one.

Rules:
1. Paste the theme file **inline**, unchanged, as the first block of the page's `<style>`.
   If its header names a web-font link, add that link to `<head>`.
2. Deck CSS uses **only** the tokens: no raw hex values. Switching theme is then
   replacing that one block. Derived shades use `color-mix()` on the tokens.
3. reveal.js: the template maps the tokens onto reveal's `--r-*` variables over its
   white base theme; paste the theme where the template says.
4. A theme change asked for one deck stays in that deck. Change a theme file only when
   the user asks to change the theme itself.

## Embedding it in a page

1. Read `slide-edit.js` and paste it **inline** in a `<script>` as the last element of
   `<body>`, after the page's own script. Pages here are single self-contained files, so
   never reference it with `src=`.
2. Set attributes on that `<script>` tag:
   - `data-roots` — selector of the editable regions. `.slide` for decks. For a plain
     page, wrap editable content in elements carrying a class and point at that.
   - `data-file` — the source file name, exactly as on disk.
   - `data-position` — only if the default `top-right` covers page chrome.
   - `data-download="off"` — for reveal.js or any library that rewrites the DOM at runtime.
   For reveal.js use `data-roots=".reveal .slides section:not(:has(section))"` (innermost
   sections only, so vertical stacks number correctly) and `data-download="off"`. Hidden
   fragments are not visible while editing; step through them first, or edit in the source.
   **Never put a closing script tag in the inlined text**, even in a comment: it ends the
   script early and the whole snippet fails with a syntax error.
3. Do not add Edit/Save buttons, flags or CSS for edit mode to the page. The script
   injects its own toolbar in a shadow root and removes all of it when serialising.
4. Page keyboard handlers need no edit-mode awareness: keys typed inside a region are
   stopped in the capture phase before they reach them.
5. If the page generates runtime DOM (dot rails, counters, an active-slide class), add a
   `slide-edit:serialise` listener that undoes it on `event.detail.root`. This only
   matters for the Download fallback.
6. Mention `?edit` and the change-set workflow in the page's top-of-file comment.

To upgrade an existing page, find its copy with `grep -n "slide-edit v" <file>` and
replace the whole inline script body with the current `slide-edit.js`, keeping the
`data-*` attributes.

## Applying a pasted change set

The user clicks "Copy changes" (or Cmd/Ctrl+S) and pastes text starting with
`# slide-edit change set for "<file>"`. Each entry has a location line, a BEFORE and an
AFTER fragment. To apply:

1. Open the named file. If the project has a "commit before editing" rule, follow it.
2. For each entry, locate BEFORE in the source and replace it with AFTER using exact
   edits. Fragments are browser-serialised, so the source may differ in entities
   (`&amp;` vs `&`, `&nbsp;`, `—` vs `&mdash;`), attribute quoting, self-closing tags and
   line wrapping. If an exact match fails, use the location line (region number, its
   heading, and the element path) and the text content to find the element, then edit it
   in the **source's** own style and indentation. Do not paste browser serialisation
   artefacts into the source: drop stray `<br>` at the end of an element, collapse
   `&nbsp;` the user did not mean, and keep entities the way the source writes them.
3. When a fragment is a whole list or table row (the user added or removed items), rebuild
   that block in source formatting rather than pasting the one-line browser output.
4. Apply the project's writing rules to the new text only if the user asks; by default the
   user's wording is applied verbatim. Point out anything that conflicts with a rule.
5. Report which entries were applied and list any that could not be matched. Tell the
   user to reload the page before editing again: the change set is cumulative since page
   load, so copying again without reloading repeats entries already applied.

## Why change sets and not Save

Re-serialising the DOM rewrites the whole file: formatting and entities drift, the git
diff becomes noise, and any runtime state the page generated gets baked in. A browser
"Save page" is worse (it also rewrites external links to a local `_files/` folder).
The change set leaves the source as authored and lets Claude make minimal, reviewable
edits. Download stays as a fallback for when Claude Code is not at hand.

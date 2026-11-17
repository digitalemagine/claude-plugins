# Design notes and status

Why the plugins are built the way they are, what has been tested, and what is open.
Usage is in `README.md` (overview) and each plugin's `README.md` (details, extending).

## Status

- Published as `digitalemagine/claude-plugins`, marketplace name `digitalemagine`.
- Plugin author is a name only; no company email anywhere in the repo.
- Tagged `html-slides--v0.2.0`. Installs verified from GitHub.
- `personal-desk` 0.1.0 (page template_version 3): not yet tagged. Its SKILL.md pins the
  template URL to tag `personal-desk--v0.1.0` with a sha256, so tag exactly that commit.
- `image-gen` 0.1.0, not yet tagged. Backends: Gemini (API, web app, hand-off) and Mistral API (experimental).
  Gemini API path tested against a mock only (no key yet).
- At least one private organisation marketplace re-lists `html-slides` (`git-subdir`
  source pinned to a release tag) next to its theme pack, so its users add one
  marketplace. Release tags are therefore a contract: never move one after release.

## Decisions

**Change sets, not Save.** Re-serialising the DOM rewrites the whole file (entity and
formatting drift, noisy diffs, runtime state baked in). Edit mode copies a markdown
change set (BEFORE/AFTER per changed element) that is pasted into Claude Code and applied
as exact edits. Download stays as a fallback and is off for reveal.js, which rewrites the DOM.

**Three engines, chosen per new deck.** Responsive (text-led, reflows, phone), fixed
canvas (1920x1080 `deck.js`-style, dense designed layouts), reveal.js (live presenting,
speaker notes; needs CDN). Existing decks keep their engine and theme. For a new deck
the skill settles both from: user > project CLAUDE.md and existing decks > request, and
**asks with AskUserQuestion when ambiguous**, never silently defaulting.

**Themes are token files.** Every theme defines the same tokens (`--bg` … `--font-mono`);
deck CSS uses only tokens, so switching theme is replacing one inline block.

**Extension by composition.** Claude Code has no skill inheritance or override. An
organisation extends `html-slides` with its own plugin that depends on it and ships a
**theme-pack skill** (description starts "Theme pack for html-slides"; lists theme files
via `${CLAUDE_SKILL_DIR}` with "use when" lines and defaults). `html-slide-edit` looks for
such skills and invokes them before choosing a theme. Rejected: forks (drift); a
`userConfig` themes folder (needs per-machine setup). Keep the latter as fallback if
discovery by description proves unreliable.

**One repo per audience.** Generic plugins here; each organisation's add-ons in its own
private repo. Plugin count is not a reason to split further; independent versions come
from `<plugin>--v<version>` tags.

**personal-desk: page as a template file, copied not retyped.** The page is about 25 KB
of HTML. Embedded in SKILL.md it would load on every desk call and Claude would have to
reproduce it verbatim to create a desk, where a single dropped character breaks the page
silently. So it is a separate file, copied with a command and checked against the sha256
in SKILL.md. Sources in order: the skill folder (plugin install), the pinned release URL
(claude.ai account skills hold only SKILL.md), an existing desk of the user's (last
resort, with consent).

**personal-desk: settings in the desk's database, not the page.** `meta/config` holds the
page URL, title and reference systems, so one template serves every desk and user, and
renaming or adding a ticket system needs no republish. Bump `template_version` on any
template change and give migration steps in SKILL.md.

**personal-desk: backups are JSON files, made by Claude and by the page.** One JSON
file holds config, sweep state and items keyed by doc id, so a restore keeps item links.
YAML adds nothing; CSV is offered for spreadsheets only (it drops sessions and
settings). Claude makes the backup (works on any surface with file output) and the page
has Export buttons through the `downloads` capability (hidden where unavailable). The
page writes `meta/config.last_export`, which drives the 30-day backup reminder.
Restore is done by Claude only: it needs validation, a preview and migration of old
files, which a page button cannot do safely. Merge (newer `updated` wins) is the
default; replace only when asked.

**personal-desk: updates are a described procedure.** Back up, republish the template,
migrate data one version at a time, check counts, then bump `template_version`. Never
without the user's yes, never a downgrade.

**Extension points per plugin, not promised for all.** Each plugin that can be extended
says so in its README under Extending; the top README lists only those. Both existing
points use the same mechanism: discovery by a skill-description prefix ("Theme pack for
html-slides", "Preset pack for personal-desk"). A prefix is a contract with dependants.

**personal-desk: preset packs suggest, never write.** A pack gives reference systems,
sweep sources and areas; it is read before creating a desk, changing reference systems
and sweeping. Precedence: user and `meta/config` > pack > built-in presets. Nothing from
a pack reaches a desk without the user confirming, as for any other proposal.

**personal-desk: generic refs.** Items carry `refs` (keys or links); each desk configures
ordered reference systems (pattern, link template, upper). Notes are matched
case-sensitively so prose is not linkified; input refs of `upper` systems are uppercased.

**image-gen: Spec first, backend second.** The spec (JSON, sections from the "realistic to JSON"
custom-instruction method plus `style`, `text` and `asset` for game art) is the source of
truth; backends only render it. Other services (PixelLab, Ludo.ai) are meant to be added
as further backends mapping the same spec onto their endpoints.

**image-gen: JSON prompt by default, prose as a lever.** Google's guide recommends narrative prose
and one public test found JSON and prose equivalent; the maintainer's own tests favour
JSON for control. So JSON is the default and switching to prose is one of the retry
levers, not a separate mode.

**image-gen: Claude extracts, not Gemini.** Image → spec and style capture run in Claude (it reads
images), so they need no backend. The Gemini extraction prompts are kept for users who
want Gemini's reading.

**image-gen: Backend tiers.** API key → `scripts/gemini_image.py` (stdlib only, prompt from a
file, never a shell argument: the shell-injection pattern found in several public
Nano Banana skills). No key → Gemini web app through Claude in Chrome, locating controls
by label. Neither → hand-off of `prompt.txt`. Mistral only when asked (below).

**image-gen: Interactions API.** The current Gemini image docs use only
`POST v1beta/interactions` (`Api-Revision: 2026-05-20`, `response_format`,
`generation_config.thinking_level`, `previous_interaction_id`). No full raw response
schema is published, so the script walks the response for image parts and skips
`thought` steps.

**image-gen: No Chrome downloads by default.** Downloads can stop on a save dialog (user setting).
Gemini's CSP blocks `fetch` to localhost and to its own `blob:` URLs, but not
`window.open` to `http://127.0.0.1` or canvas reads, so `receive_image.py` serves a relay
page that the app's tab opens and `postMessage`s the image to. Cost: the page only holds
the 1K preview (1376x768 for 16:9); full size still needs the download button.

**image-gen: JSON edits send the whole spec.** Iterations send the full updated spec with a
changed-fields list, not a diff or prose, so the spec file stays the one source of truth
and the model sees the full context each time.

**image-gen: Examples are case studies, outside the plugin.** `examples/image-gen/td-sprites`
records one run (spec, edit, sheet, checks) at repo level, so installs do not ship it and
the skill never reads it on its own; SKILL.md says to build specs only from the user's
request, and gives the raw GitHub URLs so a user can ask for an example by name.
Reason: Gemini has no seed, so a reused spec gives a similar image, and an example inside
the skill would anchor every similar request on the same look. Its sheet doubles as the
slicer's regression input.

**image-gen: Sprite sheets, not single sprites.** One sheet keeps style and scale consistent;
`slice_sheet.py` (Pillow, run via `uv run --with pillow`) keys and cuts it. Problems
are fixed in the spec, not with heavier keying.

**image-gen: Mistral is a comparison backend, not a fallback.** Its agent rewrites the spec into a
prose prompt for a Black Forest Labs model (logged as `image_model_prompt`), with no
reference images and no aspect/size control. The response did not match the docs (URL in
`info.result` instead of a `tool_file` chunk); the script handles both and never sends
the API key to the storage URL. Key from `MISTRAL_API_KEY` or `~/.vibe/.env`.

**image-gen: Paid calls need agreement.** Before the first API render of a session, the skill states
model, size, count and rough cost.

## Tested

How to re-run: `tests/README.md` (test deck builder + manual checklist, engine/theme check).


- Edit mode in Chrome on all three engines: off without `?edit`; navigation keys, clicks
  and swipes blocked while editing; Esc exits; change set correct; Download free of edit
  UI and runtime state; toolbar drag, persistence, double-click reset, clamping.
- `claude plugin validate .` and per plugin: pass.
- Theme-pack discovery, headless `claude -p` with a private theme pack installed: the
  pack was invoked every time; formal/customer requests got the pack theme, internal
  working documents got `light`, and mixed-audience requests produced a question.

- personal-desk: template script syntax; ref parsing and linking on sample inputs (Jira,
  GitHub with groups, plain links, unknown keys, invalid regex skipped, legacy `jira`
  field and `jira_site` config); migration of one live desk from template 1 to 2 and its
  data. `/plugin install personal-desk@digitalemagine` from GitHub works.
- personal-desk preset packs, headless `claude -p` with `--plugin-dir` for the plugin and
  a test pack: asked to propose a new desk's settings, it invoked the pack, put the
  pack's Jira system first, added its sweep source and areas, kept built-in presets as
  extras, and asked for confirmation before writing.
- personal-desk template 3 page, in Chromium with a stub of the claude.ai runtime: JSON
  export holds config, sweep and items keyed by id; CSV quotes commas, quotes and
  newlines, neutralises formula cells, carries item links; `last_export` is written;
  Export is hidden when `downloads` is unavailable.
- personal-desk on claude.ai, throwaway desk built from template 2 (3 items, sweep
  state, two reference systems), following SKILL.md step by step: update to template 3
  (backup, republish with `downloads`, items identical after, version recorded);
  restore in merge mode (deleted item back identical, newer desk edit kept, item added
  after the backup kept) and in replace mode (desk identical to the backup). Found and
  fixed: a restore wrote back `template_version`, `last_export` and `updated` from the
  file; replace was ambiguous for items on both sides.

- image-gen: Triggering, headless `claude -p` with the plugin loaded: fires on a precise photo
  request, a style copy and a pixel sprite; not on a bar chart from a CSV.
- image-gen: Web-app path run end to end (25 Nov 2026, Plus account): JSON spec → 2752x1536 image;
  same-chat prose touch-up (shirt, light) and same-chat full-JSON edit with a
  changed-fields list (lens 85→35mm, f/2→f/5.6, framing) both kept identity and changed
  exactly the named fields. Selectors recorded in `gemini-web.md`.
- image-gen: Game-asset test (web app): one JSON spec + saved style file → a 3x2 sprite sheet
  (3 towers on a shared base, missile, 2 enemy drones), consistent style, flat magenta;
  `slice_sheet.py` cut it into 6 named transparent PNGs. See-through rotor discs carried
  magenta; a same-chat JSON edit made them opaque and left the other 4 assets nearly
  pixel-identical (crop sizes within 1-2px). A requested V-tail was missed twice.
- image-gen: Mistral API run once on the same spec: image returned (1024x768, 16:9 ignored), spec
  followed loosely (framing, age, expression, skin). Kept as an experimental backend.

## Open

1. Possible "Apply to file…" button in the edit toolbar (File System Access API), not built.
2. Possibly a second generic theme (e.g. plain dark) so the plugin is not single-theme
   without a pack.
3. personal-desk: desk creation by the installed plugin from its own folder (the tested
   desk was published by hand from the template, then configured as SKILL.md says).
4. personal-desk: preset packs in a real desk creation and a real sweep (only the
   proposal step is tested).
5. personal-desk: the page's Export buttons on claude.ai (needs a person to click and
   accept the save prompt).
6. image-gen: Live API test with a key: confirm request accepted, response shape, `512px` size string.
7. image-gen: Web-app path: reference-image upload (`file_upload`) not yet exercised; full-size
   capture without the download button not found (the 1K preview is what the relay gets).
8. image-gen: Formal trigger evals (skill-creator) beyond the four headless checks above.
9. image-gen: Backends: PixelLab (MCP `https://api.pixellab.ai/mcp`, Bearer; pixel-art characters,
   rotations, animation, tilesets) and Ludo.ai (API/MCP/CLI on Pro plan; async jobs,
   sprites, 3D). Both have web apps for a no-key path.
10. image-gen: Game assets: multi-direction and animation frames untested; PixelLab / Ludo.ai
   backends would cover those.
11. image-gen: Mistral: Le Chat web app path (supports edits and uploads) not built.
12. image-gen: Presets from PicoPersona (JS-rendered site, not read yet).
13. Repo has no LICENSE (plugin directory submission would require one; also affects
   html-slides).

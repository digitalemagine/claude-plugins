# Design notes and status

Why the plugins are built the way they are, what has been tested, and what is open.
Usage is in `README.md`.

## Status (14 Oct 2026)

- Published as `digitalemagine/claude-plugins`, marketplace name `digitalemagine`.
- Plugin author is a name only; no company email anywhere in the repo.
- Tagged `html-slides--v0.2.0`. Installs verified from GitHub (14 Oct).
- At least one private organisation marketplace depends on `html-slides` here, through a
  theme pack (cross-marketplace dependency).

## History

- **`html-slides` 0.1.0, 13 Oct.** Edit mode extracted from a project deck into a
  reusable `slide-edit.js` (off unless `?edit`, draggable toolbar, "Copy changes" change
  set). Three engine templates. Two themes.
- **`html-slides` 0.2.0, 13 Oct.** Made generic: the organisation brand theme moved to
  that organisation's own theme pack. Theme-pack discovery added. Templates say "paste
  the chosen theme file".
- **14 Oct.** Moved into this repo, unchanged, starting without the earlier history.
  Marketplace first named `common-plugins`, then `digitalemagine`.

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

## Tested

How to re-run: `tests/README.md` (test deck builder + manual checklist, engine/theme check).


- Edit mode in Chrome on all three engines: off without `?edit`; navigation keys, clicks
  and swipes blocked while editing; Esc exits; change set correct; Download free of edit
  UI and runtime state; toolbar drag, persistence, double-click reset, clamping.
- `claude plugin validate .` and per plugin: pass.
- Theme-pack discovery, headless `claude -p` with a private theme pack installed: the
  pack was invoked every time; formal/customer requests got the pack theme, internal
  working documents got `light`, and mixed-audience requests produced a question.

## Open

1. Possible "Apply to file…" button in the edit toolbar (File System Access API), not built.
2. Possibly a second generic theme (e.g. plain dark) so the plugin is not single-theme
   without a pack.

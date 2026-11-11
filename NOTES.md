# Design notes and status

Why the plugins are built the way they are, what has been tested, and what is open.
Usage is in `README.md`.

## Status

- Published as `digitalemagine/claude-plugins`, marketplace name `digitalemagine`.
- Plugin author is a name only; no company email anywhere in the repo.
- Tagged `html-slides--v0.2.0`. Installs verified from GitHub.
- `personal-desk` 0.1.0 (page template_version 2): not yet tagged. Its SKILL.md pins the
  template URL to tag `personal-desk--v0.1.0` with a sha256, so tag exactly that commit.
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

**personal-desk: generic refs.** Items carry `refs` (keys or links); each desk configures
ordered reference systems (pattern, link template, upper). Notes are matched
case-sensitively so prose is not linkified; input refs of `upper` systems are uppercased.

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
  data. Not yet: creating a fresh desk end to end; plugin install via `/plugin install`.

## Open

1. Possible "Apply to file…" button in the edit toolbar (File System Access API), not built.
2. Possibly a second generic theme (e.g. plain dark) so the plugin is not single-theme
   without a pack.
3. personal-desk: run desk creation end to end (fresh desk, then delete it) before tagging.

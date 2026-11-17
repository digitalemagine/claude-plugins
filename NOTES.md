# Design notes and status

Why the plugins are built the way they are, what has been tested, and what is open.
Usage is in `README.md` (overview) and each plugin's `README.md` (details, extending).

## Status

- Published as `digitalemagine/claude-plugins`, marketplace name `digitalemagine`.
- Plugin author is a name only; no company email anywhere in the repo.
- Tagged `html-slides--v0.2.0`. Installs verified from GitHub.
- `personal-desk` 0.1.0 (page template_version 3): not yet tagged. Its SKILL.md pins the
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
- personal-desk preset packs, headless `claude -p` with `--plugin-dir` for the plugin and
  a test pack: asked to propose a new desk's settings, it invoked the pack, put the
  pack's Jira system first, added its sweep source and areas, kept built-in presets as
  extras, and asked for confirmation before writing.
- personal-desk template 3 page, in Chromium with a stub of the claude.ai runtime: JSON
  export holds config, sweep and items keyed by id; CSV quotes commas, quotes and
  newlines, neutralises formula cells, carries item links; `last_export` is written;
  Export is hidden when `downloads` is unavailable. Not yet on claude.ai itself, and
  restore is untested (it is a skill procedure, needs a real desk).

## Open

1. Possible "Apply to file…" button in the edit toolbar (File System Access API), not built.
2. Possibly a second generic theme (e.g. plain dark) so the plugin is not single-theme
   without a pack.
3. personal-desk: run desk creation end to end (fresh desk, then delete it) before tagging.
4. personal-desk: preset packs in a real desk creation and a real sweep (only the
   proposal step is tested).
5. personal-desk: on a throwaway desk on claude.ai: update from template 2 to 3, the
   page's Export buttons, "back up my desk", and a restore (merge and replace).

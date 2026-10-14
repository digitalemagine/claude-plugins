# claude-plugins (digitalemagine)

GitHub: `digitalemagine/claude-plugins`. Marketplace name: `digitalemagine`.

General-purpose Claude Code plugins. No organisation-specific content, so this repo can
be published on its own. Organisation-specific add-ons (themes, rules) live in their own
private marketplaces and depend on plugins here.

## Install

```
/plugin marketplace add digitalemagine/claude-plugins
/plugin install html-slides@digitalemagine
```

Update after changes are pushed: `/plugin marketplace update digitalemagine`, then
`/plugin update html-slides@digitalemagine` and restart Claude Code.

## Plugins

| Plugin | What it does |
|---|---|
| `html-slides` | Local HTML decks. Chooses the engine (responsive / fixed canvas / reveal.js) and a token-based theme (built-in `light`, plus any installed theme pack), asking when ambiguous. Adds an edit mode (`?edit`): edit in the browser, "Copy changes", paste into Claude Code, which applies the edits to the source. |

## Maintaining

- Edit here, bump `version` in the plugin's `plugin.json`, run `claude plugin validate .`,
  commit, push. Tag releases with `claude plugin tag --push` (tags `<plugin>--v<version>`)
  so dependants can pin version ranges.
- `html-slides/skills/html-slide-edit/slide-edit.js` is inlined into every deck that uses
  it. After changing it, existing decks keep their old copy until upgraded (the skill
  says how: grep for `slide-edit v`). Never put a closing script tag in that file.
- **Theme packs.** `html-slides` finds extra themes through any skill whose description
  starts with "Theme pack for html-slides". A pack's SKILL.md lists each theme's file
  (`${CLAUDE_SKILL_DIR}/themes/<name>.css`, full token set) with a "use when" line, and
  says which material each is the default for. Add a theme here only if it is generic.
- No organisation names, project names or machine paths in anything here.
- Naming: the marketplace `name` may not look like an official Anthropic one
  (`claude-plugins`, `claude-plugins-common` are rejected by `claude plugin validate`).
  The repo name has no such limit, hence repo `claude-plugins`, marketplace `digitalemagine`.

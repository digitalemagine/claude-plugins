# claude-plugins (digitalemagine)

GitHub: `digitalemagine/claude-plugins`. Marketplace name: `digitalemagine`.

General-purpose Claude Code plugins, made for my own work and shared for anyone to use.

## Make them yours

Want your company's look, tools or house rules on top? No need to fork. Create your own
marketplace (private if you like) with a small plugin that depends on one here and adds
only what is specific to you. Point it at a release tag (`<plugin>--v<version>`) so you
choose when to take updates.

This works only where a plugin has an extension point for it, and not every plugin
has one. Those that do, and what you can add:

| Plugin | Extension point | You can add |
|---|---|---|
| [`html-slides`](plugins/html-slides/README.md#extending) | theme pack | your brand's colours and fonts as deck themes |
| [`personal-desk`](plugins/personal-desk/README.md#extending) | preset pack | your ticket systems, sweep sources and areas |

## Install

```
/plugin marketplace add digitalemagine/claude-plugins
/plugin install html-slides@digitalemagine
/plugin install personal-desk@digitalemagine
```

Update after changes are pushed: `/plugin marketplace update digitalemagine`, then
`/plugin update <plugin>@digitalemagine` and restart Claude Code.

## Plugins

Each plugin's README has the details: usage, extending, maintenance notes.

| Plugin | What it does |
|---|---|
| [`html-slides`](plugins/html-slides/README.md) | Local HTML slide decks: picks the engine and theme, and adds an in-browser edit mode whose changes Claude applies back to the source. |
| [`personal-desk`](plugins/personal-desk/README.md) | A private claude.ai page for your own tasks, ideas and priorities, fed from any chat and swept from Jira, Slack and email. Backup, export and restore included. |

## Maintaining

- Edit here, bump `version` in the plugin's `plugin.json`, run `claude plugin validate .`,
  commit, push. Tag releases with `claude plugin tag --push` (tags `<plugin>--v<version>`)
  so dependants can pin version ranges. Never move a tag once released.
- Plugin-specific notes are in each plugin's `README.md`, under Maintaining.
- An extension point is a promise to dependants: change its contract (the description
  prefix, what a pack may give) only with a version bump and a note in that README.
- No organisation names, project names or machine paths in anything here.
- Naming: the marketplace `name` may not look like an official Anthropic one
  (`claude-plugins`, `claude-plugins-common` are rejected by `claude plugin validate`).
  The repo name has no such limit, hence repo `claude-plugins`, marketplace `digitalemagine`.

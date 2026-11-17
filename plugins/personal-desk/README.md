# personal-desk

A private claude.ai page with its own database for the tasks, ideas and priorities that
live outside the team tracker. Created on first use. From any chat you can add or
review items ("add to my desk: ..."), link to an item, and open a Claude session on
it. Items carry ticket references (Jira, Linear, GitHub... configured per desk), and
"sweep my desk" finds new to-dos in Jira, Slack and email.

Back up any time: "back up my desk" saves a JSON file with every item and setting
(the page's footer has the same Export, as JSON or CSV). "Restore my desk from <file>"
merges a backup back in, or moves it to a new desk, after showing what would change.
Other lists (a CSV, another tool's export) can be imported the same way. When the
plugin brings a newer page or data layout, Claude offers to update your desk, and
backs it up first.

Needs claude.ai artifacts with the database capability (and downloads, for the page's
Export buttons).

```
/plugin install personal-desk@digitalemagine
```

Also usable as a claude.ai account skill: upload `skills/personal-desk/SKILL.md`; it
fetches the page template from a release tag.

## Extending

Fit desks to your team with a **preset pack**: a plugin of yours (it can live in a
private marketplace), or a claude.ai account skill, holding a skill whose description
starts with "Preset pack for personal-desk". `personal-desk` invokes every such skill
before creating a desk, changing its reference systems, or sweeping. A pack may give:

- **Reference systems** with your real hosts, in the format of `SKILL.md`, e.g.
  `{"name":"Jira","pattern":"[A-Z][A-Z0-9]{1,9}-\\d+","url":"https://<your-site>.atlassian.net/browse/{key}","upper":true}`.
  They are offered first when a desk is created.
- **Sweep sources**: more places to look, with what counts as a to-do there (a Slack
  channel where requests land, a Jira filter, a mail label).
- **Areas**: suggested area names for items.

A pack only suggests. The user and the desk's own settings win, and nothing from a pack
is written to a desk without the user confirming.

Example pack, `skills/desk-presets/SKILL.md` in your plugin:

```markdown
---
name: desk-presets
description: Preset pack for personal-desk. Reference systems, sweep sources and areas for <team>.
---

Reference systems, in this order:
- {"name":"Jira","pattern":"[A-Z][A-Z0-9]{1,9}-\\d+","url":"https://<your-site>.atlassian.net/browse/{key}","upper":true}

Sweep sources:
- Slack #<team>-requests: messages that ask the user for something by name.

Areas: platform, hiring, customers.
```

## Maintaining

- The page is `skills/personal-desk/desk-template.html`. `SKILL.md` pins its sha256 and
  a release-tag URL, so after changing the page, update both, bump `template_version`
  and give migration steps in `SKILL.md`.
- Every change to the page or to the data layout bumps `template_version` and adds a
  step under "Updating a desk" in `SKILL.md`. Updates always back up first.
- The backup format (`kind: "personal-desk-export"`, `format: 1`) is a contract:
  old backups must stay restorable. Change it only by adding a new `format` and keeping
  the reader for the old one.
- Settings live in each desk's database (`meta/config`), not in the page, so one
  template serves every desk.

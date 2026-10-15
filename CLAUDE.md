# CLAUDE.md

General-purpose Claude Code plugin marketplace `digitalemagine` (repo
`digitalemagine/claude-plugins`, public). One plugin so far:
`html-slides`.

- Read `NOTES.md` first: design decisions, tests, status, open items. Update it whenever
  a decision, version or status changes. Keep it to current status, instructions and
  rationale: no change history.
- `README.md` is for users (install, plugin list, maintenance rules).
- Nothing organisation-specific here: no company names, brand themes, project names or
  machine paths, in any file (this repo is public). Those go in a private marketplace
  that depends on this one.
- Development loop: installs come from the remote, so local edits are not live. Test
  them with `claude --plugin-dir <plugin folder>` (repeatable; overrides the installed
  copy for that session). Then bump the plugin's `version`,
  run `claude plugin validate .`, run the checks in `tests/`, commit, push, tag with
  `claude plugin tag --push plugins/<plugin>`, and
  `claude plugin marketplace update digitalemagine` to pick it up.
- Commit or push only when the maintainer asks. Commit email: see the parent folder's
  CLAUDE.md (never a company address).

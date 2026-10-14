# CLAUDE.md

General-purpose Claude Code plugin marketplace `digitalemagine` (repo
`digitalemagine/claude-plugins`, public). One plugin so far:
`html-slides`.

- Read `NOTES.md` first: design decisions, tests, status, open items. Update it whenever
  a decision, version or status changes.
- `README.md` is for users (install, plugin list, maintenance rules).
- Nothing organisation-specific here: no company names, brand themes, project names or
  machine paths, in any file (this repo is public). Those go in a private marketplace
  that depends on this one.
- Bump the plugin's `version`, run `claude plugin validate .`, then
  `claude plugin marketplace update digitalemagine` to test locally.
- Commit or push only when the maintainer asks. Commit email: see the parent folder's
  CLAUDE.md (never a company address).

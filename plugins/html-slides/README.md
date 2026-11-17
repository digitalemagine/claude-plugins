# html-slides

Local HTML slide decks. Claude chooses the engine (responsive, fixed canvas or
reveal.js) and a token-based theme (built-in `light`, plus any installed theme pack),
and asks when either is ambiguous. Every deck gets an edit mode: open it with `?edit`,
edit text in the browser, press "Copy changes", and paste the change set into Claude
Code, which applies the edits to the source file.

```
/plugin install html-slides@digitalemagine
```

Then ask for a deck ("make a 6-slide HTML deck on ..."), or paste a "slide-edit change
set" to apply it.

## Extending

Add your own themes with a **theme pack**: a plugin of yours (it can live in a private
marketplace) holding a skill whose description starts with "Theme pack for
html-slides". When creating a deck, `html-slides` invokes every such skill it finds.

The pack's SKILL.md lists each theme:

- its file, `${CLAUDE_SKILL_DIR}/themes/<name>.css`, defining the full token set
  (copy `skills/html-slide-edit/themes/light.css` and change the values);
- a "use when" line (for example "customer-facing and formal material");
- optionally, which material it is the default for.

Pack themes are treated like `light`: the user and the project's CLAUDE.md still win, and
Claude asks when the choice is unclear. Without a pack, `light` is the only theme.

## Maintaining

- `skills/html-slide-edit/slide-edit.js` is inlined into every deck that uses it. After
  changing it, existing decks keep their old copy until upgraded (the skill says how:
  grep for `slide-edit v`). Never put a closing script tag in that file.
- Add a theme here only if it is generic; brand themes belong in a pack.
- Checks before tagging: `tests/README.md` at the repo root.

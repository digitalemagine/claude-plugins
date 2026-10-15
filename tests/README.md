# Tests

No automated suite. Two manual checks, run before tagging a release.

## 1. Edit mode in a browser

```
python3 tests/build-test-decks.py              # or --theme <file> for a pack theme
open "tests/out/t-responsive-light.html?edit"  # then fixed-canvas and reveal
```

Check on each engine (Chrome; reveal needs network for the CDN):
- Without `?edit`: no toolbar, page behaves normally.
- With `?edit`, after "Edit": arrow keys, space, clicks and swipes inside a slide do not
  navigate (reveal: Esc does not open the overview). Esc leaves edit mode; navigation resumes.
- Change some text, "Copy changes" (and Cmd/Ctrl+S): the clipboard holds a change set
  with BEFORE/AFTER for each changed element only.
- "Download" (not on reveal): the file has no toolbar, no `contenteditable`, no
  `data-slide-edit`, and no runtime state (active slide, counters).
- Toolbar: drag by the grip, reload (position kept), double-click the grip (reset),
  resize the window (stays on screen).
- Leaving with uncopied changes asks for confirmation.

## 2. Engine and theme choice (needs Claude Code)

From an empty folder, with the local plugins loaded instead of the installed ones:

```
claude -p "Make a new HTML deck <request>. Do not create any file. Reply only with: \
the skills you invoked, the engine, the theme and the full path of its CSS file, or the \
question you would ask the user (as text, do not call AskUserQuestion)." \
  --plugin-dir <this repo>/plugins/html-slides [--plugin-dir <theme pack plugin>] \
  --allowedTools "Skill Read Glob" --max-turns 8
```

Expected without a theme pack: `light` always; the engine follows the request (text-led
summary → responsive; roadmap/timeline → fixed canvas; live presenting with notes →
reveal), and conflicting signals produce a question. With a pack: see the pack's own tests.
